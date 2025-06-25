import os
import json
import uuid
import zipfile
from io import BytesIO
from flask import render_template, request, redirect, url_for, flash, jsonify, send_file, abort
from flask_login import current_user
from sqlalchemy import or_, desc, asc
from app import app, db
from models import Project, ProjectContributor, Team, TeamMember
from collaboration_models import (CodeRepository, CodeFile, CodeCommit, LiveCodingSession, 
                                LiveSessionParticipant, CodeChange, CodeModule)
from collaboration_forms import (CodeRepositoryForm, CodeFileForm, CodeCommitForm, 
                               LiveCodingSessionForm, CodeModuleForm, ImportModuleForm, ExportModuleForm)
from replit_auth import require_login


@app.route('/projects/<int:project_id>/repositories')
@require_login
def project_repositories(project_id):
    """List all repositories for a project"""
    project = Project.query.get_or_404(project_id)
    
    # Check if user has access
    is_contributor = ProjectContributor.query.filter_by(
        project_id=project_id, user_id=current_user.id
    ).first()
    
    if not is_contributor and project.owner_id != current_user.id:
        if not project.is_public:
            abort(403)
    
    repositories = CodeRepository.query.filter_by(project_id=project_id).order_by(
        desc(CodeRepository.updated_at)
    ).all()
    
    return render_template('collaboration/repositories.html', 
                         project=project, 
                         repositories=repositories)


@app.route('/projects/<int:project_id>/repositories/create', methods=['GET', 'POST'])
@require_login
def create_repository(project_id):
    """Create a new code repository"""
    project = Project.query.get_or_404(project_id)
    
    # Check if user has write access
    is_contributor = ProjectContributor.query.filter_by(
        project_id=project_id, user_id=current_user.id
    ).first()
    
    if not is_contributor and project.owner_id != current_user.id:
        abort(403)
    
    form = CodeRepositoryForm()
    
    if form.validate_on_submit():
        repository = CodeRepository(
            name=form.name.data,
            description=form.description.data,
            project_id=project_id,
            owner_id=current_user.id,
            is_private=form.is_private.data,
            default_branch=form.default_branch.data
        )
        
        db.session.add(repository)
        db.session.commit()
        
        flash('Repository created successfully!', 'success')
        return redirect(url_for('repository_detail', repo_id=repository.id))
    
    return render_template('collaboration/create_repository.html', 
                         form=form, project=project)


@app.route('/repositories/<int:repo_id>')
@require_login
def repository_detail(repo_id):
    """View repository details and files"""
    repository = CodeRepository.query.get_or_404(repo_id)
    
    # Check access permissions
    is_contributor = ProjectContributor.query.filter_by(
        project_id=repository.project_id, user_id=current_user.id
    ).first()
    
    if not is_contributor and repository.owner_id != current_user.id:
        if repository.is_private or not repository.project.is_public:
            abort(403)
    
    # Get files
    files = CodeFile.query.filter_by(
        repository_id=repo_id, is_deleted=False
    ).order_by(CodeFile.file_path).all()
    
    # Get recent commits
    recent_commits = CodeCommit.query.filter_by(
        repository_id=repo_id
    ).order_by(desc(CodeCommit.created_at)).limit(10).all()
    
    # Check if user can edit
    can_edit = (repository.owner_id == current_user.id or 
                current_user.user_type == 'admin')
    
    return render_template('collaboration/repository_detail.html', 
                         repository=repository, 
                         can_edit=can_edit)


@app.route('/repositories/<int:repo_id>/files/create', methods=['GET', 'POST'])
@require_login
def create_file(repo_id):
    """Create a new file in repository"""
    repository = CodeRepository.query.get_or_404(repo_id)
    
    # Check write permissions
    is_contributor = ProjectContributor.query.filter_by(
        project_id=repository.project_id, user_id=current_user.id
    ).first()
    
    if not is_contributor and repository.owner_id != current_user.id:
        abort(403)
    
    form = CodeFileForm()
    
    if form.validate_on_submit():
        # Check for duplicate file path
        existing_file = CodeFile.query.filter_by(
            repository_id=repo_id,
            file_path=form.file_path.data,
            is_deleted=False
        ).first()
        
        if existing_file:
            flash('A file with this path already exists.', 'error')
            return render_template('collaboration/create_file.html', 
                                 form=form, repository=repository)
        
        # Auto-detect language if not specified
        language = form.language.data
        if not language:
            file_ext = form.filename.data.split('.')[-1].lower() if '.' in form.filename.data else ''
            language_map = {
                'py': 'python', 'js': 'javascript', 'ts': 'typescript',
                'java': 'java', 'cpp': 'cpp', 'c': 'c', 'html': 'html',
                'css': 'css', 'scss': 'scss', 'sql': 'sql', 'sh': 'bash',
                'json': 'json', 'xml': 'xml', 'yml': 'yaml', 'yaml': 'yaml',
                'md': 'markdown', 'php': 'php', 'rb': 'ruby', 'go': 'go'
            }
            language = language_map.get(file_ext, 'other')
        
        file = CodeFile(
            filename=form.filename.data,
            file_path=form.file_path.data,
            content=form.content.data,
            language=language,
            file_size=len(form.content.data.encode('utf-8')),
            repository_id=repo_id,
            last_modified_by=current_user.id
        )
        
        db.session.add(file)
        db.session.commit()
        
        flash('File created successfully!', 'success')
        return redirect(url_for('file_detail', file_id=file.id))
    
    return render_template('collaboration/create_file.html', 
                         form=form, repository=repository)


@app.route('/files/<int:file_id>')
@require_login
def file_detail(file_id):
    """View file content and details"""
    file = CodeFile.query.get_or_404(file_id)
    
    # Check access permissions
    is_contributor = ProjectContributor.query.filter_by(
        project_id=file.repository.project_id, user_id=current_user.id
    ).first()
    
    if not is_contributor and file.repository.owner_id != current_user.id:
        if file.repository.is_private or not file.repository.project.is_public:
            abort(403)
    
    return render_template('collaboration/file_detail.html', file=file)


@app.route('/files/<int:file_id>/edit', methods=['GET', 'POST'])
@require_login
def edit_file(file_id):
    """Edit file content"""
    file = CodeFile.query.get_or_404(file_id)
    
    # Check write permissions
    is_contributor = ProjectContributor.query.filter_by(
        project_id=file.repository.project_id, user_id=current_user.id
    ).first()
    
    if not is_contributor and file.repository.owner_id != current_user.id:
        abort(403)
    
    form = CodeFileForm(obj=file)
    
    if form.validate_on_submit():
        file.filename = form.filename.data
        file.file_path = form.file_path.data
        file.content = form.content.data
        file.language = form.language.data
        file.file_size = len(form.content.data.encode('utf-8'))
        file.last_modified_by = current_user.id
        file.version += 1
        
        db.session.commit()
        
        flash('File updated successfully!', 'success')
        return redirect(url_for('file_detail', file_id=file.id))
    
    return render_template('collaboration/edit_file.html', 
                         form=form, file=file)


@app.route('/projects/<int:project_id>/live-session/create', methods=['GET', 'POST'])
@require_login
def create_live_session(project_id):
    """Create a live coding session"""
    project = Project.query.get_or_404(project_id)
    
    # Check permissions
    is_contributor = ProjectContributor.query.filter_by(
        project_id=project_id, user_id=current_user.id
    ).first()
    
    if not is_contributor and project.owner_id != current_user.id:
        abort(403)
    
    form = LiveCodingSessionForm()
    
    if form.validate_on_submit():
        session = LiveCodingSession(
            session_name=form.session_name.data,
            project_id=project_id,
            host_id=current_user.id,
            max_participants=form.max_participants.data,
            allow_anonymous=form.allow_anonymous.data
        )
        
        db.session.add(session)
        db.session.flush()
        
        # Add host as participant
        participant = LiveSessionParticipant(
            session_id=session.id,
            user_id=current_user.id,
            role='host'
        )
        db.session.add(participant)
        db.session.commit()
        
        flash('Live coding session started!', 'success')
        return redirect(url_for('live_session', session_id=session.id))
    
    return render_template('collaboration/create_live_session.html', 
                         form=form, project=project)


@app.route('/live-session/<int:session_id>')
@require_login
def live_session(session_id):
    """Join a live coding session"""
    session = LiveCodingSession.query.get_or_404(session_id)
    
    if not session.is_active:
        flash('This session has ended.', 'error')
        return redirect(url_for('project_detail', project_id=session.project_id))
    
    # Check if user can join
    existing_participant = LiveSessionParticipant.query.filter_by(
        session_id=session_id, user_id=current_user.id
    ).first()
    
    if not existing_participant:
        # Check if session is full
        active_participants = LiveSessionParticipant.query.filter_by(
            session_id=session_id, is_active=True
        ).count()
        
        if active_participants >= session.max_participants:
            flash('Session is full.', 'error')
            return redirect(url_for('project_detail', project_id=session.project_id))
        
        # Add as participant
        participant = LiveSessionParticipant(
            session_id=session_id,
            user_id=current_user.id,
            role='participant'
        )
        db.session.add(participant)
        db.session.commit()
    
    # Get session files
    files = CodeFile.query.join(CodeRepository).filter(
        CodeRepository.project_id == session.project_id,
        CodeFile.is_deleted == False
    ).all()
    
    return render_template('collaboration/live_session.html', 
                         session=session, 
                         files=files)


@app.route('/modules')
def module_library():
    """Browse public code modules"""
    search_query = request.args.get('search', '')
    language = request.args.get('language', '')
    module_type = request.args.get('type', '')
    sort_by = request.args.get('sort', 'newest')
    
    # Build query
    modules_query = CodeModule.query.filter_by(is_public=True)
    
    if search_query:
        modules_query = modules_query.filter(
            or_(
                CodeModule.name.ilike(f'%{search_query}%'),
                CodeModule.description.ilike(f'%{search_query}%'),
                CodeModule.tags.ilike(f'%{search_query}%')
            )
        )
    
    if language:
        modules_query = modules_query.filter_by(language=language)
    
    if module_type:
        modules_query = modules_query.filter_by(module_type=module_type)
    
    # Apply sorting
    if sort_by == 'newest':
        modules_query = modules_query.order_by(desc(CodeModule.created_at))
    elif sort_by == 'popular':
        modules_query = modules_query.order_by(desc(CodeModule.download_count))
    elif sort_by == 'name':
        modules_query = modules_query.order_by(asc(CodeModule.name))
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    modules = modules_query.paginate(page=page, per_page=20, error_out=False)
    
    return render_template('collaboration/module_library.html', modules=modules)


@app.route('/modules/create', methods=['GET', 'POST'])
@require_login
def create_module():
    """Create a new code module"""
    form = CodeModuleForm()
    
    if form.validate_on_submit():
        module = CodeModule(
            name=form.name.data,
            description=form.description.data,
            module_type=form.module_type.data,
            code_content=form.code_content.data,
            language=form.language.data,
            dependencies=form.dependencies.data,
            tags=form.tags.data,
            is_public=form.is_public.data,
            is_reusable=form.is_reusable.data,
            author_id=current_user.id
        )
        
        db.session.add(module)
        db.session.commit()
        
        flash('Code module created successfully!', 'success')
        return redirect(url_for('module_detail', module_id=module.id))
    
    return render_template('collaboration/create_module.html', form=form)


@app.route('/modules/<int:module_id>')
def module_detail(module_id):
    """View module details"""
    module = CodeModule.query.get_or_404(module_id)
    
    if not module.is_public and module.author_id != current_user.id:
        abort(403)
    
    return render_template('collaboration/module_detail.html', module=module)


@app.route('/modules/<int:module_id>/download')
@require_login
def download_module(module_id):
    """Download a code module"""
    module = CodeModule.query.get_or_404(module_id)
    
    if not module.is_public and module.author_id != current_user.id:
        abort(403)
    
    # Increment download count
    module.download_count += 1
    db.session.commit()
    
    # Create file content
    file_content = f"""# {module.name}
# {module.description}
# Language: {module.language}
# Type: {module.module_type}
# Author: {module.author.full_name}
# Created: {module.created_at.strftime('%Y-%m-%d')}

{module.code_content}
"""
    
    # Create in-memory file
    file_buffer = BytesIO()
    file_buffer.write(file_content.encode('utf-8'))
    file_buffer.seek(0)
    
    filename = f"{module.name.replace(' ', '_')}.{module.language}"
    
    return send_file(
        file_buffer,
        mimetype='text/plain',
        as_attachment=True,
        download_name=filename
    )


@app.route('/api/live-session/<int:session_id>/sync', methods=['POST'])
@require_login
def sync_code_changes(session_id):
    """Sync real-time code changes"""
    session = LiveCodingSession.query.get_or_404(session_id)
    
    # Check if user is participant
    participant = LiveSessionParticipant.query.filter_by(
        session_id=session_id, user_id=current_user.id, is_active=True
    ).first()
    
    if not participant:
        return jsonify({'error': 'Not authorized'}), 403
    
    data = request.get_json()
    
    # Create code change record
    change = CodeChange(
        change_type=data.get('type'),
        start_line=data.get('start_line'),
        end_line=data.get('end_line'),
        start_col=data.get('start_col', 0),
        end_col=data.get('end_col', 0),
        old_content=data.get('old_content', ''),
        new_content=data.get('new_content', ''),
        file_id=data.get('file_id'),
        session_id=session_id,
        user_id=current_user.id
    )
    
    db.session.add(change)
    db.session.commit()
    
    return jsonify({'status': 'success', 'change_id': change.id})


# Initialize default forum categories
def create_default_forum_data():
    """Create default forum categories"""
    if ForumCategory.query.count() == 0:
        categories = [
            ForumCategory(name='General Discussion', description='General coding discussions and questions', 
                         color='#007bff', icon='fas fa-comments', sort_order=1),
            ForumCategory(name='Help & Support', description='Get help with coding problems and bugs', 
                         color='#28a745', icon='fas fa-question-circle', sort_order=2),
            ForumCategory(name='Code Review', description='Share code for feedback and improvement', 
                         color='#ffc107', icon='fas fa-code', sort_order=3),
            ForumCategory(name='Project Showcase', description='Show off your projects and get feedback', 
                         color='#17a2b8', icon='fas fa-rocket', sort_order=4),
            ForumCategory(name='Learning Resources', description='Share and find learning materials', 
                         color='#6f42c1', icon='fas fa-book', sort_order=5),
            ForumCategory(name='Job Board', description='Find and post coding jobs and opportunities', 
                         color='#fd7e14', icon='fas fa-briefcase', sort_order=6)
        ]
        
        for category in categories:
            db.session.add(category)
        
        db.session.commit()

# Import these models in models.py
from forum_models import ForumCategory, ForumTopic, ForumReply, ForumVote
from collaboration_models import (CodeRepository, CodeFile, CodeCommit, LiveCodingSession, 
                                LiveSessionParticipant, CodeChange, CodeModule)