from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, DecimalField, BooleanField, IntegerField, HiddenField
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
