from datetime import datetime
from app import db

class ForumCategory(db.Model):
    __tablename__ = 'forum_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#007bff')  # Hex color
    icon = db.Column(db.String(50), default='fas fa-comments')
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    topics = db.relationship('ForumTopic', backref='category', lazy=True, cascade='all, delete-orphan')

class ForumTopic(db.Model):
    __tablename__ = 'forum_topics'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_pinned = db.Column(db.Boolean, default=False)
    is_locked = db.Column(db.Boolean, default=False)
    is_solved = db.Column(db.Boolean, default=False)
    views_count = db.Column(db.Integer, default=0)
    
    # Code snippet fields
    code_snippet = db.Column(db.Text)
    code_language = db.Column(db.String(50))
    
    # Tags for better categorization
    tags = db.Column(db.String(500))  # Comma-separated tags
    
    # Foreign keys
    category_id = db.Column(db.Integer, db.ForeignKey('forum_categories.id'), nullable=False)
    author_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    author = db.relationship('User', backref='forum_topics')
    replies = db.relationship('ForumReply', backref='topic', lazy=True, cascade='all, delete-orphan')
    
    @property
    def reply_count(self):
        return len(self.replies)
    
    @property
    def last_reply(self):
        return self.replies[-1] if self.replies else None

class ForumReply(db.Model):
    __tablename__ = 'forum_replies'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    is_solution = db.Column(db.Boolean, default=False)
    
    # Code snippet fields
    code_snippet = db.Column(db.Text)
    code_language = db.Column(db.String(50))
    
    # Foreign keys
    topic_id = db.Column(db.Integer, db.ForeignKey('forum_topics.id'), nullable=False)
    author_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    reply_to_id = db.Column(db.Integer, db.ForeignKey('forum_replies.id'), nullable=True)  # For nested replies
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    author = db.relationship('User', backref='forum_replies')
    replies = db.relationship('ForumReply', backref='parent_reply', remote_side=[id])

class ForumVote(db.Model):
    __tablename__ = 'forum_votes'
    
    id = db.Column(db.Integer, primary_key=True)
    vote_type = db.Column(db.String(10), nullable=False)  # 'upvote' or 'downvote'
    
    # Foreign keys
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('forum_topics.id'), nullable=True)
    reply_id = db.Column(db.Integer, db.ForeignKey('forum_replies.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    user = db.relationship('User', backref='forum_votes')
    topic = db.relationship('ForumTopic', backref='votes')
    reply = db.relationship('ForumReply', backref='votes')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'topic_id', name='unique_user_topic_vote'),
        db.UniqueConstraint('user_id', 'reply_id', name='unique_user_reply_vote'),
    )