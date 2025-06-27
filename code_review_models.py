from app import db
from datetime import datetime
from sqlalchemy import func
import uuid

class CodeSubmission(db.Model):
    __tablename__ = 'code_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(100), unique=True, nullable=False, default=lambda: str(uuid.uuid4())[:8])
    
    # Submission details
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    review_type = db.Column(db.String(50), nullable=False)  # 'performance', 'security', 'best_practices', 'general'
    programming_language = db.Column(db.String(50), nullable=False)
    framework = db.Column(db.String(100))
    
    # Code source
    submission_type = db.Column(db.String(20), nullable=False)  # 'file_upload' or 'repository_url'
    file_path = db.Column(db.String(500))  # Path to uploaded file
    repository_url = db.Column(db.String(500))  # GitHub/GitLab URL
    
    # Status and matching
    status = db.Column(db.String(30), default='pending')  # 'pending', 'matched', 'in_review', 'completed', 'cancelled'
    priority = db.Column(db.String(20), default='normal')  # 'low', 'normal', 'high', 'urgent'
    estimated_review_time = db.Column(db.Integer)  # in hours
    
    # Relationships
    submitter_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    reviewer_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.now)
    matched_at = db.Column(db.DateTime)
    review_started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    submitter = db.relationship('User', foreign_keys=[submitter_id], backref='code_submissions')
    reviewer = db.relationship('User', foreign_keys=[reviewer_id], backref='assigned_reviews')
    reviews = db.relationship('CodeReview', backref='submission', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('ReviewComment', backref='submission', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<CodeSubmission {self.ticket_id}: {self.title}>'
    
    def get_status_badge(self):
        status_colors = {
            'pending': 'warning',
            'matched': 'info',
            'in_review': 'primary',
            'completed': 'success',
            'cancelled': 'danger'
        }
        return status_colors.get(self.status, 'secondary')

class ReviewerProfile(db.Model):
    __tablename__ = 'reviewer_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Verification status
    is_verified = db.Column(db.Boolean, default=False)
    verification_date = db.Column(db.DateTime)
    verification_method = db.Column(db.String(50))  # 'portfolio', 'certification', 'test', 'manual'
    
    # Expertise
    specializations = db.Column(db.Text)  # JSON array of specializations
    programming_languages = db.Column(db.Text)  # JSON array of languages
    frameworks = db.Column(db.Text)  # JSON array of frameworks
    years_experience = db.Column(db.Integer)
    
    # Availability
    is_available = db.Column(db.Boolean, default=True)
    max_concurrent_reviews = db.Column(db.Integer, default=3)
    preferred_review_types = db.Column(db.Text)  # JSON array
    
    # Ratings and stats
    average_rating = db.Column(db.Float, default=0.0)
    total_reviews = db.Column(db.Integer, default=0)
    completed_reviews = db.Column(db.Integer, default=0)
    response_rate = db.Column(db.Float, default=100.0)
    
    # Profile information
    bio = db.Column(db.Text)
    portfolio_url = db.Column(db.String(500))
    linkedin_url = db.Column(db.String(500))
    github_url = db.Column(db.String(500))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    user = db.relationship('User', backref='reviewer_profile')
    
    def get_current_review_count(self):
        return CodeSubmission.query.filter_by(
            reviewer_id=self.user_id,
            status='in_review'
        ).count()
    
    def can_accept_review(self):
        return (self.is_verified and 
                self.is_available and 
                self.get_current_review_count() < self.max_concurrent_reviews)
    
    def __repr__(self):
        return f'<ReviewerProfile {self.user_id}>'

class CodeReview(db.Model):
    __tablename__ = 'code_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Review content
    summary_feedback = db.Column(db.Text, nullable=False)
    performance_notes = db.Column(db.Text)
    security_notes = db.Column(db.Text)
    best_practices_notes = db.Column(db.Text)
    
    # Ratings (1-5 scale)
    code_quality_rating = db.Column(db.Integer)
    security_rating = db.Column(db.Integer)
    performance_rating = db.Column(db.Integer)
    maintainability_rating = db.Column(db.Integer)
    overall_rating = db.Column(db.Integer)
    
    # Files and attachments
    report_file_path = db.Column(db.String(500))
    fixed_code_path = db.Column(db.String(500))
    
    # Review metadata
    time_spent = db.Column(db.Integer)  # in minutes
    complexity_assessment = db.Column(db.String(20))  # 'low', 'medium', 'high'
    
    # Relationships
    submission_id = db.Column(db.Integer, db.ForeignKey('code_submissions.id'), nullable=False)
    reviewer_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    reviewer = db.relationship('User', backref='authored_reviews')
    
    def get_average_rating(self):
        ratings = [
            self.code_quality_rating,
            self.security_rating,
            self.performance_rating,
            self.maintainability_rating
        ]
        valid_ratings = [r for r in ratings if r is not None]
        return sum(valid_ratings) / len(valid_ratings) if valid_ratings else 0

class ReviewComment(db.Model):
    __tablename__ = 'review_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Comment details
    file_path = db.Column(db.String(500))
    line_number = db.Column(db.Integer)
    comment_text = db.Column(db.Text, nullable=False)
    comment_type = db.Column(db.String(30))  # 'suggestion', 'issue', 'question', 'compliment'
    severity = db.Column(db.String(20))  # 'low', 'medium', 'high', 'critical'
    
    # Code context
    original_code = db.Column(db.Text)
    suggested_code = db.Column(db.Text)
    
    # Status
    is_resolved = db.Column(db.Boolean, default=False)
    submitter_response = db.Column(db.Text)
    
    # Relationships
    submission_id = db.Column(db.Integer, db.ForeignKey('code_submissions.id'), nullable=False)
    reviewer_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    reviewer = db.relationship('User', backref='review_comments')
    
    def get_severity_badge(self):
        severity_colors = {
            'low': 'info',
            'medium': 'warning',
            'high': 'danger',
            'critical': 'dark'
        }
        return severity_colors.get(self.severity, 'secondary')

class ReviewRating(db.Model):
    __tablename__ = 'review_ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Rating details
    overall_rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    helpfulness_rating = db.Column(db.Integer)
    communication_rating = db.Column(db.Integer)
    timeliness_rating = db.Column(db.Integer)
    
    # Feedback
    feedback_text = db.Column(db.Text)
    would_recommend = db.Column(db.Boolean)
    
    # Relationships
    submission_id = db.Column(db.Integer, db.ForeignKey('code_submissions.id'), nullable=False)
    reviewer_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    submitter_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    submission = db.relationship('CodeSubmission', backref='ratings')
    reviewer = db.relationship('User', foreign_keys=[reviewer_id], backref='received_ratings')
    submitter = db.relationship('User', foreign_keys=[submitter_id], backref='given_ratings')

class ReviewNotification(db.Model):
    __tablename__ = 'review_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Notification details
    type = db.Column(db.String(50), nullable=False)  # 'new_submission', 'review_matched', 'review_started', 'review_completed'
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Status
    is_read = db.Column(db.Boolean, default=False)
    is_sent_email = db.Column(db.Boolean, default=False)
    
    # Relationships
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    submission_id = db.Column(db.Integer, db.ForeignKey('code_submissions.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.now)
    read_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref='review_notifications')
    submission = db.relationship('CodeSubmission', backref='notifications')
    
    def mark_as_read(self):
        self.is_read = True
        self.read_at = datetime.now()
        db.session.commit()