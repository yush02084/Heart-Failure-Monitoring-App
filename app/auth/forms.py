from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, HiddenField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional


class LoginForm(FlaskForm):
    login_id = StringField("ログインID", validators=[DataRequired(), Length(4, 20)])
    pin = PasswordField("PIN / パスワード", validators=[DataRequired()])


class RegisterWatcherForm(FlaskForm):
    login_id = StringField("ログインID", validators=[DataRequired(), Length(4, 20)])
    password = PasswordField("パスワード", validators=[DataRequired(), Length(8)])
    password_confirm = PasswordField(
        "パスワード（確認）",
        validators=[DataRequired(), EqualTo("password", message="パスワードが一致しません")]
    )
    name = StringField("お名前", validators=[DataRequired(), Length(1, 20)])
    email = StringField("メールアドレス", validators=[DataRequired(), Email()])
    phone_number = StringField("電話番号", validators=[Optional(), Length(max=20)])
    token = HiddenField()
