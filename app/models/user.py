from flask_login import UserMixin
from app.extensions import db
from app.core.tz import now_jst


class User(UserMixin, db.Model):
    __tablename__ = "Users"

    id = db.Column(db.Integer, primary_key=True)
    login_id = db.Column(db.Text, unique=True, nullable=False)
    pin_hash = db.Column(db.Text, nullable=False)
    role = db.Column(db.Text, nullable=False)  # 'parent' or 'watcher'
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text)
    phone_number = db.Column(db.Text)
    base_weight = db.Column(db.Float)
    base_weight_updated_at = db.Column(db.DateTime)
    failed_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=now_jst)
    updated_at = db.Column(db.DateTime, nullable=False, default=now_jst, onupdate=now_jst)
    deleted_at = db.Column(db.DateTime)

    # リレーション
    daily_records = db.relationship("DailyRecord", backref="parent", lazy="dynamic",
                                    foreign_keys="DailyRecord.parent_user_id")
    watch_as_parent = db.relationship("WatchRelationship", backref="parent",
                                      foreign_keys="WatchRelationship.parent_user_id")
    watch_as_watcher = db.relationship("WatchRelationship", backref="watcher",
                                       foreign_keys="WatchRelationship.watcher_user_id")

    def get_id(self):
        return str(self.id)

    def is_parent(self):
        return self.role == "parent"

    def is_watcher(self):
        return self.role == "watcher"
