from app.extensions import db
from app.core.tz import now_jst
from app.core.alert_logic import ALERT_EMOJI, ALERT_LABEL, ALERT_COLOR_CLASS, BREATH_LABEL


class DailyRecord(db.Model):
    __tablename__ = "Daily_Records"

    id = db.Column(db.Integer, primary_key=True)
    parent_user_id = db.Column(db.Integer, db.ForeignKey("Users.id"), nullable=False)
    record_date = db.Column(db.Date, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    breath_condition = db.Column(db.Integer, nullable=False)  # 1〜4
    alert_level = db.Column(db.Integer, nullable=False)        # 0〜3
    alert_logic_version = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, nullable=False, default=now_jst)
    updated_at = db.Column(db.DateTime, nullable=False, default=now_jst, onupdate=now_jst)
    deleted_at = db.Column(db.DateTime)

    __table_args__ = (
        db.UniqueConstraint("parent_user_id", "record_date"),
        db.Index("ix_dr_parent_user_id", "parent_user_id"),
        db.Index("ix_dr_record_date", "record_date"),
    )

    def to_dict(self, base_weight: float = None):
        weight_diff = None
        weight_diff_str = "—"
        if base_weight is not None:
            diff = self.weight - base_weight
            weight_diff = round(diff, 1)
            weight_diff_str = f"+{weight_diff}" if diff >= 0 else str(weight_diff)

        record_dt = self.record_date
        date_str = f"{record_dt.year}年{record_dt.month:02d}月{record_dt.day:02d}日"

        level = self.alert_level if self.alert_level in ALERT_EMOJI else 0
        return {
            "id": self.id,
            "date_str": date_str,
            "date_iso": record_dt.isoformat(),
            "weight": self.weight,
            "weight_diff": weight_diff,       # float or None
            "weight_diff_str": weight_diff_str,
            "breath_condition": self.breath_condition,
            "breath_label": BREATH_LABEL.get(self.breath_condition, "—"),
            "alert_level": level,
            "alert_emoji": ALERT_EMOJI[level],
            "alert_color_class": ALERT_COLOR_CLASS[level],
            "alert_label": ALERT_LABEL[level],
        }
