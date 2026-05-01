"""
メール通知ユーティリティ
- send_email: 1件のメール送信
- notify_watchers_email: 親の全watcherにメール送信
push_utils.notify_watchers_push と同じシグネチャで呼べるようにしている。
"""
import logging
from flask import current_app
from flask_mail import Message
from app.extensions import mail

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> bool:
    """1件のメール送信。MAIL_SERVER または MAIL_DEFAULT_SENDER 未設定ならスキップ。"""
    if not current_app.config.get("MAIL_SERVER") or not current_app.config.get("MAIL_DEFAULT_SENDER"):
        logger.info("[Email] MAIL未設定のためスキップ")
        return False
    try:
        msg = Message(subject=subject, recipients=[to], body=body)
        mail.send(msg)
        logger.info(f"[Email] 送信成功: {to}")
        return True
    except Exception as e:
        logger.error(f"[Email] 送信失敗 to={to}: {e}", exc_info=True)
        return False


def notify_watchers_email(parent_user_id: int, subject: str, body: str):
    """親に紐づく全watcherのうち、emailが登録されているユーザーに送信。"""
    from app.models import WatchRelationship
    from app.models.user import User

    rels = WatchRelationship.query.filter_by(
        parent_user_id=parent_user_id, status="active"
    ).all()
    watcher_ids = [r.watcher_user_id for r in rels]
    if not watcher_ids:
        return

    watchers = (
        User.query.filter(User.id.in_(watcher_ids))
        .filter(User.deleted_at.is_(None))
        .all()
    )
    for w in watchers:
        if w.email:
            send_email(w.email, subject, body)
