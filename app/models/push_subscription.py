from app.extensions import db
from app.core.tz import now_jst


class PushSubscription(db.Model):
    __tablename__ = "Push_Subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.id"), nullable=False)
    endpoint = db.Column(db.Text, unique=True, nullable=False)
    p256dh = db.Column(db.Text, nullable=False)
    auth = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=now_jst)

    user = db.relationship("User", backref=db.backref("push_subscriptions", lazy="dynamic"))
