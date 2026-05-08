from flask_wtf import FlaskForm # type: ignore
from wtforms import StringField, PasswordField, BooleanField # type: ignore

class LoginForm(FlaskForm):
    username = StringField('Username')
    password = PasswordField('Password')
    remember = BooleanField('Remember Me')
