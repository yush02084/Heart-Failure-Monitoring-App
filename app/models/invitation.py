from app.extensions import db
from app.core.tz import now_jst


class Invitation(db.Model):
    __tablename__ = "Invitations"

    id = db.Column(db.Integer, primary_key=True)
    parent_user_id = db.Column(db.Integer, db.ForeignKey("Users.id"), nullable=False)
    sharing_token = db.Column(db.Text, unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=now_jst)

    parent = db.relationship("User", foreign_keys=[parent_user_id])

    def is_valid(self):
        return self.used_at is None and self.expires_at > now_jst()
