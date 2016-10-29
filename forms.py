from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, TextAreaField, validators, PasswordField
from wtforms.validators import Required

class CatalogForm(Form):
    name = StringField('Name:',validators=[Required()])
    submit = SubmitField('Submit')

class ItemForm(Form):
    name = StringField('Name:', validators=[Required()])
    description = TextAreaField('Description:')
    price = StringField('Price:',validators=[Required()])
    submit = SubmitField('Submit')

class SignupForm(Form):
    name = StringField('Name:', [validators.DataRequired()])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email Address', [validators.Length(min=6, max=35)])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
    submit = SubmitField('Sign Up')

class LoginForm(Form):
    username = StringField('User Name:', [validators.DataRequired()])
    password = PasswordField('password', [validators.DataRequired()])
    submit = SubmitField('Login')
