from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length

class ForumTopicForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=5, max=200)])
    content = TextAreaField('Content', validators=[DataRequired(), Length(min=10, max=5000)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    tags = StringField('Tags', validators=[Length(max=500)], 
                      description='Comma-separated tags (e.g., python, bug, help)')
    
    # Code snippet fields
    code_snippet = TextAreaField('Code Snippet', validators=[Length(max=10000)])
    code_language = SelectField('Code Language', choices=[
        ('', 'Select Language'),
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('java', 'Java'),
        ('cpp', 'C++'),
        ('c', 'C'),
        ('html', 'HTML'),
        ('css', 'CSS'),
        ('sql', 'SQL'),
        ('bash', 'Bash'),
        ('json', 'JSON'),
        ('xml', 'XML'),
        ('yaml', 'YAML'),
        ('markdown', 'Markdown'),
        ('other', 'Other')
    ])
    
    is_pinned = BooleanField('Pin this topic')
    submit = SubmitField('Create Topic')


class ForumReplyForm(FlaskForm):
    content = TextAreaField('Reply', validators=[DataRequired(), Length(min=5, max=3000)])
    
    # Code snippet fields
    code_snippet = TextAreaField('Code Snippet', validators=[Length(max=10000)])
    code_language = SelectField('Code Language', choices=[
        ('', 'Select Language'),
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('java', 'Java'),
        ('cpp', 'C++'),
        ('c', 'C'),
        ('html', 'HTML'),
        ('css', 'CSS'),
        ('sql', 'SQL'),
        ('bash', 'Bash'),
        ('json', 'JSON'),
        ('xml', 'XML'),
        ('yaml', 'YAML'),
        ('markdown', 'Markdown'),
        ('other', 'Other')
    ])
    
    reply_to_id = HiddenField()
    is_solution = BooleanField('Mark as solution')
    submit = SubmitField('Post Reply')


class ForumSearchForm(FlaskForm):
    query = StringField('Search')
    category_id = SelectField('Category', coerce=int)
    sort_by = SelectField('Sort By', choices=[
        ('newest', 'Newest'),
        ('oldest', 'Oldest'),
        ('most_replies', 'Most Replies'),
        ('most_views', 'Most Views'),
        ('solved', 'Solved First'),
        ('unsolved', 'Unsolved First')
    ], default='newest')
    
    submit = SubmitField('Search')