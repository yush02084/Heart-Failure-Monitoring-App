"""
プッシュ通知ユーティリティ
- send_push: 1件のサブスクリプションに送信
- notify_watchers_push: 親の全watcherに一括送信
- check_and_notify_unrecorded: 毎朝7時に未記録チェック
"""
import json
import logging
from flask import current_app
from pywebpush import webpush, WebPushException

logger = logging.getLogger(__name__)


def _get_vapid():
    """PEM文字列からVapidオブジェクトを生成。
    pywebpush 2.x はPEM文字列を直接受け付けないため、cryptographyで読み込んでから
    Vapidのプライベート属性に直接セットする（公開APIが存在しないための暫定対応）。
    pywebpush のバージョンアップ時はこの箇所を要確認。
    """
    from py_vapid import Vapid
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    pem = current_app.config["VAPID_PRIVATE_KEY"]
    if isinstance(pem, str):
        pem = pem.encode("utf-8")
    private_key = load_pem_private_key(pem, password=None)
    v = Vapid()
    v._private_key = private_key  # pywebpush に公開APIがないため直接セット
    v._public_key = private_key.public_key()
    return v


def send_push(endpoint: str, p256dh: str, auth: str, title: str, body: str, url: str = "/watcher/dashboard"):
    """1件のサブスクリプションにプッシュ通知を送る"""
    if not current_app.config.get("VAPID_PRIVATE_KEY"):
        logger.warning("[Push] VAPID_PRIVATE_KEY未設定のためスキップ")
        return "error"
    try:
        logger.info(f"[Push] 送信開始: {endpoint[:60]}...")
        vapid = _get_vapid()
        webpush(
            subscription_info={
                "endpoint": endpoint,
                "keys": {"p256dh": p256dh, "auth": auth},
            },
            data=json.dumps({"title": title, "body": body, "url": url}),
            vapid_private_key=vapid,
            vapid_claims=current_app.config["VAPID_CLAIMS"],
        )
        logger.info("[Push] 送信成功")
        return "ok"
    except WebPushException as e:
        logger.error(f"[Push] 送信失敗: {e} / response: {e.response.text if e.response else 'none'}")
        if e.response and e.response.status_code == 410:
            return "gone"
        return "error"
    except Exception as e:
        logger.error(f"[Push] 予期しないエラー: {e}", exc_info=True)
        return "error"


def notify_watchers_push(parent_user_id: int, title: str, body: str):
    """親に紐づく全watcherのサブスクリプションに一括送信"""
    from app.extensions import db
    from app.models import WatchRelationship, PushSubscription

    rels = WatchRelationship.query.filter_by(
        parent_user_id=parent_user_id, status="active"
    ).all()
    watcher_ids = [r.watcher_user_id for r in rels]
    if not watcher_ids:
        return

    subs = PushSubscription.query.filter(
        PushSubscription.user_id.in_(watcher_ids)
    ).all()

    gone_ids = []
    for sub in subs:
        result = send_push(sub.endpoint, sub.p256dh, sub.auth, title, body)
        if result == "gone":
            gone_ids.append(sub.id)

    if gone_ids:
        PushSubscription.query.filter(PushSubscription.id.in_(gone_ids)).delete(synchronize_session=False)
        db.session.commit()


def check_and_notify_unrecorded():
    """毎朝7時JSTに実行: 2日以上未記録の親がいるwatcherに通知
    Flask-APSchedulerがapp_contextを自動でpushするため、current_appが使える。
    """
    from app.extensions import db
    from app.models import WatchRelationship, DailyRecord, PushSubscription
    from app.models.user import User
    from app.core.tz import today_jst
    from sqlalchemy import func

    today = today_jst()

    # 全アクティブな見守り関係を取得
    rels = WatchRelationship.query.filter_by(status="active").all()
    if not rels:
        return

    # 最終記録日を一括取得
    parent_ids = list({r.parent_user_id for r in rels})
    latest_map = {}
    if parent_ids:
        rows = (
            db.session.query(
                DailyRecord.parent_user_id,
                func.max(DailyRecord.record_date).label("max_date"),
            )
            .filter(DailyRecord.parent_user_id.in_(parent_ids))
            .filter(DailyRecord.deleted_at.is_(None))
            .group_by(DailyRecord.parent_user_id)
            .all()
        )
        latest_map = {r.parent_user_id: r.max_date for r in rows}

    # 親を一括取得（N+1回避）
    parent_map = {u.id: u for u in User.query.filter(User.id.in_(parent_ids)).all()}

    # watcherごとに未記録の親をまとめる
    watcher_alerts: dict[int, list[str]] = {}
    for rel in rels:
        last_date = latest_map.get(rel.parent_user_id)
        days = None if last_date is None else (today - last_date).days

        if days is None or days >= 2:
            parent = parent_map.get(rel.parent_user_id)
            if parent:
                watcher_alerts.setdefault(rel.watcher_user_id, []).append(parent.name)

    # 通知送信
    gone_ids_all = []
    for watcher_id, names in watcher_alerts.items():
        subs = PushSubscription.query.filter_by(user_id=watcher_id).all()
        if not subs:
            continue
        body = "、".join(names) + "さんの記録が届いていません"
        for sub in subs:
            result = send_push(
                sub.endpoint, sub.p256dh, sub.auth,
                title="📅 記録が届いていません",
                body=body,
                url="/watcher/notifications",
            )
            if result == "gone":
                gone_ids_all.append(sub.id)

    if gone_ids_all:
        PushSubscription.query.filter(PushSubscription.id.in_(gone_ids_all)).delete(synchronize_session=False)
        db.session.commit()
