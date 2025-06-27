from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from code_review_models import (CodeSubmission, ReviewerProfile, CodeReview, 
                               ReviewComment, ReviewRating, ReviewNotification)
from code_review_forms import (CodeSubmissionForm, ReviewerProfileForm, CodeReviewForm,
                              ReviewCommentForm, ReviewRatingForm, ReviewerSearchForm)
from models import User
from app import db
import os
import uuid
import zipfile
import tarfile
import json
import requests
from datetime import datetime, timedelta
import tempfile
import shutil

code_review_bp = Blueprint('code_review', __name__, url_prefix='/code-review')

# Utility functions
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def validate_github_url(url):
    """Validate GitHub/GitLab URL and check if repository exists"""
    try:
        if 'github.com' in url:
            # Convert to API URL
            parts = url.replace('https://github.com/', '').split('/')
            if len(parts) >= 2:
                api_url = f"https://api.github.com/repos/{parts[0]}/{parts[1]}"
                response = requests.get(api_url, timeout=10)
                return response.status_code == 200
        elif 'gitlab.com' in url:
            # Convert to API URL
            parts = url.replace('https://gitlab.com/', '').split('/')
            if len(parts) >= 2:
                project_path = f"{parts[0]}%2F{parts[1]}"
                api_url = f"https://gitlab.com/api/v4/projects/{project_path}"
                response = requests.get(api_url, timeout=10)
                return response.status_code == 200
    except:
        return False
    return False

def create_notification(user_id, notification_type, title, message, submission_id=None):
    """Create a notification for a user"""
    notification = ReviewNotification(
        user_id=user_id,
        type=notification_type,
        title=title,
        message=message,
        submission_id=submission_id
    )
    db.session.add(notification)
    db.session.commit()

def find_suitable_reviewers(submission):
    """Find reviewers that match the submission requirements"""
    reviewers = ReviewerProfile.query.filter_by(
        is_verified=True,
        is_available=True
    ).all()
    
    suitable_reviewers = []
    for reviewer in reviewers:
        if reviewer.can_accept_review():
            # Check if reviewer matches the requirements
            languages = json.loads(reviewer.programming_languages or '[]')
            specializations = json.loads(reviewer.specializations or '[]')
            preferred_types = json.loads(reviewer.preferred_review_types or '[]')
            
            score = 0
            if submission.programming_language.lower() in [lang.lower() for lang in languages]:
                score += 3
            if submission.review_type in preferred_types:
                score += 2
            if any(spec.lower() in submission.description.lower() for spec in specializations):
                score += 1
                
            if score > 0:
                suitable_reviewers.append((reviewer, score))
    
    # Sort by score (highest first) and then by rating
    suitable_reviewers.sort(key=lambda x: (x[1], x[0].average_rating), reverse=True)
    return [reviewer for reviewer, score in suitable_reviewers]

# Main routes
@code_review_bp.route('/')
def dashboard():
    """Code review dashboard"""
    if current_user.is_authenticated:
        # Get user's submissions
        submissions = CodeSubmission.query.filter_by(submitter_id=current_user.id).order_by(
            CodeSubmission.created_at.desc()
        ).limit(5).all()
        
        # Get user's assigned reviews (if they're a reviewer)
        assigned_reviews = []
        reviewer_profile = ReviewerProfile.query.filter_by(user_id=current_user.id).first()
        if reviewer_profile:
            assigned_reviews = CodeSubmission.query.filter_by(
                reviewer_id=current_user.id,
                status='in_review'
            ).limit(5).all()
        
        # Get notifications
        notifications = ReviewNotification.query.filter_by(
            user_id=current_user.id,
            is_read=False
        ).order_by(ReviewNotification.created_at.desc()).limit(5).all()
        
        return render_template('code_review/dashboard.html',
                             submissions=submissions,
                             assigned_reviews=assigned_reviews,
                             notifications=notifications,
                             reviewer_profile=reviewer_profile)
    else:
        # Public dashboard showing statistics
        total_submissions = CodeSubmission.query.count()
        completed_reviews = CodeSubmission.query.filter_by(status='completed').count()
        active_reviewers = ReviewerProfile.query.filter_by(is_verified=True, is_available=True).count()
        
        return render_template('code_review/public_dashboard.html',
                             total_submissions=total_submissions,
                             completed_reviews=completed_reviews,
                             active_reviewers=active_reviewers)

@code_review_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_code():
    """Submit code for review"""
    form = CodeSubmissionForm()
    
    if form.validate_on_submit():
        try:
            # Create submission
            submission = CodeSubmission(
                title=form.title.data,
                description=form.description.data,
                review_type=form.review_type.data,
                programming_language=form.programming_language.data,
                framework=form.framework.data,
                submission_type=form.submission_type.data,
                priority=form.priority.data,
                estimated_review_time=form.estimated_review_time.data,
                submitter_id=current_user.id,
                status='pending'
            )
            
            # Handle file upload
            if form.submission_type.data == 'file_upload' and form.code_file.data:
                file = form.code_file.data
                if file and allowed_file(file.filename, {'zip', 'tar', 'gz'}):
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    
                    # Create upload directory if it doesn't exist
                    upload_dir = os.path.join(current_app.root_path, 'static', 'code_uploads')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    file_path = os.path.join(upload_dir, unique_filename)
                    file.save(file_path)
                    
                    # Validate the uploaded file
                    if not validate_uploaded_file(file_path):
                        os.remove(file_path)
                        flash('Invalid file format or file is corrupted.', 'error')
                        return render_template('code_review/submit.html', form=form)
                    
                    submission.file_path = f"static/code_uploads/{unique_filename}"
                    
            # Handle repository URL
            elif form.submission_type.data == 'repository_url' and form.repository_url.data:
                if not validate_github_url(form.repository_url.data):
                    flash('Invalid repository URL or repository is not accessible.', 'error')
                    return render_template('code_review/submit.html', form=form)
                submission.repository_url = form.repository_url.data
            
            else:
                flash('Please provide either a file upload or repository URL.', 'error')
                return render_template('code_review/submit.html', form=form)
            
            # Save submission
            db.session.add(submission)
            db.session.commit()
            
            # Try to match with reviewers
            suitable_reviewers = find_suitable_reviewers(submission)
            
            if suitable_reviewers:
                # Auto-assign to best reviewer if available
                best_reviewer = suitable_reviewers[0]
                submission.reviewer_id = best_reviewer.user_id
                submission.status = 'matched'
                submission.matched_at = datetime.now()
                
                # Create notifications
                create_notification(
                    submission.reviewer_id,
                    'new_assignment',
                    'New Code Review Assignment',
                    f'You have been assigned to review "{submission.title}" (Ticket: {submission.ticket_id})',
                    submission.id
                )
                
                create_notification(
                    current_user.id,
                    'review_matched',
                    'Code Review Matched',
                    f'Your submission "{submission.title}" has been matched with a reviewer.',
                    submission.id
                )
                
                db.session.commit()
                flash(f'Code submitted successfully! Ticket ID: {submission.ticket_id}. You\'ve been matched with a reviewer.', 'success')
            else:
                flash(f'Code submitted successfully! Ticket ID: {submission.ticket_id}. We\'re finding a suitable reviewer for you.', 'info')
            
            return redirect(url_for('code_review.submission_detail', submission_id=submission.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting code: {str(e)}', 'error')
            
    return render_template('code_review/submit.html', form=form)

def validate_uploaded_file(file_path):
    """Validate uploaded file integrity"""
    try:
        if file_path.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.testzip()
        elif file_path.endswith(('.tar', '.tar.gz')):
            with tarfile.open(file_path, 'r') as tar_ref:
                tar_ref.getmembers()
        return True
    except:
        return False

@code_review_bp.route('/submissions')
@login_required
def my_submissions():
    """View user's submissions"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = CodeSubmission.query.filter_by(submitter_id=current_user.id)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    submissions = query.order_by(CodeSubmission.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('code_review/my_submissions.html', 
                         submissions=submissions, 
                         status_filter=status_filter)

@code_review_bp.route('/submission/<int:submission_id>')
@login_required
def submission_detail(submission_id):
    """View submission details"""
    submission = CodeSubmission.query.get_or_404(submission_id)
    
    # Check permissions
    if (submission.submitter_id != current_user.id and 
        submission.reviewer_id != current_user.id and 
        not current_user.is_admin):
        flash('Access denied.', 'error')
        return redirect(url_for('code_review.dashboard'))
    
    # Get review if exists
    review = CodeReview.query.filter_by(submission_id=submission_id).first()
    
    # Get comments
    comments = ReviewComment.query.filter_by(submission_id=submission_id).order_by(
        ReviewComment.created_at.asc()
    ).all()
    
    # Get rating if exists
    rating = ReviewRating.query.filter_by(submission_id=submission_id).first()
    
    return render_template('code_review/submission_detail.html',
                         submission=submission,
                         review=review,
                         comments=comments,
                         rating=rating)

@code_review_bp.route('/become-reviewer', methods=['GET', 'POST'])
@login_required
def become_reviewer():
    """Apply to become a reviewer"""
    existing_profile = ReviewerProfile.query.filter_by(user_id=current_user.id).first()
    
    if existing_profile:
        flash('You already have a reviewer profile.', 'info')
        return redirect(url_for('code_review.reviewer_profile'))
    
    form = ReviewerProfileForm()
    
    if form.validate_on_submit():
        try:
            profile = ReviewerProfile(
                user_id=current_user.id,
                bio=form.bio.data,
                specializations=json.dumps([s.strip() for s in (form.specializations.data or '').split(',')]),
                programming_languages=json.dumps([l.strip() for l in (form.programming_languages.data or '').split(',')]),
                frameworks=json.dumps([f.strip() for f in (form.frameworks.data or '').split(',') if f.strip()]),
                years_experience=form.years_experience.data,
                max_concurrent_reviews=form.max_concurrent_reviews.data,
                preferred_review_types=json.dumps([t.strip() for t in (form.preferred_review_types.data or '').split(',') if t.strip()]),
                portfolio_url=form.portfolio_url.data,
                linkedin_url=form.linkedin_url.data,
                github_url=form.github_url.data,
                is_available=form.is_available.data,
                is_verified=False  # Requires manual verification
            )
            
            db.session.add(profile)
            db.session.commit()
            
            flash('Reviewer application submitted! Your profile will be reviewed for verification.', 'success')
            return redirect(url_for('code_review.reviewer_profile'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating reviewer profile: {str(e)}', 'error')
    
    return render_template('code_review/become_reviewer.html', form=form)

@code_review_bp.route('/reviewer-profile')
@login_required
def reviewer_profile():
    """View reviewer profile"""
    profile = ReviewerProfile.query.filter_by(user_id=current_user.id).first()
    
    if not profile:
        flash('You need to apply to become a reviewer first.', 'info')
        return redirect(url_for('code_review.become_reviewer'))
    
    # Get recent reviews
    recent_reviews = CodeSubmission.query.filter_by(
        reviewer_id=current_user.id,
        status='completed'
    ).order_by(CodeSubmission.completed_at.desc()).limit(5).all()
    
    return render_template('code_review/reviewer_profile.html', 
                         profile=profile, 
                         recent_reviews=recent_reviews)

@code_review_bp.route('/review/<int:submission_id>', methods=['GET', 'POST'])
@login_required
def conduct_review(submission_id):
    """Conduct a code review"""
    submission = CodeSubmission.query.get_or_404(submission_id)
    
    # Check if user is the assigned reviewer
    if submission.reviewer_id != current_user.id:
        flash('Access denied. You are not assigned to this review.', 'error')
        return redirect(url_for('code_review.dashboard'))
    
    # Check if review already exists
    existing_review = CodeReview.query.filter_by(submission_id=submission_id).first()
    if existing_review:
        flash('Review already completed for this submission.', 'info')
        return redirect(url_for('code_review.submission_detail', submission_id=submission_id))
    
    form = CodeReviewForm()
    comment_form = ReviewCommentForm()
    
    if form.validate_on_submit():
        try:
            # Create review
            review = CodeReview(
                submission_id=submission_id,
                reviewer_id=current_user.id,
                summary_feedback=form.summary_feedback.data,
                performance_notes=form.performance_notes.data,
                security_notes=form.security_notes.data,
                best_practices_notes=form.best_practices_notes.data,
                code_quality_rating=form.code_quality_rating.data,
                security_rating=form.security_rating.data,
                performance_rating=form.performance_rating.data,
                maintainability_rating=form.maintainability_rating.data,
                complexity_assessment=form.complexity_assessment.data,
                time_spent=form.time_spent.data
            )
            
            # Handle file uploads
            if form.report_file.data:
                file = form.report_file.data
                if allowed_file(file.filename, {'pdf', 'doc', 'docx', 'txt'}):
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    
                    upload_dir = os.path.join(current_app.root_path, 'static', 'review_reports')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    file_path = os.path.join(upload_dir, unique_filename)
                    file.save(file_path)
                    review.report_file_path = f"static/review_reports/{unique_filename}"
            
            if form.fixed_code_file.data:
                file = form.fixed_code_file.data
                if allowed_file(file.filename, {'zip', 'tar', 'gz'}):
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    
                    upload_dir = os.path.join(current_app.root_path, 'static', 'fixed_code')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    file_path = os.path.join(upload_dir, unique_filename)
                    file.save(file_path)
                    review.fixed_code_path = f"static/fixed_code/{unique_filename}"
            
            # Calculate overall rating
            review.overall_rating = review.get_average_rating()
            
            # Update submission status
            submission.status = 'completed'
            submission.completed_at = datetime.now()
            
            # Update reviewer profile stats
            reviewer_profile = ReviewerProfile.query.filter_by(user_id=current_user.id).first()
            if reviewer_profile:
                reviewer_profile.completed_reviews += 1
                reviewer_profile.total_reviews += 1
            
            db.session.add(review)
            db.session.commit()
            
            # Create notification for submitter
            create_notification(
                submission.submitter_id,
                'review_completed',
                'Code Review Completed',
                f'Your code review for "{submission.title}" has been completed.',
                submission.id
            )
            
            flash('Review submitted successfully!', 'success')
            return redirect(url_for('code_review.submission_detail', submission_id=submission_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting review: {str(e)}', 'error')
    
    return render_template('code_review/conduct_review.html', 
                         submission=submission, 
                         form=form, 
                         comment_form=comment_form)

@code_review_bp.route('/add-comment', methods=['POST'])
@login_required
def add_comment():
    """Add a comment to a submission"""
    form = ReviewCommentForm()
    
    if form.validate_on_submit():
        try:
            submission = CodeSubmission.query.get_or_404(form.submission_id.data)
            
            # Check permissions
            if (submission.reviewer_id != current_user.id and 
                submission.submitter_id != current_user.id):
                return jsonify({'error': 'Access denied'}), 403
            
            comment = ReviewComment(
                submission_id=form.submission_id.data,
                reviewer_id=current_user.id,
                file_path=form.file_path.data,
                line_number=form.line_number.data,
                comment_text=form.comment_text.data,
                comment_type=form.comment_type.data,
                severity=form.severity.data,
                original_code=form.original_code.data,
                suggested_code=form.suggested_code.data
            )
            
            db.session.add(comment)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Comment added successfully'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid form data'}), 400

@code_review_bp.route('/reviewers')
def browse_reviewers():
    """Browse available reviewers"""
    form = ReviewerSearchForm()
    page = request.args.get('page', 1, type=int)
    
    query = ReviewerProfile.query.filter_by(is_verified=True)
    
    # Apply filters
    if request.args.get('specialization'):
        specialization = request.args.get('specialization')
        query = query.filter(ReviewerProfile.specializations.contains(specialization))
    
    if request.args.get('programming_language'):
        language = request.args.get('programming_language')
        query = query.filter(ReviewerProfile.programming_languages.contains(language))
    
    if request.args.get('min_rating'):
        min_rating = float(request.args.get('min_rating'))
        query = query.filter(ReviewerProfile.average_rating >= min_rating)
    
    if request.args.get('availability') == 'available':
        query = query.filter_by(is_available=True)
    
    reviewers = query.order_by(ReviewerProfile.average_rating.desc()).paginate(
        page=page, per_page=12, error_out=False
    )
    
    return render_template('code_review/browse_reviewers.html', 
                         reviewers=reviewers, 
                         form=form)

@code_review_bp.route('/rate-reviewer/<int:submission_id>', methods=['GET', 'POST'])
@login_required
def rate_reviewer(submission_id):
    """Rate a reviewer after review completion"""
    submission = CodeSubmission.query.get_or_404(submission_id)
    
    # Check permissions
    if submission.submitter_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('code_review.dashboard'))
    
    # Check if review is completed
    if submission.status != 'completed':
        flash('Review must be completed before rating.', 'error')
        return redirect(url_for('code_review.submission_detail', submission_id=submission_id))
    
    # Check if already rated
    existing_rating = ReviewRating.query.filter_by(submission_id=submission_id).first()
    if existing_rating:
        flash('You have already rated this reviewer.', 'info')
        return redirect(url_for('code_review.submission_detail', submission_id=submission_id))
    
    form = ReviewRatingForm()
    
    if form.validate_on_submit():
        try:
            rating = ReviewRating(
                submission_id=submission_id,
                reviewer_id=submission.reviewer_id,
                submitter_id=current_user.id,
                overall_rating=form.overall_rating.data,
                helpfulness_rating=form.helpfulness_rating.data,
                communication_rating=form.communication_rating.data,
                timeliness_rating=form.timeliness_rating.data,
                feedback_text=form.feedback_text.data,
                would_recommend=form.would_recommend.data
            )
            
            db.session.add(rating)
            
            # Update reviewer's average rating
            reviewer_profile = ReviewerProfile.query.filter_by(user_id=submission.reviewer_id).first()
            if reviewer_profile:
                # Calculate new average rating
                all_ratings = ReviewRating.query.filter_by(reviewer_id=submission.reviewer_id).all()
                if all_ratings:
                    total_rating = sum(r.overall_rating for r in all_ratings) + form.overall_rating.data
                    reviewer_profile.average_rating = total_rating / (len(all_ratings) + 1)
            
            db.session.commit()
            
            flash('Rating submitted successfully!', 'success')
            return redirect(url_for('code_review.submission_detail', submission_id=submission_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting rating: {str(e)}', 'error')
    
    return render_template('code_review/rate_reviewer.html', 
                         submission=submission, 
                         form=form)

@code_review_bp.route('/notifications')
@login_required
def notifications():
    """View user notifications"""
    page = request.args.get('page', 1, type=int)
    
    notifications = ReviewNotification.query.filter_by(
        user_id=current_user.id
    ).order_by(ReviewNotification.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Mark all as read
    unread_notifications = ReviewNotification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).all()
    
    for notification in unread_notifications:
        notification.mark_as_read()
    
    return render_template('code_review/notifications.html', notifications=notifications)

# Admin routes
@code_review_bp.route('/admin/verify-reviewer/<int:profile_id>')
@login_required
def verify_reviewer(profile_id):
    """Admin: Verify a reviewer profile"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('code_review.dashboard'))
    
    profile = ReviewerProfile.query.get_or_404(profile_id)
    profile.is_verified = True
    profile.verification_date = datetime.now()
    profile.verification_method = 'manual'
    
    db.session.commit()
    
    # Create notification for the reviewer
    create_notification(
        profile.user_id,
        'profile_verified',
        'Reviewer Profile Verified',
        'Congratulations! Your reviewer profile has been verified and you can now accept review assignments.'
    )
    
    flash('Reviewer profile verified successfully.', 'success')
    return redirect(url_for('code_review.browse_reviewers'))