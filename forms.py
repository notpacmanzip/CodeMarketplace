from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, DecimalField, BooleanField, IntegerField, HiddenField, SubmitField, DateTimeLocalField, URLField
from wtforms.validators import DataRequired, Email, Length, NumberRange, URL, Optional

class ProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[Length(max=50)])
    last_name = StringField('Last Name', validators=[Length(max=50)])
    company = StringField('Company', validators=[Length(max=100)])
    bio = TextAreaField('Bio', validators=[Length(max=1000)])
    location = StringField('Location', validators=[Length(max=100)])
    website = StringField('Website', validators=[Optional(), URL()])
    github_url = StringField('GitHub URL', validators=[Optional(), URL()])
    user_type = SelectField('Account Type', choices=[('buyer', 'Buyer'), ('seller', 'Seller')], validators=[DataRequired()])

class ProductForm(FlaskForm):
    title = StringField('Product Title', validators=[DataRequired(), Length(min=10, max=200)])
    short_description = StringField('Short Description', validators=[DataRequired(), Length(min=20, max=500)])
    description = TextAreaField('Full Description', validators=[DataRequired(), Length(min=50)])
    price = DecimalField('Price (USD)', validators=[DataRequired(), NumberRange(min=0.01, max=9999999.99)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    programming_languages = StringField('Programming Languages', validators=[Length(max=500)], 
                                      description='Comma-separated list (e.g., Python, JavaScript, Go)')
    framework = StringField('Framework/Technology', validators=[Length(max=100)])
    license_type = SelectField('License Type', choices=[
        ('MIT', 'MIT License'),
        ('GPL-3.0', 'GPL v3'),
        ('Apache-2.0', 'Apache 2.0'),
        ('BSD-3-Clause', 'BSD 3-Clause'),
        ('Commercial', 'Commercial License'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    version = StringField('Version', validators=[Length(max=20)])
    demo_url = StringField('Demo URL', validators=[Optional(), URL()])
    github_url = StringField('GitHub Repository', validators=[Optional(), URL()])
    documentation_url = StringField('Documentation URL', validators=[Optional(), URL()])
    thumbnail = FileField('Thumbnail Image', validators=[FileAllowed(['jpg', 'png', 'gif', 'webp'], 'Images only!')])

class ReviewForm(FlaskForm):
    rating = SelectField('Rating', choices=[(5, '5 Stars'), (4, '4 Stars'), (3, '3 Stars'), (2, '2 Stars'), (1, '1 Star')], 
                        coerce=int, validators=[DataRequired()])
    title = StringField('Review Title', validators=[Length(max=200)])
    comment = TextAreaField('Review Comment', validators=[Length(max=1000)])

class MessageForm(FlaskForm):
    recipient_id = HiddenField('Recipient', validators=[DataRequired()])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Message', validators=[DataRequired(), Length(max=2000)])
    conversation_id = HiddenField('Conversation ID')

class SearchForm(FlaskForm):
    query = StringField('Search Products')
    category = SelectField('Category', coerce=int)
    language = SelectField('Programming Language')
    min_price = DecimalField('Min Price', validators=[Optional(), NumberRange(min=0)])
    max_price = DecimalField('Max Price', validators=[Optional(), NumberRange(min=0)])
    sort_by = SelectField('Sort By', choices=[
        ('newest', 'Newest First'),
        ('oldest', 'Oldest First'),
        ('price_low', 'Price: Low to High'),
        ('price_high', 'Price: High to Low'),
        ('rating', 'Highest Rated'),
        ('popular', 'Most Popular')
    ], default='newest')


# Collaborative Platform Forms

class TeamForm(FlaskForm):
    name = StringField('Team Name', validators=[DataRequired(), Length(min=3, max=200)])
    description = TextAreaField('Description', validators=[Length(max=1000)])
    avatar_url = URLField('Team Avatar URL', validators=[Optional(), URL()])
    is_public = BooleanField('Public Team', default=True)
    max_members = SelectField('Maximum Members', choices=[(5, '5'), (10, '10'), (20, '20'), (50, '50')], 
                             coerce=int, default=10, validators=[DataRequired()])
    submit = SubmitField('Create Team')


class ProjectForm(FlaskForm):
    name = StringField('Project Name', validators=[DataRequired(), Length(min=3, max=200)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10, max=2000)])
    requirements = TextAreaField('Requirements & Goals', validators=[Length(max=3000)])
    team_id = SelectField('Team', coerce=int, validators=[DataRequired()])
    
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'), 
        ('high', 'High'),
        ('critical', 'Critical')
    ], default='medium', validators=[DataRequired()])
    
    budget = DecimalField('Budget (USD)', validators=[Optional(), NumberRange(min=0)])
    payment_model = SelectField('Payment Model', choices=[
        ('milestone', 'Milestone-based'),
        ('hourly', 'Hourly Rate'),
        ('fixed', 'Fixed Price'),
        ('equity', 'Equity Share')
    ], default='milestone', validators=[DataRequired()])
    
    start_date = DateTimeLocalField('Start Date', validators=[Optional()])
    due_date = DateTimeLocalField('Due Date', validators=[Optional()])
    
    is_public = BooleanField('Public Project', default=False)
    tags = StringField('Tags', validators=[Length(max=500)], 
                      description='Comma-separated tags (e.g., Python, React, AI)')
    
    submit = SubmitField('Create Project')


class RepositoryForm(FlaskForm):
    name = StringField('Repository Name', validators=[DataRequired(), Length(min=3, max=200)])
    description = TextAreaField('Description', validators=[Length(max=1000)])
    language = SelectField('Primary Language', choices=[
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('typescript', 'TypeScript'),
        ('java', 'Java'),
        ('cpp', 'C++'),
        ('csharp', 'C#'),
        ('go', 'Go'),
        ('rust', 'Rust'),
        ('php', 'PHP'),
        ('ruby', 'Ruby'),
        ('swift', 'Swift'),
        ('kotlin', 'Kotlin'),
        ('html', 'HTML'),
        ('css', 'CSS'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    visibility = SelectField('Visibility', choices=[
        ('private', 'Private'),
        ('team', 'Team Only'),
        ('public', 'Public')
    ], default='private', validators=[DataRequired()])
    
    submit = SubmitField('Create Repository')


class FileForm(FlaskForm):
    filename = StringField('File Name', validators=[DataRequired(), Length(min=1, max=500)])
    filepath = StringField('File Path', validators=[DataRequired(), Length(min=1, max=1000)])
    content = TextAreaField('File Content', validators=[DataRequired()])
    language = SelectField('Language', choices=[
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('typescript', 'TypeScript'),
        ('html', 'HTML'),
        ('css', 'CSS'),
        ('json', 'JSON'),
        ('markdown', 'Markdown'),
        ('text', 'Plain Text'),
        ('other', 'Other')
    ], default='text')
    
    submit = SubmitField('Save File')


class MilestoneForm(FlaskForm):
    title = StringField('Milestone Title', validators=[DataRequired(), Length(min=3, max=200)])
    description = TextAreaField('Description', validators=[Length(max=1000)])
    requirements = TextAreaField('Requirements', validators=[Length(max=2000)])
    payment_amount = DecimalField('Payment Amount (USD)', validators=[Optional(), NumberRange(min=0)])
    due_date = DateTimeLocalField('Due Date', validators=[Optional()])
    
    submit = SubmitField('Create Milestone')


class CollaborationSessionForm(FlaskForm):
    title = StringField('Session Title', validators=[DataRequired(), Length(min=3, max=200)])
    description = TextAreaField('Description', validators=[Length(max=1000)])
    
    session_type = SelectField('Session Type', choices=[
        ('coding', 'Coding Session'),
        ('review', 'Code Review'),
        ('planning', 'Planning Meeting'),
        ('discussion', 'Discussion')
    ], default='coding', validators=[DataRequired()])
    
    max_participants = SelectField('Max Participants', choices=[
        (2, '2'), (3, '3'), (5, '5'), (10, '10'), (20, '20')
    ], coerce=int, default=5, validators=[DataRequired()])
    
    scheduled_at = DateTimeLocalField('Scheduled Time', validators=[Optional()])
    
    submit = SubmitField('Create Session')


class JoinTeamForm(FlaskForm):
    submit = SubmitField('Join Team')


class PaymentForm(FlaskForm):
    recipient_id = SelectField('Recipient', coerce=str, validators=[DataRequired()])
    milestone_id = SelectField('Milestone', coerce=int, validators=[Optional()])
    amount = DecimalField('Amount (USD)', validators=[DataRequired(), NumberRange(min=0.01)])
    payment_type = SelectField('Payment Type', choices=[
        ('milestone', 'Milestone Payment'),
        ('bonus', 'Bonus Payment'),
        ('hourly', 'Hourly Payment'),
        ('final', 'Final Payment')
    ], default='milestone', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Length(max=500)])
    
    submit = SubmitField('Process Payment')
