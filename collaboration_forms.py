from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField, IntegerField, HiddenField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

class CodeRepositoryForm(FlaskForm):
    name = StringField('Repository Name', validators=[DataRequired(), Length(min=3, max=200)])
    description = TextAreaField('Description', validators=[Length(max=1000)])
    is_private = BooleanField('Private Repository', default=False)
    default_branch = StringField('Default Branch', validators=[Length(max=100)], default='main')
    submit = SubmitField('Create Repository')


class CodeFileForm(FlaskForm):
    filename = StringField('File Name', validators=[DataRequired(), Length(min=1, max=500)])
    file_path = StringField('File Path', validators=[DataRequired(), Length(min=1, max=1000)])
    content = TextAreaField('File Content', validators=[DataRequired()])
    language = SelectField('Programming Language', choices=[
        ('', 'Auto-detect'),
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('typescript', 'TypeScript'),
        ('java', 'Java'),
        ('cpp', 'C++'),
        ('c', 'C'),
        ('html', 'HTML'),
        ('css', 'CSS'),
        ('scss', 'SCSS'),
        ('sql', 'SQL'),
        ('bash', 'Bash/Shell'),
        ('json', 'JSON'),
        ('xml', 'XML'),
        ('yaml', 'YAML'),
        ('markdown', 'Markdown'),
        ('php', 'PHP'),
        ('ruby', 'Ruby'),
        ('go', 'Go'),
        ('rust', 'Rust'),
        ('swift', 'Swift'),
        ('kotlin', 'Kotlin'),
        ('other', 'Other')
    ])
    submit = SubmitField('Save File')


class CodeCommitForm(FlaskForm):
    message = TextAreaField('Commit Message', validators=[DataRequired(), Length(min=5, max=500)])
    branch = StringField('Branch', validators=[DataRequired(), Length(max=100)], default='main')
    changes_summary = TextAreaField('Changes Summary', validators=[Length(max=1000)])
    submit = SubmitField('Commit Changes')


class LiveCodingSessionForm(FlaskForm):
    session_name = StringField('Session Name', validators=[DataRequired(), Length(min=3, max=200)])
    max_participants = SelectField('Max Participants', choices=[
        (2, '2'), (5, '5'), (10, '10'), (20, '20'), (50, '50')
    ], coerce=int, default=10, validators=[DataRequired()])
    allow_anonymous = BooleanField('Allow Anonymous Users', default=False)
    submit = SubmitField('Start Session')


class CodeModuleForm(FlaskForm):
    name = StringField('Module Name', validators=[DataRequired(), Length(min=3, max=200)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10, max=1000)])
    module_type = SelectField('Module Type', choices=[
        ('function', 'Function'),
        ('class', 'Class'),
        ('component', 'Component'),
        ('snippet', 'Code Snippet'),
        ('library', 'Library'),
        ('utility', 'Utility')
    ], validators=[DataRequired()])
    
    code_content = TextAreaField('Code Content', validators=[DataRequired(), Length(min=10)])
    language = SelectField('Programming Language', choices=[
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('typescript', 'TypeScript'),
        ('java', 'Java'),
        ('cpp', 'C++'),
        ('c', 'C'),
        ('html', 'HTML'),
        ('css', 'CSS'),
        ('php', 'PHP'),
        ('ruby', 'Ruby'),
        ('go', 'Go'),
        ('rust', 'Rust'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    dependencies = TextAreaField('Dependencies', validators=[Length(max=1000)],
                                description='List any dependencies or requirements')
    tags = StringField('Tags', validators=[Length(max=500)],
                      description='Comma-separated tags for searchability')
    
    is_public = BooleanField('Make Public', default=True)
    is_reusable = BooleanField('Allow Reuse', default=True)
    
    submit = SubmitField('Save Module')


class ImportModuleForm(FlaskForm):
    module_id = HiddenField('Module ID', validators=[DataRequired()])
    import_to_project = SelectField('Import to Project', coerce=int, validators=[DataRequired()])
    custom_name = StringField('Custom Name', validators=[Length(max=200)])
    submit = SubmitField('Import Module')


class ExportModuleForm(FlaskForm):
    file_ids = HiddenField('File IDs')  # JSON array of file IDs to export
    module_name = StringField('Module Name', validators=[DataRequired(), Length(min=3, max=200)])
    description = TextAreaField('Description', validators=[Length(max=1000)])
    export_format = SelectField('Export Format', choices=[
        ('zip', 'ZIP Archive'),
        ('single', 'Single File'),
        ('module', 'Reusable Module')
    ], default='module', validators=[DataRequired()])
    submit = SubmitField('Export')