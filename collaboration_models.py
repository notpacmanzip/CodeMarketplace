from datetime import datetime
from app import db
import json

class CodeRepository(db.Model):
    __tablename__ = 'code_repositories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Repository settings
    is_private = db.Column(db.Boolean, default=False)
    default_branch = db.Column(db.String(100), default='main')
    
    # Foreign keys
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    owner_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    owner = db.relationship('User', backref='owned_repositories')
    project = db.relationship('Project', backref='code_repositories')
    files = db.relationship('CodeFile', backref='repository', lazy=True, cascade='all, delete-orphan')
    commits = db.relationship('CodeCommit', backref='repository', lazy=True, cascade='all, delete-orphan')

class CodeFile(db.Model):
    __tablename__ = 'code_files'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(500), nullable=False)
    file_path = db.Column(db.String(1000), nullable=False)  # Full path in repository
    content = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(50))
    file_size = db.Column(db.Integer, default=0)
    
    # Version control
    version = db.Column(db.Integer, default=1)
    is_deleted = db.Column(db.Boolean, default=False)
    
    # Foreign keys
    repository_id = db.Column(db.Integer, db.ForeignKey('code_repositories.id'), nullable=False)
    last_modified_by = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    modifier = db.relationship('User', backref='modified_files')
    
    def get_file_extension(self):
        return self.filename.split('.')[-1] if '.' in self.filename else ''

class CodeCommit(db.Model):
    __tablename__ = 'code_commits'
    
    id = db.Column(db.Integer, primary_key=True)
    commit_hash = db.Column(db.String(40), nullable=False, unique=True)
    message = db.Column(db.Text, nullable=False)
    branch = db.Column(db.String(100), default='main')
    
    # Commit metadata
    changes_summary = db.Column(db.Text)  # JSON of file changes
    files_changed = db.Column(db.Integer, default=0)
    lines_added = db.Column(db.Integer, default=0)
    lines_removed = db.Column(db.Integer, default=0)
    
    # Foreign keys
    repository_id = db.Column(db.Integer, db.ForeignKey('code_repositories.id'), nullable=False)
    author_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    author = db.relationship('User', backref='code_commits')

class LiveCodingSession(db.Model):
    __tablename__ = 'live_coding_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_name = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Session settings
    max_participants = db.Column(db.Integer, default=10)
    allow_anonymous = db.Column(db.Boolean, default=False)
    
    # Foreign keys
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    host_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    active_file_id = db.Column(db.Integer, db.ForeignKey('code_files.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    host = db.relationship('User', backref='hosted_live_sessions')
    project = db.relationship('Project', backref='live_sessions')
    active_file = db.relationship('CodeFile', backref='active_sessions')
    participants = db.relationship('LiveSessionParticipant', backref='live_session', lazy=True, cascade='all, delete-orphan')

class LiveSessionParticipant(db.Model):
    __tablename__ = 'live_session_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(50), default='participant')  # 'host', 'editor', 'participant', 'viewer'
    is_active = db.Column(db.Boolean, default=True)
    cursor_position = db.Column(db.String(50))  # Store cursor position for real-time sync
    
    # Foreign keys
    session_id = db.Column(db.Integer, db.ForeignKey('live_coding_sessions.id'), nullable=False)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    joined_at = db.Column(db.DateTime, default=datetime.now)
    last_activity = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    user = db.relationship('User', backref='live_session_participations')

class CodeChange(db.Model):
    __tablename__ = 'code_changes'
    
    id = db.Column(db.Integer, primary_key=True)
    change_type = db.Column(db.String(50), nullable=False)  # 'insert', 'delete', 'replace'
    start_line = db.Column(db.Integer, nullable=False)
    end_line = db.Column(db.Integer, nullable=False)
    start_col = db.Column(db.Integer, default=0)
    end_col = db.Column(db.Integer, default=0)
    
    # Change content
    old_content = db.Column(db.Text)
    new_content = db.Column(db.Text)
    
    # Sync status
    is_applied = db.Column(db.Boolean, default=False)
    conflict_resolved = db.Column(db.Boolean, default=True)
    
    # Foreign keys
    file_id = db.Column(db.Integer, db.ForeignKey('code_files.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('live_coding_sessions.id'), nullable=False)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    file = db.relationship('CodeFile', backref='code_file_changes')
    session = db.relationship('LiveCodingSession', backref='code_changes')
    user = db.relationship('User', backref='authored_code_changes')

class CodeModule(db.Model):
    __tablename__ = 'code_modules'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    module_type = db.Column(db.String(50), nullable=False)  # 'function', 'class', 'component', 'snippet'
    
    # Module content
    code_content = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(50), nullable=False)
    dependencies = db.Column(db.Text)  # JSON list of dependencies
    
    # Module metadata
    is_public = db.Column(db.Boolean, default=True)
    is_reusable = db.Column(db.Boolean, default=True)
    download_count = db.Column(db.Integer, default=0)
    
    # Tags for searchability
    tags = db.Column(db.String(500))  # Comma-separated tags
    
    # Foreign keys
    author_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    repository_id = db.Column(db.Integer, db.ForeignKey('code_repositories.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    author = db.relationship('User', backref='authored_code_modules')
    project = db.relationship('Project', backref='code_modules')
    repository = db.relationship('CodeRepository', backref='code_modules')