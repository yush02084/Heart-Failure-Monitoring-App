from app.extensions import db
from app.core.tz import now_jst


class WatchRelationship(db.Model):
    __tablename__ = "Watch_Relationships"

    id = db.Column(db.Integer, primary_key=True)
    parent_user_id = db.Column(db.Integer, db.ForeignKey("Users.id"), nullable=False)
    watcher_user_id = db.Column(db.Integer, db.ForeignKey("Users.id"), nullable=False)
    status = db.Column(db.Text, nullable=False, default="active")  # pending/active/revoked
    invited_at = db.Column(db.DateTime, nullable=False, default=now_jst)
    accepted_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=now_jst)
    updated_at = db.Column(db.DateTime, nullable=False, default=now_jst, onupdate=now_jst)

    __table_args__ = (
        db.UniqueConstraint("parent_user_id", "watcher_user_id"),
        db.Index("ix_wr_watcher_user_id", "watcher_user_id"),
        db.Index("ix_wr_parent_user_id", "parent_user_id"),
    )
