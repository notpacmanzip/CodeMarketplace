from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from sqlalchemy import desc, func
from app import db
from models import User, Product, Purchase, Category
from code_review_models import ReviewerProfile, CodeSubmission, CodeReview, ReviewRating
from replit_auth import require_admin
from datetime import datetime, timedelta
import json

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

ADMIN_PASSWORD = "4116walidnadi"

def check_admin_password():
    """Check if admin password is correct"""
    return session.get('admin_authenticated') == True

def require_admin_auth():
    """Decorator to require admin password authentication"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            if not check_admin_password():
                return redirect(url_for('admin.login'))
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login with password"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin_authenticated'] = True
            flash('Admin access granted!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid admin password. Please try again.', 'error')
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    """Admin logout"""
    session.pop('admin_authenticated', None)
    flash('Admin session ended.', 'info')
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@require_admin_auth()
def dashboard():
    """Admin dashboard with overview statistics"""
    # Product sales statistics
    total_products = Product.query.count()
    total_sales = Purchase.query.count()
    total_revenue = db.session.query(func.sum(Purchase.amount)).scalar() or 0
    pending_products = Product.query.filter_by(is_approved=False).count()
    
    # Code review statistics
    total_submissions = CodeSubmission.query.count()
    pending_reviews = CodeSubmission.query.filter_by(status='pending').count()
    active_reviewers = ReviewerProfile.query.filter_by(is_verified=True, is_available=True).count()
    unverified_reviewers = ReviewerProfile.query.filter_by(is_verified=False).count()
    
    # Recent activity
    recent_purchases = Purchase.query.order_by(desc(Purchase.created_at)).limit(5).all()
    recent_submissions = CodeSubmission.query.order_by(desc(CodeSubmission.created_at)).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_products=total_products,
                         total_sales=total_sales,
                         total_revenue=total_revenue,
                         pending_products=pending_products,
                         total_submissions=total_submissions,
                         pending_reviews=pending_reviews,
                         active_reviewers=active_reviewers,
                         unverified_reviewers=unverified_reviewers,
                         recent_purchases=recent_purchases,
                         recent_submissions=recent_submissions)

@admin_bp.route('/products')
@require_admin_auth()
def manage_products():
    """Manage products and sales"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    category_filter = request.args.get('category', '')
    
    # Build query
    query = Product.query
    
    if status_filter == 'pending':
        query = query.filter_by(is_approved=False)
    elif status_filter == 'approved':
        query = query.filter_by(is_approved=True)
    elif status_filter == 'featured':
        query = query.filter_by(is_featured=True)
    
    if category_filter:
        query = query.filter_by(category_id=category_filter)
    
    products = query.order_by(desc(Product.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get categories for filter
    categories = Category.query.all()
    
    # Sales statistics for each product
    product_stats = {}
    for product in products.items:
        stats = db.session.query(
            func.count(Purchase.id).label('total_sales'),
            func.sum(Purchase.amount).label('total_revenue')
        ).filter_by(product_id=product.id).first()
        
        product_stats[product.id] = {
            'sales': stats.total_sales or 0,
            'revenue': stats.total_revenue or 0
        }
    
    return render_template('admin/manage_products.html',
                         products=products,
                         categories=categories,
                         status_filter=status_filter,
                         category_filter=category_filter,
                         product_stats=product_stats)

@admin_bp.route('/sales')
@login_required
@require_admin
def sales_analytics():
    """Sales analytics and reports"""
    # Date range filter
    days = request.args.get('days', 30, type=int)
    start_date = datetime.now() - timedelta(days=days)
    
    # Sales over time
    sales_data = db.session.query(
        func.date(Purchase.created_at).label('date'),
        func.count(Purchase.id).label('sales'),
        func.sum(Purchase.amount).label('revenue')
    ).filter(Purchase.created_at >= start_date).group_by(
        func.date(Purchase.created_at)
    ).order_by('date').all()
    
    # Top selling products
    top_products = db.session.query(
        Product.title,
        Product.price,
        func.count(Purchase.id).label('sales'),
        func.sum(Purchase.amount).label('revenue')
    ).join(Purchase).filter(
        Purchase.created_at >= start_date
    ).group_by(Product.id).order_by(desc('sales')).limit(10).all()
    
    # Top sellers
    top_sellers = db.session.query(
        User.username,
        User.full_name,
        func.count(Purchase.id).label('sales'),
        func.sum(Purchase.amount).label('revenue')
    ).join(Product, User.id == Product.seller_id).join(Purchase).filter(
        Purchase.created_at >= start_date
    ).group_by(User.id).order_by(desc('revenue')).limit(10).all()
    
    # Category performance
    category_stats = db.session.query(
        Category.name,
        func.count(Purchase.id).label('sales'),
        func.sum(Purchase.amount).label('revenue')
    ).join(Product).join(Purchase).filter(
        Purchase.created_at >= start_date
    ).group_by(Category.id).order_by(desc('revenue')).all()
    
    return render_template('admin/sales_analytics.html',
                         sales_data=sales_data,
                         top_products=top_products,
                         top_sellers=top_sellers,
                         category_stats=category_stats,
                         days=days)

@admin_bp.route('/reviewers')
@require_admin_auth()
def manage_reviewers():
    """Manage code reviewers and their portfolios"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    # Build query
    query = ReviewerProfile.query.join(User)
    
    if status_filter == 'verified':
        query = query.filter(ReviewerProfile.is_verified == True)
    elif status_filter == 'pending':
        query = query.filter(ReviewerProfile.is_verified == False)
    elif status_filter == 'available':
        query = query.filter(ReviewerProfile.is_available == True)
    
    reviewers = query.order_by(desc(ReviewerProfile.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get statistics for each reviewer
    reviewer_stats = {}
    for reviewer in reviewers.items:
        # Count reviews and calculate ratings
        total_reviews = CodeSubmission.query.filter_by(
            reviewer_id=reviewer.user_id,
            status='completed'
        ).count()
        
        avg_rating = db.session.query(func.avg(ReviewRating.overall_rating)).filter_by(
            reviewer_id=reviewer.user_id
        ).scalar() or 0
        
        recent_reviews = CodeSubmission.query.filter_by(
            reviewer_id=reviewer.user_id
        ).filter(CodeSubmission.created_at >= datetime.now() - timedelta(days=30)).count()
        
        reviewer_stats[reviewer.user_id] = {
            'total_reviews': total_reviews,
            'avg_rating': round(avg_rating, 1),
            'recent_reviews': recent_reviews
        }
    
    return render_template('admin/manage_reviewers.html',
                         reviewers=reviewers,
                         status_filter=status_filter,
                         reviewer_stats=reviewer_stats)

@admin_bp.route('/reviewer/<user_id>')
@require_admin_auth()
def reviewer_detail(user_id):
    """View detailed reviewer portfolio"""
    reviewer = ReviewerProfile.query.filter_by(user_id=user_id).first_or_404()
    
    # Get reviewer statistics
    total_reviews = CodeSubmission.query.filter_by(
        reviewer_id=user_id,
        status='completed'
    ).count()
    
    pending_reviews = CodeSubmission.query.filter_by(
        reviewer_id=user_id,
        status='in_review'
    ).count()
    
    # Recent reviews with ratings
    recent_reviews = db.session.query(
        CodeSubmission, ReviewRating
    ).outerjoin(ReviewRating).filter(
        CodeSubmission.reviewer_id == user_id,
        CodeSubmission.status == 'completed'
    ).order_by(desc(CodeSubmission.completed_at)).limit(10).all()
    
    # Rating distribution
    rating_distribution = db.session.query(
        ReviewRating.overall_rating,
        func.count(ReviewRating.id).label('count')
    ).filter_by(reviewer_id=user_id).group_by(
        ReviewRating.overall_rating
    ).all()
    
    # Specializations and languages (parse JSON)
    specializations = json.loads(reviewer.specializations or '[]')
    languages = json.loads(reviewer.programming_languages or '[]')
    frameworks = json.loads(reviewer.frameworks or '[]')
    
    return render_template('admin/reviewer_detail.html',
                         reviewer=reviewer,
                         total_reviews=total_reviews,
                         pending_reviews=pending_reviews,
                         recent_reviews=recent_reviews,
                         rating_distribution=rating_distribution,
                         specializations=specializations,
                         languages=languages,
                         frameworks=frameworks)

@admin_bp.route('/verify-reviewer/<user_id>', methods=['POST'])
@login_required
@require_admin
def verify_reviewer(user_id):
    """Verify a reviewer profile"""
    reviewer = ReviewerProfile.query.filter_by(user_id=user_id).first_or_404()
    
    action = request.form.get('action')
    
    if action == 'verify':
        reviewer.is_verified = True
        reviewer.verification_date = datetime.now()
        reviewer.verification_method = 'admin_manual'
        flash(f'Reviewer {reviewer.user.username} has been verified.', 'success')
    elif action == 'reject':
        reviewer.is_verified = False
        reviewer.verification_date = None
        flash(f'Reviewer {reviewer.user.username} verification has been rejected.', 'warning')
    
    db.session.commit()
    return redirect(url_for('admin.reviewer_detail', user_id=user_id))

@admin_bp.route('/approve-product/<int:product_id>', methods=['POST'])
@login_required
@require_admin
def approve_product(product_id):
    """Approve or reject a product"""
    product = Product.query.get_or_404(product_id)
    
    action = request.form.get('action')
    
    if action == 'approve':
        product.is_approved = True
        flash(f'Product "{product.title}" has been approved.', 'success')
    elif action == 'reject':
        product.is_approved = False
        flash(f'Product "{product.title}" has been rejected.', 'warning')
    elif action == 'feature':
        product.is_featured = not product.is_featured
        status = 'featured' if product.is_featured else 'unfeatured'
        flash(f'Product "{product.title}" has been {status}.', 'info')
    
    db.session.commit()
    return redirect(url_for('admin.manage_products'))

@admin_bp.route('/code-reviews')
@login_required
@require_admin
def manage_code_reviews():
    """Manage code review submissions"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    query = CodeSubmission.query
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    submissions = query.order_by(desc(CodeSubmission.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/manage_code_reviews.html',
                         submissions=submissions,
                         status_filter=status_filter)

@admin_bp.route('/users')
@login_required
@require_admin
def manage_users():
    """Manage platform users"""
    page = request.args.get('page', 1, type=int)
    role_filter = request.args.get('role', 'all')
    
    query = User.query
    
    if role_filter == 'sellers':
        query = query.filter(User.products.any())
    elif role_filter == 'reviewers':
        query = query.join(ReviewerProfile, isouter=True).filter(ReviewerProfile.user_id.isnot(None))
    elif role_filter == 'admins':
        query = query.filter_by(is_admin=True)
    
    users = query.order_by(desc(User.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/manage_users.html',
                         users=users,
                         role_filter=role_filter)

@admin_bp.route('/analytics-api/sales-chart')
@login_required
@require_admin
def sales_chart_data():
    """API endpoint for sales chart data"""
    days = request.args.get('days', 30, type=int)
    start_date = datetime.now() - timedelta(days=days)
    
    sales_data = db.session.query(
        func.date(Purchase.created_at).label('date'),
        func.count(Purchase.id).label('sales'),
        func.sum(Purchase.amount).label('revenue')
    ).filter(Purchase.created_at >= start_date).group_by(
        func.date(Purchase.created_at)
    ).order_by('date').all()
    
    return jsonify({
        'dates': [str(row.date) for row in sales_data],
        'sales': [row.sales for row in sales_data],
        'revenue': [float(row.revenue or 0) for row in sales_data]
    })

@admin_bp.route('/toggle-user-admin/<user_id>', methods=['POST'])
@login_required
@require_admin
def toggle_user_admin(user_id):
    """Toggle user admin status"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot modify your own admin status.', 'error')
    else:
        user.is_admin = not user.is_admin
        status = 'granted' if user.is_admin else 'revoked'
        flash(f'Admin access {status} for {user.username}.', 'success')
        db.session.commit()
    
    return redirect(url_for('admin.manage_users'))