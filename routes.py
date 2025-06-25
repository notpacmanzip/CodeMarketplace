import os
import uuid
from flask import render_template, request, redirect, url_for, flash, session, jsonify, abort
from flask_login import current_user
from sqlalchemy import or_, and_, desc, asc
from app import app, db
from models import (User, Category, Product, ProductScreenshot, Review,
                    Message, Purchase, Team, TeamMember, Project,
                    ProjectContributor, Milestone, Repository, RepositoryFile,
                    Commit, CollaborationSession, SessionParticipant,
                    SessionChatMessage, Payment, Notification)
from forms import (ProfileForm, ProductForm, ReviewForm, MessageForm,
                   SearchForm, TeamForm, ProjectForm, RepositoryForm, FileForm,
                   MilestoneForm, CollaborationSessionForm, JoinTeamForm,
                   PaymentForm)
from replit_auth import require_login, require_seller, require_admin, make_replit_blueprint
from utils import save_uploaded_file, generate_conversation_id, format_price, get_language_choices, paginate_query


@app.route("/auth/replit_auth/authorized")
def replit_auth_authorized():
    if not current_user.is_authenticated:
        # Si pour une raison le signal oauth_authorized n’a pas déclenché la connexion
        return redirect(url_for("replit_auth.login"))

    # Rediriger vers la page d'accueil ou dashboard après connexion réussie
    return redirect(url_for("home"))


# Register auth blueprint
app.register_blueprint(make_replit_blueprint(), url_prefix="/auth")


# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True


@app.context_processor
def inject_globals():
    """Inject global variables into templates"""
    return {'current_user': current_user, 'format_price': format_price}


@app.route('/')
def index():
    """Landing page for non-authenticated users, home page for authenticated users"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    # Get featured products for landing page
    featured_products = Product.query.filter_by(
        is_featured=True, is_active=True, status='approved').limit(6).all()
    categories = Category.query.all()

    return render_template('welcome.html',
                           featured_products=featured_products,
                           categories=categories)


@app.route('/home')
@require_login
def home():
    """Legacy home page - redirect to collaborative dashboard"""
    return redirect(url_for('collaborative_dashboard'))


@app.route('/profile')
@require_login
def profile():
    """View user profile"""
    return render_template('profile.html', user=current_user)


@app.route('/profile/edit', methods=['GET', 'POST'])
@require_login
def edit_profile():
    """Edit user profile"""
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.company = form.company.data
        current_user.bio = form.bio.data
        current_user.location = form.location.data
        current_user.website = form.website.data
        current_user.github_url = form.github_url.data
        current_user.user_type = form.user_type.data

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html',
                           user=current_user,
                           form=form,
                           editing=True)


@app.route('/products')
def product_list():
    """List all products with search and filtering"""
    form = SearchForm()
    page = request.args.get('page', 1, type=int)

    # Get filter parameters
    query = request.args.get('query', '')
    category_id = request.args.get('category', type=int)
    language = request.args.get('language', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    sort_by = request.args.get('sort_by', 'newest')

    # Build query
    products_query = Product.query.filter_by(is_active=True, status='approved')

    # Apply filters
    if query:
        products_query = products_query.filter(
            or_(Product.title.ilike(f'%{query}%'),
                Product.description.ilike(f'%{query}%'),
                Product.short_description.ilike(f'%{query}%')))

    if category_id:
        products_query = products_query.filter_by(category_id=category_id)

    if language:
        products_query = products_query.filter(
            Product.programming_languages.ilike(f'%{language}%'))

    if min_price is not None:
        products_query = products_query.filter(Product.price >= min_price)

    if max_price is not None:
        products_query = products_query.filter(Product.price <= max_price)

    # Apply sorting
    if sort_by == 'newest':
        products_query = products_query.order_by(desc(Product.created_at))
    elif sort_by == 'oldest':
        products_query = products_query.order_by(asc(Product.created_at))
    elif sort_by == 'price_low':
        products_query = products_query.order_by(asc(Product.price))
    elif sort_by == 'price_high':
        products_query = products_query.order_by(desc(Product.price))
    elif sort_by == 'popular':
        products_query = products_query.order_by(desc(Product.view_count))

    # Paginate
    products = paginate_query(products_query, page)

    # Get choices for form
    categories = Category.query.all()
    form.category.choices = [('', 'All Categories')] + [(c.id, c.name)
                                                        for c in categories]
    form.language.choices = get_language_choices()

    return render_template('products/list.html',
                           products=products,
                           form=form,
                           categories=categories,
                           current_filters={
                               'query': query,
                               'category': category_id,
                               'language': language,
                               'min_price': min_price,
                               'max_price': max_price,
                               'sort_by': sort_by
                           })


@app.route('/products/<int:product_id>')
def product_detail(product_id):
    """View product details"""
    product = Product.query.get_or_404(product_id)

    if not product.is_active or product.status != 'approved':
        abort(404)

    # Increment view count
    product.view_count += 1
    db.session.commit()

    # Get reviews
    reviews = Review.query.filter_by(product_id=product_id).order_by(
        desc(Review.created_at)).all()

    # Check if user has purchased this product
    has_purchased = False
    if current_user.is_authenticated:
        has_purchased = Purchase.query.filter_by(
            buyer_id=current_user.id,
            product_id=product_id).first() is not None

    # Check if user has already reviewed
    has_reviewed = False
    if current_user.is_authenticated and has_purchased:
        has_reviewed = Review.query.filter_by(
            product_id=product_id,
            reviewer_id=current_user.id).first() is not None

    return render_template('products/detail.html',
                           product=product,
                           reviews=reviews,
                           has_purchased=has_purchased,
                           has_reviewed=has_reviewed)


@app.route('/products/create', methods=['GET', 'POST'])
@require_seller
def create_product():
    """Create a new product"""
    form = ProductForm()

    # Get categories for form
    categories = Category.query.all()
    form.category_id.choices = [(c.id, c.name) for c in categories]

    if form.validate_on_submit():
        product = Product(
            title=form.title.data,
            short_description=form.short_description.data,
            description=form.description.data,
            price=form.price.data,
            category_id=form.category_id.data,
            programming_languages=form.programming_languages.data,
            framework=form.framework.data,
            license_type=form.license_type.data,
            version=form.version.data,
            demo_url=form.demo_url.data,
            github_url=form.github_url.data,
            documentation_url=form.documentation_url.data,
            seller_id=current_user.id)

        # Handle thumbnail upload
        if form.thumbnail.data:
            thumbnail_path = save_uploaded_file(form.thumbnail.data)
            if thumbnail_path:
                product.thumbnail_url = thumbnail_path

        db.session.add(product)
        db.session.commit()

        flash(
            'Product created successfully! It will be reviewed before going live.',
            'success')
        return redirect(url_for('seller_dashboard'))

    return render_template('products/create.html', form=form)


@app.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@require_seller
def edit_product(product_id):
    """Edit a product"""
    product = Product.query.get_or_404(product_id)

    # Check if user owns this product
    if product.seller_id != current_user.id and current_user.user_type != 'admin':
        abort(403)

    form = ProductForm(obj=product)

    # Get categories for form
    categories = Category.query.all()
    form.category_id.choices = [(c.id, c.name) for c in categories]

    if form.validate_on_submit():
        product.title = form.title.data
        product.short_description = form.short_description.data
        product.description = form.description.data
        product.price = form.price.data
        product.category_id = form.category_id.data
        product.programming_languages = form.programming_languages.data
        product.framework = form.framework.data
        product.license_type = form.license_type.data
        product.version = form.version.data
        product.demo_url = form.demo_url.data
        product.github_url = form.github_url.data
        product.documentation_url = form.documentation_url.data

        # Handle thumbnail upload
        if form.thumbnail.data:
            thumbnail_path = save_uploaded_file(form.thumbnail.data)
            if thumbnail_path:
                product.thumbnail_url = thumbnail_path

        # Reset status to pending if significant changes made
        product.status = 'pending'

        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('seller_dashboard'))

    return render_template('products/edit.html', form=form, product=product)


@app.route('/products/<int:product_id>/review', methods=['POST'])
@require_login
def add_review(product_id):
    """Add a review for a product"""
    product = Product.query.get_or_404(product_id)

    # Check if user has purchased this product
    purchase = Purchase.query.filter_by(buyer_id=current_user.id,
                                        product_id=product_id).first()
    if not purchase:
        flash('You can only review products you have purchased.', 'error')
        return redirect(url_for('product_detail', product_id=product_id))

    # Check if user has already reviewed
    existing_review = Review.query.filter_by(
        product_id=product_id, reviewer_id=current_user.id).first()
    if existing_review:
        flash('You have already reviewed this product.', 'error')
        return redirect(url_for('product_detail', product_id=product_id))

    form = ReviewForm()
    if form.validate_on_submit():
        review = Review(product_id=product_id,
                        reviewer_id=current_user.id,
                        seller_id=product.seller_id,
                        rating=form.rating.data,
                        title=form.title.data,
                        comment=form.comment.data,
                        is_verified_purchase=True)

        db.session.add(review)
        db.session.commit()

        flash('Review added successfully!', 'success')

    return redirect(url_for('product_detail', product_id=product_id))


@app.route('/checkout/<int:product_id>')
@require_login
def checkout(product_id):
    """Checkout page for purchasing a product"""
    product = Product.query.get_or_404(product_id)

    if not product.is_active or product.status != 'approved':
        abort(404)

    # Check if user already owns this product
    existing_purchase = Purchase.query.filter_by(
        buyer_id=current_user.id, product_id=product_id).first()
    if existing_purchase:
        flash('You already own this product!', 'info')
        return redirect(url_for('product_detail', product_id=product_id))

    return render_template('payment/checkout.html', product=product)


@app.route('/purchase/<int:product_id>', methods=['POST'])
@require_login
def purchase_product(product_id):
    """Process product purchase (mock implementation)"""
    product = Product.query.get_or_404(product_id)

    # Check if user already owns this product
    existing_purchase = Purchase.query.filter_by(
        buyer_id=current_user.id, product_id=product_id).first()
    if existing_purchase:
        flash('You already own this product!', 'info')
        return redirect(url_for('product_detail', product_id=product_id))

    # Create purchase record
    purchase = Purchase(buyer_id=current_user.id,
                        product_id=product_id,
                        amount_paid=product.price,
                        payment_method='mock_payment',
                        transaction_id=f"mock_{uuid.uuid4().hex[:12]}",
                        payment_status='completed')

    # Update product download count
    product.download_count += 1

    db.session.add(purchase)
    db.session.commit()

    flash('Purchase completed successfully!', 'success')
    return redirect(url_for('payment_success', purchase_id=purchase.id))


@app.route('/payment/success/<int:purchase_id>')
@require_login
def payment_success(purchase_id):
    """Payment success page"""
    purchase = Purchase.query.get_or_404(purchase_id)

    if purchase.buyer_id != current_user.id:
        abort(403)

    return render_template('payment/success.html', purchase=purchase)


@app.route('/payment/cancel')
def payment_cancel():
    """Payment cancelled page"""
    return render_template('payment/cancel.html')


@app.route('/dashboard/seller')
@require_seller
def seller_dashboard():
    """Seller dashboard"""
    # Get seller's products
    products = Product.query.filter_by(seller_id=current_user.id).order_by(
        desc(Product.created_at)).all()

    # Get sales statistics
    sales = Purchase.query.join(Product).filter(
        Product.seller_id == current_user.id).all()
    total_earnings = sum([sale.amount_paid for sale in sales])
    total_sales = len(sales)

    # Get recent reviews
    recent_reviews = Review.query.filter_by(
        seller_id=current_user.id).order_by(desc(
            Review.created_at)).limit(5).all()

    return render_template('dashboard/seller.html',
                           products=products,
                           total_earnings=total_earnings,
                           total_sales=total_sales,
                           recent_reviews=recent_reviews)


@app.route('/dashboard/admin')
@require_admin
def admin_dashboard():
    """Admin dashboard"""
    # Get pending products
    pending_products = Product.query.filter_by(status='pending').order_by(
        desc(Product.created_at)).all()

    # Get statistics
    total_users = User.query.count()
    total_products = Product.query.count()
    total_sales = Purchase.query.count()

    return render_template('dashboard/admin.html',
                           pending_products=pending_products,
                           total_users=total_users,
                           total_products=total_products,
                           total_sales=total_sales)


@app.route('/admin/product/<int:product_id>/approve', methods=['POST'])
@require_admin
def approve_product(product_id):
    """Approve a product"""
    product = Product.query.get_or_404(product_id)
    product.status = 'approved'
    db.session.commit()

    flash('Product approved successfully!', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/product/<int:product_id>/reject', methods=['POST'])
@require_admin
def reject_product(product_id):
    """Reject a product"""
    product = Product.query.get_or_404(product_id)
    product.status = 'rejected'
    db.session.commit()

    flash('Product rejected successfully!', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/messages')
@require_login
def inbox():
    """User's message inbox"""
    conversations = db.session.query(Message.conversation_id).filter(
        or_(Message.sender_id == current_user.id,
            Message.recipient_id == current_user.id)).distinct().all()

    conversation_data = []
    for conv in conversations:
        conv_id = conv[0]
        last_message = Message.query.filter_by(
            conversation_id=conv_id).order_by(desc(
                Message.created_at)).first()

        # Get the other participant
        if last_message.sender_id == current_user.id:
            other_user = User.query.get(last_message.recipient_id)
        else:
            other_user = User.query.get(last_message.sender_id)

        # Count unread messages
        unread_count = Message.query.filter_by(conversation_id=conv_id,
                                               recipient_id=current_user.id,
                                               is_read=False).count()

        conversation_data.append({
            'conversation_id': conv_id,
            'other_user': other_user,
            'last_message': last_message,
            'unread_count': unread_count
        })

    # Sort by last message time
    conversation_data.sort(key=lambda x: x['last_message'].created_at,
                           reverse=True)

    return render_template('messages/inbox.html',
                           conversations=conversation_data)


@app.route('/messages/<conversation_id>')
@require_login
def conversation(conversation_id):
    """View a conversation"""
    messages = Message.query.filter_by(
        conversation_id=conversation_id).order_by(asc(
            Message.created_at)).all()

    if not messages:
        abort(404)

    # Check if user is part of this conversation
    user_in_conversation = any(
        msg.sender_id == current_user.id or msg.recipient_id == current_user.id
        for msg in messages)

    if not user_in_conversation:
        abort(403)

    # Mark messages as read
    Message.query.filter_by(conversation_id=conversation_id,
                            recipient_id=current_user.id,
                            is_read=False).update({'is_read': True})
    db.session.commit()

    # Get the other participant
    for msg in messages:
        if msg.sender_id != current_user.id:
            other_user = User.query.get(msg.sender_id)
            break
        elif msg.recipient_id != current_user.id:
            other_user = User.query.get(msg.recipient_id)
            break
    else:
        other_user = None

    return render_template('messages/conversation.html',
                           messages=messages,
                           conversation_id=conversation_id,
                           other_user=other_user)


@app.route('/messages/send', methods=['POST'])
@require_login
def send_message():
    """Send a message"""
    form = MessageForm()

    if form.validate_on_submit():
        # Generate conversation ID if not provided
        conversation_id = form.conversation_id.data
        if not conversation_id:
            conversation_id = generate_conversation_id(current_user.id,
                                                       form.recipient_id.data)

        message = Message(sender_id=current_user.id,
                          recipient_id=form.recipient_id.data,
                          subject=form.subject.data,
                          content=form.content.data,
                          conversation_id=conversation_id)

        db.session.add(message)
        db.session.commit()

        flash('Message sent successfully!', 'success')
        return redirect(
            url_for('conversation', conversation_id=conversation_id))

    flash('Failed to send message. Please try again.', 'error')
    return redirect(url_for('inbox'))


@app.route('/contact/<user_id>')
@require_login
def contact_user(user_id):
    """Start a conversation with a user"""
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash('You cannot message yourself!', 'error')
        return redirect(url_for('inbox'))

    conversation_id = generate_conversation_id(current_user.id, user_id)

    # Check if conversation exists
    existing_message = Message.query.filter_by(
        conversation_id=conversation_id).first()
    if existing_message:
        return redirect(
            url_for('conversation', conversation_id=conversation_id))

    # Create new conversation form
    form = MessageForm()
    form.recipient_id.data = user_id
    form.conversation_id.data = conversation_id

    return render_template('messages/conversation.html',
                           form=form,
                           other_user=user,
                           conversation_id=conversation_id,
                           messages=[])


def create_default_data():
    """Create default categories and admin user"""
    if Category.query.count() == 0:
        categories = [
            Category(name='Web Development',
                     description='Web applications, websites, and web tools'),
            Category(name='Mobile Apps',
                     description=
                     'iOS, Android, and cross-platform mobile applications'),
            Category(name='Desktop Software',
                     description='Desktop applications and utilities'),
            Category(name='APIs & Libraries',
                     description='APIs, libraries, and code packages'),
            Category(name='Games',
                     description='Video games and game development tools'),
            Category(name='DevOps & Tools',
                     description='Development tools, CI/CD, and automation'),
            Category(name='Data Science',
                     description=
                     'Data analysis, machine learning, and analytics tools'),
            Category(name='Other',
                     description='Other software products and tools')
        ]

        for category in categories:
            db.session.add(category)

        db.session.commit()


# Collaborative Coding Platform Routes


@app.route('/teams')
def teams_list():
    """List all teams"""
    search = request.args.get('search', '')
    team_type = request.args.get('type', '')

    query = Team.query

    if search:
        query = query.filter(
            Team.name.contains(search) | Team.description.contains(search))

    if team_type == 'public':
        query = query.filter(Team.is_public == True)
    elif team_type == 'private':
        query = query.filter(Team.is_public == False)

    teams = query.order_by(Team.created_at.desc()).all()
    return render_template('teams/list.html', teams=teams)


@app.route('/teams/create', methods=['GET', 'POST'])
@require_login
def create_team():
    """Create a new team"""
    form = TeamForm()

    if form.validate_on_submit():
        team = Team(name=form.name.data,
                    description=form.description.data,
                    avatar_url=form.avatar_url.data,
                    owner_id=current_user.id,
                    is_public=form.is_public.data,
                    max_members=form.max_members.data)

        db.session.add(team)
        db.session.flush()  # Get the team ID

        # Add owner as team member
        member = TeamMember(team_id=team.id,
                            user_id=current_user.id,
                            role='owner')
        db.session.add(member)
        db.session.commit()

        flash('Team created successfully!', 'success')
        return redirect(url_for('team_detail', team_id=team.id))

    return render_template('teams/create.html', form=form)


@app.route('/teams/<int:team_id>')
def team_detail(team_id):
    """View team details"""
    team = Team.query.get_or_404(team_id)
    return render_template('teams/detail.html', team=team)


@app.route('/teams/<int:team_id>/edit', methods=['GET', 'POST'])
@require_login
def edit_team(team_id):
    """Edit team details"""
    team = Team.query.get_or_404(team_id)

    # Check if user is team owner or admin
    user_member = TeamMember.query.filter_by(team_id=team_id,
                                             user_id=current_user.id).first()
    if not user_member or user_member.role not in ['owner', 'admin']:
        flash('You do not have permission to edit this team.', 'error')
        return redirect(url_for('team_detail', team_id=team_id))

    form = TeamForm(obj=team)

    if form.validate_on_submit():
        team.name = form.name.data
        team.description = form.description.data
        team.avatar_url = form.avatar_url.data
        team.is_public = form.is_public.data
        team.max_members = form.max_members.data
        team.updated_at = datetime.now()

        db.session.commit()
        flash('Team updated successfully!', 'success')
        return redirect(url_for('team_detail', team_id=team_id))

    return render_template('teams/edit.html', form=form, team=team)


@app.route('/teams/<int:team_id>/join', methods=['POST'])
@require_login
def join_team(team_id):
    """Join a team"""
    team = Team.query.get_or_404(team_id)

    # Check if already a member
    existing_member = TeamMember.query.filter_by(
        team_id=team_id, user_id=current_user.id).first()
    if existing_member:
        flash('You are already a member of this team.', 'info')
        return redirect(url_for('team_detail', team_id=team_id))

    # Check if team is full
    if len(team.members) >= team.max_members:
        flash('Team is full.', 'error')
        return redirect(url_for('team_detail', team_id=team_id))

    # Check if team is public
    if not team.is_public:
        flash('This team is private.', 'error')
        return redirect(url_for('team_detail', team_id=team_id))

    member = TeamMember(team_id=team_id,
                        user_id=current_user.id,
                        role='member')
    db.session.add(member)
    db.session.commit()

    flash('Successfully joined the team!', 'success')
    return redirect(url_for('team_detail', team_id=team_id))


@app.route('/projects')
def projects_list():
    """List all projects"""
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')

    query = Project.query.filter(Project.is_public == True)

    if search:
        query = query.filter(
            Project.name.contains(search)
            | Project.description.contains(search))

    if status:
        query = query.filter(Project.status == status)

    if priority:
        query = query.filter(Project.priority == priority)

    projects = query.order_by(Project.created_at.desc()).all()
    return render_template('projects/list.html', projects=projects)


@app.route('/projects/create', methods=['GET', 'POST'])
@app.route('/projects/create/<int:team_id>', methods=['GET', 'POST'])
@require_login
def create_project(team_id=None):
    """Create a new project"""
    form = ProjectForm()

    # Populate team choices
    user_teams = Team.query.join(TeamMember).filter(
        TeamMember.user_id == current_user.id).all()
    form.team_id.choices = [(team.id, team.name) for team in user_teams]

    if team_id:
        form.team_id.data = team_id

    if form.validate_on_submit():
        project = Project(name=form.name.data,
                          description=form.description.data,
                          requirements=form.requirements.data,
                          team_id=form.team_id.data,
                          owner_id=current_user.id,
                          priority=form.priority.data,
                          budget=form.budget.data,
                          payment_model=form.payment_model.data,
                          start_date=form.start_date.data,
                          due_date=form.due_date.data,
                          is_public=form.is_public.data,
                          tags=form.tags.data)

        db.session.add(project)
        db.session.flush()

        # Add creator as project contributor
        contributor = ProjectContributor(project_id=project.id,
                                         user_id=current_user.id,
                                         role='lead')
        db.session.add(contributor)
        db.session.commit()

        flash('Project created successfully!', 'success')
        return redirect(url_for('project_detail', project_id=project.id))

    return render_template('projects/create.html', form=form, team_id=team_id)


@app.route('/projects/<int:project_id>')
def project_detail(project_id):
    """View project details"""
    project = Project.query.get_or_404(project_id)
    return render_template('projects/detail.html', project=project)


@app.route('/projects/<int:project_id>/collaborate')
@require_login
def collaborative_editor(project_id):
    """Open collaborative editor for project"""
    project = Project.query.get_or_404(project_id)

    # Check if user has access to this project
    is_contributor = ProjectContributor.query.filter_by(
        project_id=project_id, user_id=current_user.id).first()

    is_team_member = TeamMember.query.filter_by(
        team_id=project.team_id, user_id=current_user.id).first()

    if not (is_contributor or is_team_member or project.is_public):
        flash('You do not have access to this project.', 'error')
        return redirect(url_for('project_detail', project_id=project_id))

    # Get or create active collaboration session
    active_session = CollaborationSession.query.filter_by(
        project_id=project_id, status='active').first()

    return render_template('collaboration/editor.html',
                           project=project,
                           session=active_session)


# Repository creation route moved to collaboration_routes.py


# API Routes for collaborative features
@app.route('/api/files/<int:file_id>')
@require_login
def get_file_content(file_id):
    """Get file content for editor"""
    # Import here to avoid circular imports
    from collaboration_models import CodeFile
    file = CodeFile.query.get_or_404(file_id)
    return jsonify({
        'content': file.content,
        'language': file.language,
        'filename': file.filename
    })


@app.route('/api/files/<int:file_id>', methods=['PUT'])
@require_login
def update_file_content(file_id):
    """Update file content"""
    from collaboration_models import CodeFile
    file = CodeFile.query.get_or_404(file_id)
    data = request.get_json()

    file.content = data.get('content', '')
    file.file_size = len(data.get('content', '').encode('utf-8'))
    file.last_modified_by = current_user.id
    file.version += 1
    file.updated_at = datetime.now()
    db.session.commit()

    return jsonify({'success': True})


@app.route('/api/chat/send', methods=['POST'])
@require_login
def send_chat_message():
    """Send chat message in collaboration session"""
    data = request.get_json()
    session_id = data.get('session_id')
    message = data.get('message')

    if session_id and message:
        chat_message = SessionChatMessage(session_id=session_id,
                                          user_id=current_user.id,
                                          message=message)
        db.session.add(chat_message)
        db.session.commit()

        return jsonify({'success': True})

    return jsonify({'success': False})


# Repository detail route moved to collaboration_routes.py

# File editing routes moved to collaboration_routes.py

# File creation route moved to collaboration_routes.py


@app.route('/api/files/<int:file_id>', methods=['DELETE'])
@require_login
def delete_file_api(file_id):
    """Delete a file"""
    file = RepositoryFile.query.get_or_404(file_id)

    # Check permissions
    project = file.repository.project
    is_contributor = ProjectContributor.query.filter_by(
        project_id=project.id, user_id=current_user.id).first()

    if not is_contributor:
        return jsonify({'success': False, 'message': 'No access'})

    db.session.delete(file)
    db.session.commit()

    return jsonify({'success': True, 'message': 'File deleted'})


# Repository sharing route moved to collaboration_routes.py


# Additional API endpoints for project management
@app.route('/api/projects/<int:project_id>/join', methods=['POST'])
@require_login
def join_project_api(project_id):
    """Join a project as contributor"""
    project = Project.query.get_or_404(project_id)

    # Check if already a contributor
    existing = ProjectContributor.query.filter_by(
        project_id=project_id, user_id=current_user.id).first()

    if existing:
        return jsonify({'success': False, 'message': 'Already a contributor'})

    if not project.is_public:
        return jsonify({'success': False, 'message': 'Project is private'})

    contributor = ProjectContributor(project_id=project_id,
                                     user_id=current_user.id,
                                     role='contributor')
    db.session.add(contributor)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Successfully joined project'})


@app.route('/api/projects/<int:project_id>/milestones', methods=['POST'])
@require_login
def create_milestone_api(project_id):
    """Create a new milestone"""
    project = Project.query.get_or_404(project_id)
    data = request.get_json()

    # Check if user has access
    is_contributor = ProjectContributor.query.filter_by(
        project_id=project_id, user_id=current_user.id).first()

    if not is_contributor:
        return jsonify({'success': False, 'message': 'No access'})

    milestone = Milestone(project_id=project_id,
                          title=data.get('title', ''),
                          description=data.get('description', ''),
                          payment_amount=data.get('payment_amount'))

    db.session.add(milestone)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Milestone created'})


# Update home page to show collaborative features
@app.route('/dashboard')
@require_login
def collaborative_dashboard():
    """Collaborative coding dashboard"""
    # Get user's teams
    user_teams = Team.query.join(TeamMember).filter(
        TeamMember.user_id == current_user.id).all()

    # Get user's projects
    user_projects = Project.query.join(ProjectContributor).filter(
        ProjectContributor.user_id == current_user.id).order_by(
            Project.updated_at.desc()).limit(5).all()

    # Get recent activity (notifications)
    notifications = Notification.query.filter_by(
        user_id=current_user.id, is_read=False).order_by(
            Notification.created_at.desc()).limit(10).all()

    return render_template('dashboard/collaborative.html',
                           teams=user_teams,
                           projects=user_projects,
                           notifications=notifications)


# Import new route modules
import forum_routes
import collaboration_routes

# Initialize default data when the app starts
with app.app_context():
    create_default_data()
    # Forum data initialization handled elsewhere


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
