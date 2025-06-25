from datetime import datetime
from app import db
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint

# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)
    
    # Additional marketplace fields
    user_type = db.Column(db.String, default='buyer')  # 'buyer', 'seller', 'admin'
    company = db.Column(db.String, nullable=True)
    bio = db.Column(db.Text, nullable=True)
    location = db.Column(db.String, nullable=True)
    website = db.Column(db.String, nullable=True)
    github_url = db.Column(db.String, nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    products = db.relationship('Product', backref='seller', lazy=True)
    reviews_given = db.relationship('Review', foreign_keys='Review.reviewer_id', backref='reviewer', lazy=True)
    reviews_received = db.relationship('Review', foreign_keys='Review.seller_id', backref='seller_user', lazy=True)
    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy=True)
    messages_received = db.relationship('Message', foreign_keys='Message.recipient_id', backref='recipient', lazy=True)
    purchases = db.relationship('Purchase', backref='buyer', lazy=True)

    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or "Anonymous"

    @property
    def average_rating(self):
        if not self.reviews_received:
            return 0
        return sum([review.rating for review in self.reviews_received]) / len(self.reviews_received)

# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.String, db.ForeignKey(User.id))
    browser_session_key = db.Column(db.String, nullable=False)
    user = db.relationship(User)

    __table_args__ = (UniqueConstraint(
        'user_id',
        'browser_session_key',
        'provider',
        name='uq_user_browser_session_key_provider',
    ),)

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    short_description = db.Column(db.String(500))
    price = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD')
    
    # Technical details
    programming_languages = db.Column(db.String(500))  # Comma-separated
    framework = db.Column(db.String(100))
    license_type = db.Column(db.String(50))  # MIT, GPL, Commercial, etc.
    version = db.Column(db.String(20))
    
    # Media
    thumbnail_url = db.Column(db.String(500))
    demo_url = db.Column(db.String(500))
    github_url = db.Column(db.String(500))
    documentation_url = db.Column(db.String(500))
    
    # Status
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Metrics
    view_count = db.Column(db.Integer, default=0)
    download_count = db.Column(db.Integer, default=0)
    
    # Foreign keys
    seller_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    screenshots = db.relationship('ProductScreenshot', backref='product', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='product', lazy=True)
    purchases = db.relationship('Purchase', backref='product', lazy=True)

    @property
    def average_rating(self):
        if not self.reviews:
            return 0
        return sum([review.rating for review in self.reviews]) / len(self.reviews)

    @property
    def review_count(self):
        return len(self.reviews)

    @property
    def languages_list(self):
        if self.programming_languages:
            return [lang.strip() for lang in self.programming_languages.split(',')]
        return []

class ProductScreenshot(db.Model):
    __tablename__ = 'product_screenshots'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    caption = db.Column(db.String(200))
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)

class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    reviewer_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    seller_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    title = db.Column(db.String(200))
    comment = db.Column(db.Text)
    
    is_verified_purchase = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    subject = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    
    is_read = db.Column(db.Boolean, default=False)
    conversation_id = db.Column(db.String, nullable=False)  # Groups related messages
    
    created_at = db.Column(db.DateTime, default=datetime.now)

class Purchase(db.Model):
    __tablename__ = 'purchases'
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    amount_paid = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD')
    
    # Payment details (for mock implementation)
    payment_method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(100))
    payment_status = db.Column(db.String(20), default='completed')  # pending, completed, failed, refunded
    
    created_at = db.Column(db.DateTime, default=datetime.now)
