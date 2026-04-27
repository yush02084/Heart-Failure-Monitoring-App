from flask_wtf import FlaskForm
from wtforms import FloatField, RadioField
from wtforms.validators import DataRequired, NumberRange


class DailyInputForm(FlaskForm):
    weight = FloatField(
        "体重（kg）",
        validators=[DataRequired(), NumberRange(min=20.0, max=300.0, message="20〜300kgの範囲で入力してください")]
    )
    breath_condition = RadioField(
        "息切れの状態",
        choices=[
            ("1", "普通"),
            ("2", "ちょっと苦しい"),
            ("3", "けっこう苦しい"),
            ("4", "とても苦しい"),
        ],
        validators=[DataRequired()],
        coerce=int,
    )
