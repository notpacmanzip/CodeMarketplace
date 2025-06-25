import os
from flask import render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import current_user
from sqlalchemy import or_, desc, asc, func
from app import app, db
from models import User
from forum_models import ForumCategory, ForumTopic, ForumReply, ForumVote
from forum_forms import ForumTopicForm, ForumReplyForm, ForumSearchForm
from replit_auth import require_login


@app.route('/forum')
def forum_index():
    """Forum main page"""
    categories = ForumCategory.query.filter_by(is_active=True).order_by(ForumCategory.sort_order).all()
    
    # Get recent topics
    recent_topics = ForumTopic.query.join(ForumCategory).filter(
        ForumCategory.is_active == True
    ).order_by(desc(ForumTopic.created_at)).limit(10).all()
    
    # Forum statistics
    stats = {
        'total_topics': ForumTopic.query.count(),
        'total_replies': ForumReply.query.count(),
        'total_users': User.query.count(),
        'solved_topics': ForumTopic.query.filter_by(is_solved=True).count()
    }
    
    return render_template('forum/index.html', 
                         categories=categories, 
                         recent_topics=recent_topics,
                         stats=stats)


@app.route('/forum/category/<int:category_id>')
def forum_category(category_id):
    """View topics in a specific category"""
    category = ForumCategory.query.get_or_404(category_id)
    
    # Search and filtering
    search_form = ForumSearchForm()
    query = request.args.get('query', '')
    sort_by = request.args.get('sort_by', 'newest')
    
    # Build topics query
    topics_query = ForumTopic.query.filter_by(category_id=category_id)
    
    if query:
        topics_query = topics_query.filter(
            or_(
                ForumTopic.title.ilike(f'%{query}%'),
                ForumTopic.content.ilike(f'%{query}%'),
                ForumTopic.tags.ilike(f'%{query}%')
            )
        )
    
    # Apply sorting
    if sort_by == 'newest':
        topics_query = topics_query.order_by(desc(ForumTopic.created_at))
    elif sort_by == 'oldest':
        topics_query = topics_query.order_by(asc(ForumTopic.created_at))
    elif sort_by == 'most_replies':
        topics_query = topics_query.outerjoin(ForumReply).group_by(ForumTopic.id).order_by(desc(func.count(ForumReply.id)))
    elif sort_by == 'most_views':
        topics_query = topics_query.order_by(desc(ForumTopic.views_count))
    elif sort_by == 'solved':
        topics_query = topics_query.order_by(desc(ForumTopic.is_solved), desc(ForumTopic.created_at))
    elif sort_by == 'unsolved':
        topics_query = topics_query.order_by(asc(ForumTopic.is_solved), desc(ForumTopic.created_at))
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    topics = topics_query.paginate(page=page, per_page=20, error_out=False)
    
    return render_template('forum/category.html', 
                         category=category, 
                         topics=topics,
                         search_form=search_form)


@app.route('/forum/topic/<int:topic_id>')
def forum_topic(topic_id):
    """View a forum topic and its replies"""
    topic = ForumTopic.query.get_or_404(topic_id)
    
    # Increment view count (only if not the author)
    if not current_user.is_authenticated or current_user.id != topic.author_id:
        topic.views_count += 1
        db.session.commit()
    
    # Get replies with pagination
    page = request.args.get('page', 1, type=int)
    replies = ForumReply.query.filter_by(topic_id=topic_id, reply_to_id=None).order_by(
        asc(ForumReply.created_at)
    ).paginate(page=page, per_page=10, error_out=False)
    
    # Reply form
    reply_form = ForumReplyForm()
    
    return render_template('forum/topic.html', 
                         topic=topic, 
                         replies=replies,
                         reply_form=reply_form)


@app.route('/forum/create-topic', methods=['GET', 'POST'])
@app.route('/forum/create-topic/<int:category_id>', methods=['GET', 'POST'])
@require_login
def create_forum_topic(category_id=None):
    """Create a new forum topic"""
    form = ForumTopicForm()
    
    # Populate category choices
    categories = ForumCategory.query.filter_by(is_active=True).order_by(ForumCategory.name).all()
    form.category_id.choices = [(cat.id, cat.name) for cat in categories]
    
    if category_id:
        form.category_id.data = category_id
    
    if form.validate_on_submit():
        topic = ForumTopic(
            title=form.title.data,
            content=form.content.data,
            category_id=form.category_id.data,
            author_id=current_user.id,
            tags=form.tags.data,
            code_snippet=form.code_snippet.data,
            code_language=form.code_language.data,
            is_pinned=form.is_pinned.data if current_user.user_type == 'admin' else False
        )
        
        db.session.add(topic)
        db.session.commit()
        
        flash('Topic created successfully!', 'success')
        return redirect(url_for('forum_topic', topic_id=topic.id))
    
    return render_template('forum/create_topic.html', form=form, category_id=category_id)


@app.route('/forum/topic/<int:topic_id>/reply', methods=['POST'])
@require_login
def create_forum_reply(topic_id):
    """Create a reply to a forum topic"""
    topic = ForumTopic.query.get_or_404(topic_id)
    
    if topic.is_locked:
        flash('This topic is locked and cannot receive new replies.', 'error')
        return redirect(url_for('forum_topic', topic_id=topic_id))
    
    form = ForumReplyForm()
    
    if form.validate_on_submit():
        reply = ForumReply(
            content=form.content.data,
            topic_id=topic_id,
            author_id=current_user.id,
            code_snippet=form.code_snippet.data,
            code_language=form.code_language.data,
            reply_to_id=form.reply_to_id.data if form.reply_to_id.data else None,
            is_solution=form.is_solution.data and (current_user.id == topic.author_id or current_user.user_type == 'admin')
        )
        
        db.session.add(reply)
        
        # Mark topic as solved if this is a solution
        if reply.is_solution:
            topic.is_solved = True
        
        db.session.commit()
        
        flash('Reply posted successfully!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
    
    return redirect(url_for('forum_topic', topic_id=topic_id))


@app.route('/forum/vote', methods=['POST'])
@require_login
def forum_vote():
    """Vote on topics or replies"""
    data = request.get_json()
    
    vote_type = data.get('vote_type')  # 'upvote' or 'downvote'
    topic_id = data.get('topic_id')
    reply_id = data.get('reply_id')
    
    if not vote_type or vote_type not in ['upvote', 'downvote']:
        return jsonify({'error': 'Invalid vote type'}), 400
    
    if not topic_id and not reply_id:
        return jsonify({'error': 'Must specify topic_id or reply_id'}), 400
    
    # Check for existing vote
    existing_vote = ForumVote.query.filter_by(
        user_id=current_user.id,
        topic_id=topic_id,
        reply_id=reply_id
    ).first()
    
    if existing_vote:
        if existing_vote.vote_type == vote_type:
            # Remove vote if clicking same vote type
            db.session.delete(existing_vote)
            action = 'removed'
        else:
            # Change vote type
            existing_vote.vote_type = vote_type
            action = 'changed'
    else:
        # Create new vote
        vote = ForumVote(
            user_id=current_user.id,
            topic_id=topic_id,
            reply_id=reply_id,
            vote_type=vote_type
        )
        db.session.add(vote)
        action = 'added'
    
    db.session.commit()
    
    # Calculate vote counts
    if topic_id:
        upvotes = ForumVote.query.filter_by(topic_id=topic_id, vote_type='upvote').count()
        downvotes = ForumVote.query.filter_by(topic_id=topic_id, vote_type='downvote').count()
    else:
        upvotes = ForumVote.query.filter_by(reply_id=reply_id, vote_type='upvote').count()
        downvotes = ForumVote.query.filter_by(reply_id=reply_id, vote_type='downvote').count()
    
    return jsonify({
        'action': action,
        'upvotes': upvotes,
        'downvotes': downvotes,
        'score': upvotes - downvotes
    })


@app.route('/forum/search')
def forum_search():
    """Search forum topics and replies"""
    form = ForumSearchForm()
    query = request.args.get('query', '')
    category_id = request.args.get('category_id', type=int)
    sort_by = request.args.get('sort_by', 'newest')
    
    # Populate category choices
    categories = ForumCategory.query.filter_by(is_active=True).order_by(ForumCategory.name).all()
    form.category_id.choices = [('', 'All Categories')] + [(cat.id, cat.name) for cat in categories]
    
    topics = []
    if query:
        # Build search query
        topics_query = ForumTopic.query.join(ForumCategory).filter(ForumCategory.is_active == True)
        
        # Apply search filter
        topics_query = topics_query.filter(
            or_(
                ForumTopic.title.ilike(f'%{query}%'),
                ForumTopic.content.ilike(f'%{query}%'),
                ForumTopic.tags.ilike(f'%{query}%')
            )
        )
        
        # Apply category filter
        if category_id:
            topics_query = topics_query.filter(ForumTopic.category_id == category_id)
        
        # Apply sorting
        if sort_by == 'newest':
            topics_query = topics_query.order_by(desc(ForumTopic.created_at))
        elif sort_by == 'oldest':
            topics_query = topics_query.order_by(asc(ForumTopic.created_at))
        elif sort_by == 'most_replies':
            topics_query = topics_query.outerjoin(ForumReply).group_by(ForumTopic.id).order_by(desc(func.count(ForumReply.id)))
        elif sort_by == 'most_views':
            topics_query = topics_query.order_by(desc(ForumTopic.views_count))
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        topics = topics_query.paginate(page=page, per_page=20, error_out=False)
    
    return render_template('forum/search.html', 
                         form=form, 
                         topics=topics,
                         query=query)