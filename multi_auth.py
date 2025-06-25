import jwt
import os
import uuid
from functools import wraps
from urllib.parse import urlencode

from flask import g, session, redirect, request, render_template, url_for, flash
from flask_dance.consumer import (
    OAuth2ConsumerBlueprint,
    oauth_authorized,
    oauth_error,
)
from flask_dance.contrib.google import make_google_blueprint
from flask_dance.contrib.github import make_github_blueprint
from flask_dance.consumer.storage import BaseStorage
from flask_login import LoginManager, login_user, logout_user, current_user
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError
from sqlalchemy.exc import NoResultFound
from werkzeug.local import LocalProxy

from app import app, db
from models import OAuth, User

login_manager = LoginManager(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class UserSessionStorage(BaseStorage):

    def get(self, blueprint):
        try:
            token = db.session.query(OAuth).filter_by(
                user_id=current_user.get_id(),
                browser_session_key=g.browser_session_key,
                provider=blueprint.name,
            ).one().token
        except NoResultFound:
            token = None
        return token

    def set(self, blueprint, token):
        db.session.query(OAuth).filter_by(
            user_id=current_user.get_id(),
            browser_session_key=g.browser_session_key,
            provider=blueprint.name,
        ).delete()
        new_model = OAuth()
        new_model.user_id = current_user.get_id()
        new_model.browser_session_key = g.browser_session_key
        new_model.provider = blueprint.name
        new_model.token = token
        db.session.add(new_model)
        db.session.commit()

    def delete(self, blueprint):
        db.session.query(OAuth).filter_by(
            user_id=current_user.get_id(),
            browser_session_key=g.browser_session_key,
            provider=blueprint.name).delete()
        db.session.commit()


def make_replit_blueprint():
    try:
        repl_id = os.environ['REPL_ID']
    except KeyError:
        raise SystemExit("the REPL_ID environment variable must be set")

    issuer_url = os.environ.get('ISSUER_URL', "https://replit.com/oidc")

    replit_bp = OAuth2ConsumerBlueprint(
        "replit_auth",
        __name__,
        client_id=repl_id,
        client_secret=None,
        base_url=issuer_url,
        authorization_url_params={
            "prompt": "login consent",
        },
        token_url=issuer_url + "/token",
        token_url_params={
            "auth": (),
            "include_client_id": True,
        },
        auto_refresh_url=issuer_url + "/token",
        auto_refresh_kwargs={
            "client_id": repl_id,
        },
        authorization_url=issuer_url + "/auth",
        use_pkce=True,
        code_challenge_method="S256",
        scope=["openid", "profile", "email", "offline_access"],
        storage=UserSessionStorage(),
    )

    @replit_bp.before_app_request
    def set_applocal_session():
        if '_browser_session_key' not in session:
            session['_browser_session_key'] = uuid.uuid4().hex
        session.modified = True
        g.browser_session_key = session['_browser_session_key']
        g.flask_dance_replit = replit_bp.session

    return replit_bp


def create_oauth_blueprints():
    """Create all OAuth blueprints"""
    blueprints = {}
    
    # Replit Auth
    try:
        blueprints['replit'] = make_replit_blueprint()
    except SystemExit:
        pass  # Replit auth not available
    
    # Google OAuth
    google_client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
    google_client_secret = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
    if google_client_id and google_client_secret:
        blueprints['google'] = make_google_blueprint(
            client_id=google_client_id,
            client_secret=google_client_secret,
            scope=["openid", "email", "profile"],
            storage=UserSessionStorage()
        )
    
    # GitHub OAuth
    github_client_id = os.environ.get('GITHUB_OAUTH_CLIENT_ID')
    github_client_secret = os.environ.get('GITHUB_OAUTH_CLIENT_SECRET')
    if github_client_id and github_client_secret:
        blueprints['github'] = make_github_blueprint(
            client_id=github_client_id,
            client_secret=github_client_secret,
            scope="user:email",
            storage=UserSessionStorage()
        )
    
    return blueprints


def save_user_from_provider(user_data, provider):
    """Save user data from OAuth provider"""
    if provider == 'replit':
        user_claims = jwt.decode(user_data['id_token'], options={"verify_signature": False})
        user_id = user_claims['sub']
        email = user_claims.get('email')
        first_name = user_claims.get('first_name')
        last_name = user_claims.get('last_name')
        profile_image_url = user_claims.get('profile_image_url')
    elif provider == 'google':
        user_id = f"google_{user_data['sub']}"
        email = user_data.get('email')
        first_name = user_data.get('given_name')
        last_name = user_data.get('family_name')
        profile_image_url = user_data.get('picture')
    elif provider == 'github':
        user_id = f"github_{user_data['id']}"
        email = user_data.get('email')
        # GitHub doesn't separate first/last names
        name_parts = (user_data.get('name') or '').split(' ', 1)
        first_name = name_parts[0] if name_parts else None
        last_name = name_parts[1] if len(name_parts) > 1 else None
        profile_image_url = user_data.get('avatar_url')
    else:
        return None

    # Check if user already exists
    user = User.query.get(user_id)
    if not user:
        user = User()
        user.id = user_id
    
    # Update user data
    user.email = email
    user.first_name = first_name
    user.last_name = last_name
    user.profile_image_url = profile_image_url
    
    user = db.session.merge(user)
    db.session.commit()
    return user


@oauth_authorized.connect
def oauth_logged_in(blueprint, token):
    """Handle OAuth login for all providers"""
    if not token:
        flash('Failed to log in.', 'error')
        return redirect(url_for('index'))

    try:
        if blueprint.name == 'replit_auth':
            user = save_user_from_provider(token, 'replit')
        elif blueprint.name == 'google':
            resp = blueprint.session.get("/oauth2/v2/userinfo")
            if not resp.ok:
                flash('Failed to fetch user info from Google.', 'error')
                return redirect(url_for('index'))
            user = save_user_from_provider(resp.json(), 'google')
        elif blueprint.name == 'github':
            resp = blueprint.session.get("/user")
            if not resp.ok:
                flash('Failed to fetch user info from GitHub.', 'error')
                return redirect(url_for('index'))
            user = save_user_from_provider(resp.json(), 'github')
        else:
            flash('Unknown login provider.', 'error')
            return redirect(url_for('index'))

        if user:
            login_user(user)
            blueprint.token = token
            next_url = session.pop("next_url", None)
            flash(f'Successfully logged in!', 'success')
            return redirect(next_url or url_for('home'))
        else:
            flash('Failed to create user account.', 'error')
            return redirect(url_for('index'))
            
    except Exception as e:
        flash('Login failed. Please try again.', 'error')
        return redirect(url_for('index'))


@oauth_error.connect
def oauth_error_handler(blueprint, error, error_description=None, error_uri=None):
    flash('Authentication failed. Please try again.', 'error')
    return redirect(url_for('index'))


def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            session["next_url"] = get_next_navigation_url(request)
            return redirect(url_for('auth_login'))
        return f(*args, **kwargs)
    return decorated_function


def get_next_navigation_url(request):
    is_navigation_url = request.headers.get(
        'Sec-Fetch-Mode') == 'navigate' and request.headers.get(
            'Sec-Fetch-Dest') == 'document'
    if is_navigation_url:
        return request.url
    return request.referrer or request.url


def logout_all_providers():
    """Logout from all OAuth providers"""
    logout_user()
    
    # Clear all OAuth tokens
    if hasattr(g, 'browser_session_key'):
        db.session.query(OAuth).filter_by(
            browser_session_key=g.browser_session_key
        ).delete()
        db.session.commit()
    
    # Clear session
    session.clear()
    flash('Successfully logged out.', 'success')
    return redirect(url_for('index'))