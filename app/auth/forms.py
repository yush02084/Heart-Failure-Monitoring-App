from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, HiddenField, DecimalField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, NumberRange


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


class RegisterParentForm(FlaskForm):
    login_id     = StringField("ログインID", validators=[DataRequired(), Length(4, 20)])
    pin          = PasswordField("PIN（4桁）", validators=[
                       DataRequired(), Length(4, 4, message="PINは4桁で入力してください")
                   ])
    pin_confirm  = PasswordField("PIN（確認）", validators=[
                       DataRequired(), EqualTo("pin", message="PINが一致しません")
                   ])
    name         = StringField("お名前", validators=[DataRequired(), Length(1, 20)])
    phone_number = StringField("電話番号", validators=[Optional(), Length(max=20)])
    base_weight  = DecimalField("基準体重（kg）", places=1, validators=[
                       DataRequired(message="基準体重を入力してください"),
                       NumberRange(min=20.0, max=300.0, message="20〜300kgの範囲で入力してください")
                   ])
