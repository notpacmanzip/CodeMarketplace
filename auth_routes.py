from flask import render_template, redirect, url_for, flash, session
from flask_login import current_user, logout_user
from app import app
from multi_auth import create_oauth_blueprints, logout_all_providers, require_login

# Create and register OAuth blueprints
oauth_blueprints = create_oauth_blueprints()

# Register blueprints with the app
for name, blueprint in oauth_blueprints.items():
    if name == 'replit':
        app.register_blueprint(blueprint, url_prefix="/auth")
    else:
        app.register_blueprint(blueprint, url_prefix=f"/auth/{name}")


@app.route('/login')
def auth_login():
    """Show login page with multiple provider options"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    available_providers = list(oauth_blueprints.keys())
    return render_template('auth/login.html', providers=available_providers)


@app.route('/auth/login/<provider>')
def login_with_provider(provider):
    """Initiate login with specific OAuth provider"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if provider not in oauth_blueprints:
        flash('Login provider not available.', 'error')
        return redirect(url_for('auth_login'))
    
    blueprint = oauth_blueprints[provider]
    
    # Store the next URL in session
    next_url = session.get('next_url', url_for('dashboard'))
    session['next_url'] = next_url
    
    if provider == 'replit':
        return redirect(url_for('replit_auth.login'))
    else:
        return redirect(url_for(f'{provider}.login'))


@app.route('/logout')
def auth_logout():
    """Logout from all providers"""
    return logout_all_providers()


@app.route('/auth/profile')
@require_login
def auth_profile():
    """User profile page"""
    return render_template('auth/profile.html')