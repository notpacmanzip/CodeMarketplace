from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SelectField, HiddenField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Length, URL, Optional, NumberRange
from wtforms.widgets import TextArea

class CodeSubmissionForm(FlaskForm):
    title = StringField('Project Title', validators=[DataRequired(), Length(min=5, max=200)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=20, max=2000)],
                               description='Describe your code and what specific feedback you\'re looking for')
    
    review_type = SelectField('Review Type', choices=[
        ('general', 'General Code Review'),
        ('performance', 'Performance Optimization'),
        ('security', 'Security Audit'),
        ('best_practices', 'Best Practices & Clean Code'),
        ('architecture', 'Architecture Review'),
        ('testing', 'Testing & Quality Assurance')
    ], validators=[DataRequired()])
    
    programming_language = SelectField('Primary Language', choices=[
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
        ('scala', 'Scala'),
        ('dart', 'Dart'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    framework = StringField('Framework/Technology', validators=[Length(max=100)],
                           description='e.g., React, Django, Spring Boot, etc.')
    
    submission_type = SelectField('Submission Method', choices=[
        ('file_upload', 'Upload Files (.zip, .tar.gz)'),
        ('repository_url', 'Repository URL (GitHub/GitLab)')
    ], validators=[DataRequired()])
    
    # File upload field
    code_file = FileField('Code Files', 
                         validators=[FileAllowed(['zip', 'tar', 'gz'], 'Only .zip and .tar.gz files allowed')])
    
    # Repository URL field
    repository_url = StringField('Repository URL', validators=[Optional(), URL()],
                                description='GitHub or GitLab repository URL')
    
    priority = SelectField('Priority', choices=[
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='normal')
    
    estimated_review_time = SelectField('Expected Review Time', choices=[
        ('2', '2-4 hours'),
        ('8', '1 day'),
        ('24', '2-3 days'),
        ('72', '1 week')
    ], coerce=int, default=24)

class ReviewerProfileForm(FlaskForm):
    bio = TextAreaField('Professional Bio', validators=[DataRequired(), Length(min=50, max=1000)])
    
    specializations = StringField('Specializations', validators=[DataRequired(), Length(max=500)],
                                 description='Comma-separated (e.g., Web Development, API Design, DevOps)')
    
    programming_languages = StringField('Programming Languages', validators=[DataRequired(), Length(max=300)],
                                       description='Comma-separated (e.g., Python, JavaScript, Java)')
    
    frameworks = StringField('Frameworks & Technologies', validators=[Length(max=500)],
                            description='Comma-separated (e.g., React, Django, Docker)')
    
    years_experience = IntegerField('Years of Experience', validators=[DataRequired(), NumberRange(min=1, max=50)])
    
    max_concurrent_reviews = SelectField('Max Concurrent Reviews', choices=[
        (1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')
    ], coerce=int, default=3)
    
    preferred_review_types = StringField('Preferred Review Types', validators=[Length(max=300)],
                                       description='Comma-separated from: general, performance, security, best_practices, architecture, testing')
    
    portfolio_url = StringField('Portfolio URL', validators=[Optional(), URL()])
    linkedin_url = StringField('LinkedIn URL', validators=[Optional(), URL()])
    github_url = StringField('GitHub URL', validators=[Optional(), URL()])
    
    is_available = BooleanField('Available for Reviews', default=True)

class CodeReviewForm(FlaskForm):
    summary_feedback = TextAreaField('Summary Feedback', 
                                   validators=[DataRequired(), Length(min=100, max=5000)],
                                   widget=TextArea(),
                                   description='Overall assessment and key recommendations')
    
    performance_notes = TextAreaField('Performance Analysis', 
                                    validators=[Length(max=2000)],
                                    description='Performance optimizations and bottlenecks')
    
    security_notes = TextAreaField('Security Assessment', 
                                 validators=[Length(max=2000)],
                                 description='Security vulnerabilities and recommendations')
    
    best_practices_notes = TextAreaField('Best Practices', 
                                       validators=[Length(max=2000)],
                                       description='Code quality and best practice improvements')
    
    # Ratings (1-5 scale)
    code_quality_rating = SelectField('Code Quality', choices=[
        (1, '1 - Needs Major Improvement'),
        (2, '2 - Below Average'),
        (3, '3 - Average'),
        (4, '4 - Good'),
        (5, '5 - Excellent')
    ], coerce=int, validators=[DataRequired()])
    
    security_rating = SelectField('Security', choices=[
        (1, '1 - Critical Issues'),
        (2, '2 - Security Concerns'),
        (3, '3 - Basic Security'),
        (4, '4 - Good Security'),
        (5, '5 - Excellent Security')
    ], coerce=int, validators=[DataRequired()])
    
    performance_rating = SelectField('Performance', choices=[
        (1, '1 - Poor Performance'),
        (2, '2 - Below Average'),
        (3, '3 - Average Performance'),
        (4, '4 - Good Performance'),
        (5, '5 - Excellent Performance')
    ], coerce=int, validators=[DataRequired()])
    
    maintainability_rating = SelectField('Maintainability', choices=[
        (1, '1 - Hard to Maintain'),
        (2, '2 - Below Average'),
        (3, '3 - Average'),
        (4, '4 - Easy to Maintain'),
        (5, '5 - Very Maintainable')
    ], coerce=int, validators=[DataRequired()])
    
    complexity_assessment = SelectField('Code Complexity', choices=[
        ('low', 'Low Complexity'),
        ('medium', 'Medium Complexity'),
        ('high', 'High Complexity')
    ], validators=[DataRequired()])
    
    time_spent = IntegerField('Time Spent (minutes)', validators=[DataRequired(), NumberRange(min=30, max=2000)])
    
    # File uploads for reports and fixed code
    report_file = FileField('Review Report', 
                           validators=[FileAllowed(['pdf', 'doc', 'docx', 'txt'], 'Document files only')])
    
    fixed_code_file = FileField('Fixed/Improved Code', 
                               validators=[FileAllowed(['zip', 'tar', 'gz'], 'Archive files only')])

class ReviewCommentForm(FlaskForm):
    file_path = StringField('File Path', validators=[DataRequired(), Length(max=500)])
    line_number = IntegerField('Line Number', validators=[Optional(), NumberRange(min=1)])
    
    comment_text = TextAreaField('Comment', validators=[DataRequired(), Length(min=10, max=1000)])
    
    comment_type = SelectField('Comment Type', choices=[
        ('suggestion', 'Suggestion'),
        ('issue', 'Issue/Problem'),
        ('question', 'Question'),
        ('compliment', 'Positive Feedback')
    ], validators=[DataRequired()])
    
    severity = SelectField('Severity', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], default='medium')
    
    original_code = TextAreaField('Original Code', validators=[Length(max=2000)])
    suggested_code = TextAreaField('Suggested Code', validators=[Length(max=2000)])
    
    submission_id = HiddenField('Submission ID', validators=[DataRequired()])

class ReviewRatingForm(FlaskForm):
    overall_rating = SelectField('Overall Rating', choices=[
        (1, '1 Star - Poor'),
        (2, '2 Stars - Below Average'),
        (3, '3 Stars - Average'),
        (4, '4 Stars - Good'),
        (5, '5 Stars - Excellent')
    ], coerce=int, validators=[DataRequired()])
    
    helpfulness_rating = SelectField('Helpfulness', choices=[
        (1, '1 - Not Helpful'),
        (2, '2 - Slightly Helpful'),
        (3, '3 - Moderately Helpful'),
        (4, '4 - Very Helpful'),
        (5, '5 - Extremely Helpful')
    ], coerce=int, validators=[DataRequired()])
    
    communication_rating = SelectField('Communication', choices=[
        (1, '1 - Poor Communication'),
        (2, '2 - Below Average'),
        (3, '3 - Average'),
        (4, '4 - Good Communication'),
        (5, '5 - Excellent Communication')
    ], coerce=int, validators=[DataRequired()])
    
    timeliness_rating = SelectField('Timeliness', choices=[
        (1, '1 - Very Late'),
        (2, '2 - Late'),
        (3, '3 - On Time'),
        (4, '4 - Ahead of Schedule'),
        (5, '5 - Very Fast')
    ], coerce=int, validators=[DataRequired()])
    
    feedback_text = TextAreaField('Written Feedback', validators=[Length(max=1000)],
                                 description='Optional detailed feedback about the review')
    
    would_recommend = BooleanField('Would you recommend this reviewer?', default=True)

class ReviewerSearchForm(FlaskForm):
    specialization = SelectField('Specialization', choices=[
        ('', 'Any Specialization'),
        ('web_development', 'Web Development'),
        ('mobile_development', 'Mobile Development'),
        ('backend_development', 'Backend Development'),
        ('frontend_development', 'Frontend Development'),
        ('devops', 'DevOps'),
        ('data_science', 'Data Science'),
        ('machine_learning', 'Machine Learning'),
        ('security', 'Security'),
        ('performance', 'Performance'),
        ('architecture', 'Architecture')
    ])
    
    programming_language = SelectField('Programming Language', choices=[
        ('', 'Any Language'),
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('java', 'Java'),
        ('cpp', 'C++'),
        ('csharp', 'C#'),
        ('go', 'Go'),
        ('rust', 'Rust'),
        ('php', 'PHP'),
        ('ruby', 'Ruby')
    ])
    
    min_rating = SelectField('Minimum Rating', choices=[
        ('', 'Any Rating'),
        ('3.0', '3+ Stars'),
        ('4.0', '4+ Stars'),
        ('4.5', '4.5+ Stars')
    ])
    
    availability = SelectField('Availability', choices=[
        ('', 'Any'),
        ('available', 'Available Now'),
        ('verified', 'Verified Only')
    ])