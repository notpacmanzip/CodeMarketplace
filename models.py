from datetime import datetime
from app import db
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint
import json

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


# Collaborative Coding Platform Models

class Team(db.Model):
    __tablename__ = 'teams'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    avatar_url = db.Column(db.String(500))
    
    owner_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    is_public = db.Column(db.Boolean, default=True)
    max_members = db.Column(db.Integer, default=10)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    owner = db.relationship('User', backref='owned_teams')
    members = db.relationship('TeamMember', backref='team', cascade='all, delete-orphan')
    projects = db.relationship('Project', backref='team', cascade='all, delete-orphan')


class TeamMember(db.Model):
    __tablename__ = 'team_members'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    role = db.Column(db.String(50), default='member')  # owner, admin, member, contributor
    joined_at = db.Column(db.DateTime, default=datetime.now)
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('team_id', 'user_id', name='unique_team_member'),)
    
    user = db.relationship('User', backref='team_memberships')


class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    requirements = db.Column(db.Text)  # Project goals and requirements
    
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    owner_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    status = db.Column(db.String(50), default='planning')  # planning, active, completed, paused, cancelled
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    
    budget = db.Column(db.Numeric(10, 2))
    currency = db.Column(db.String(3), default='USD')
    payment_model = db.Column(db.String(50), default='milestone')  # milestone, hourly, fixed, equity
    
    start_date = db.Column(db.DateTime)
    due_date = db.Column(db.DateTime)
    completed_date = db.Column(db.DateTime)
    
    is_public = db.Column(db.Boolean, default=False)
    tags = db.Column(db.String(500))  # Comma-separated
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    owner = db.relationship('User', backref='owned_projects')
    contributors = db.relationship('ProjectContributor', backref='project', cascade='all, delete-orphan')
    milestones = db.relationship('Milestone', backref='project', cascade='all, delete-orphan')
    repositories = db.relationship('Repository', backref='project', cascade='all, delete-orphan')
    collaborations = db.relationship('CollaborationSession', backref='project', cascade='all, delete-orphan')


class ProjectContributor(db.Model):
    __tablename__ = 'project_contributors'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    role = db.Column(db.String(50), default='contributor')  # lead, developer, designer, tester, reviewer
    contribution_percentage = db.Column(db.Numeric(5, 2), default=0)  # For payment distribution
    hours_logged = db.Column(db.Numeric(8, 2), default=0)
    
    joined_at = db.Column(db.DateTime, default=datetime.now)
    
    __table_args__ = (db.UniqueConstraint('project_id', 'user_id', name='unique_project_contributor'),)
    
    user = db.relationship('User', backref='project_contributions')


class Milestone(db.Model):
    __tablename__ = 'milestones'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    requirements = db.Column(db.Text)
    
    status = db.Column(db.String(50), default='pending')  # pending, in_progress, completed, cancelled
    payment_amount = db.Column(db.Numeric(10, 2))
    
    due_date = db.Column(db.DateTime)
    completed_date = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class Repository(db.Model):
    __tablename__ = 'repositories'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    visibility = db.Column(db.String(20), default='private')  # public, private, team
    language = db.Column(db.String(50))
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    files = db.relationship('RepositoryFile', backref='repository', cascade='all, delete-orphan')
    commits = db.relationship('Commit', backref='repository', cascade='all, delete-orphan')


class RepositoryFile(db.Model):
    __tablename__ = 'repository_files'
    id = db.Column(db.Integer, primary_key=True)
    repository_id = db.Column(db.Integer, db.ForeignKey('repositories.id'), nullable=False)
    
    filename = db.Column(db.String(500), nullable=False)
    filepath = db.Column(db.String(1000), nullable=False)
    content = db.Column(db.Text)
    language = db.Column(db.String(50))
    
    size = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class Commit(db.Model):
    __tablename__ = 'commits'
    id = db.Column(db.Integer, primary_key=True)
    repository_id = db.Column(db.Integer, db.ForeignKey('repositories.id'), nullable=False)
    author_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    hash = db.Column(db.String(40), unique=True, nullable=False)
    message = db.Column(db.Text, nullable=False)
    changes_summary = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    author = db.relationship('User', backref='commits')


class CollaborationSession(db.Model):
    __tablename__ = 'collaboration_sessions'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    host_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    session_type = db.Column(db.String(50), default='coding')  # coding, review, planning, discussion
    status = db.Column(db.String(20), default='scheduled')  # scheduled, active, completed, cancelled
    
    max_participants = db.Column(db.Integer, default=5)
    
    scheduled_at = db.Column(db.DateTime)
    started_at = db.Column(db.DateTime)
    ended_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    host = db.relationship('User', backref='hosted_sessions')
    participants = db.relationship('SessionParticipant', backref='session', cascade='all, delete-orphan')
    chat_messages = db.relationship('SessionChatMessage', backref='session', cascade='all, delete-orphan')


class SessionParticipant(db.Model):
    __tablename__ = 'session_participants'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('collaboration_sessions.id'), nullable=False)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    role = db.Column(db.String(50), default='participant')  # host, co-host, participant, observer
    joined_at = db.Column(db.DateTime, default=datetime.now)
    left_at = db.Column(db.DateTime)
    
    __table_args__ = (db.UniqueConstraint('session_id', 'user_id', name='unique_session_participant'),)
    
    user = db.relationship('User', backref='session_participations')


class SessionChatMessage(db.Model):
    __tablename__ = 'session_chat_messages'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('collaboration_sessions.id'), nullable=False)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    message = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='text')  # text, code, file, system
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    user = db.relationship('User', backref='session_messages')


class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    recipient_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    milestone_id = db.Column(db.Integer, db.ForeignKey('milestones.id'), nullable=True)
    
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD')
    
    payment_type = db.Column(db.String(50), default='milestone')  # milestone, bonus, hourly, final
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed, cancelled
    
    description = db.Column(db.Text)
    transaction_id = db.Column(db.String(100))
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    project = db.relationship('Project', backref='payments')
    recipient = db.relationship('User', backref='received_payments')
    milestone = db.relationship('Milestone', backref='payments')


class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), default='info')  # info, success, warning, error, payment, project
    
    is_read = db.Column(db.Boolean, default=False)
    link_url = db.Column(db.String(500))
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    user = db.relationship('User', backref='notifications')


# Models are imported in app.py to avoid circular imports
