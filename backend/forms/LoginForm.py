from flask_wtf import FlaskForm # type: ignore
from wtforms import StringField, PasswordField, BooleanField # type: ignore
from wtforms.validators import DataRequired # type: ignore

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
