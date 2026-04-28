from sqlalchemy.orm import joinedload
from app.extensions import db
from app.models import User, WatchRelationship, DailyRecord
from app.core.tz import today_jst
from app.core.alert_logic import ALERT_EMOJI, ALERT_LABEL, ALERT_COLOR_CLASS


def get_dashboard_context(watcher: User) -> dict:
    """watcherダッシュボード用データを組み立てる"""
    rels = (
        WatchRelationship.query
        .filter_by(watcher_user_id=watcher.id, status="active")
        .join(WatchRelationship.parent)
        .filter(User.deleted_at.is_(None))
        .options(joinedload(WatchRelationship.parent))
        .all()
    )

    # 監視対象の親IDリストを一括取得してN+1を回避
    parent_ids = [rel.parent_user_id for rel in rels]
    latest_map: dict[int, DailyRecord] = {}
    if parent_ids:
        # 各親の最新レコードをサブクエリで一括取得
        from sqlalchemy import func
        subq = (
            db.session.query(
                DailyRecord.parent_user_id,
                func.max(DailyRecord.record_date).label("max_date"),
            )
            .filter(DailyRecord.parent_user_id.in_(parent_ids))
            .filter(DailyRecord.deleted_at.is_(None))
            .group_by(DailyRecord.parent_user_id)
            .subquery()
        )
        latest_records = (
            db.session.query(DailyRecord)
            .join(subq, (DailyRecord.parent_user_id == subq.c.parent_user_id)
                  & (DailyRecord.record_date == subq.c.max_date))
            .all()
        )
        latest_map = {r.parent_user_id: r for r in latest_records}

    watched_parents = []
    today = today_jst()

    for rel in rels:
        parent = rel.parent
        latest = latest_map.get(parent.id)

        if latest:
            days_since = (today - latest.record_date).days
            last_date_str = f"{latest.record_date.year}年{latest.record_date.month:02d}月{latest.record_date.day:02d}日"
            alert_level = latest.alert_level if days_since < 14 else 0
            rec_dict = latest.to_dict(base_weight=parent.base_weight)
        else:
            days_since = None
            last_date_str = "記録なし"
            alert_level = 0
            rec_dict = None

        watched_parents.append({
            "parent_id": parent.id,
            "parent_name": parent.name,
            "phone_number": parent.phone_number,
            "latest_record": rec_dict,
            "alert_level": alert_level,
            "alert_emoji": ALERT_EMOJI[alert_level],
            "alert_color_class": ALERT_COLOR_CLASS[alert_level],
            "alert_label": ALERT_LABEL[alert_level],
            "last_input_date_str": last_date_str,
            "days_since_last_input": days_since,
        })

    # 警戒→注意→通常の順でソート
    watched_parents.sort(key=lambda x: x["alert_level"], reverse=True)
    return {"user": _user_dict(watcher), "watched_parents": watched_parents}


def get_parent_detail_context(watcher: User, parent_id: int) -> dict | None:
    """親詳細ページ用データを組み立てる"""
    # アクセス権確認
    rel = WatchRelationship.query.filter_by(
        watcher_user_id=watcher.id,
        parent_user_id=parent_id,
        status="active",
    ).options(joinedload(WatchRelationship.parent)).first()
    if not rel:
        return None

    parent = rel.parent
    records = (
        DailyRecord.query
        .filter_by(parent_user_id=parent_id)
        .filter(DailyRecord.deleted_at.is_(None))
        .order_by(DailyRecord.record_date.desc())
        .limit(7)
        .all()
    )

    today = today_jst()
    latest = records[0] if records else None

    if latest and (today - latest.record_date).days < 14:
        alert_level = latest.alert_level
    else:
        alert_level = 0

    recent_records = [r.to_dict(base_weight=parent.base_weight) for r in records]

    phone = parent.phone_number or ""
    tel_link = f"tel:{phone}" if phone else "#"

    return {
        "parent": {
            "id": parent.id,
            "name": parent.name,
            "phone_number": phone,
            "tel_link": tel_link,
        },
        "today_alert": {
            "level": alert_level,
            "emoji": ALERT_EMOJI[alert_level],
            "color_class": ALERT_COLOR_CLASS[alert_level],
            "label": ALERT_LABEL[alert_level],
            "should_show_call_button": alert_level >= 2,
        },
        "recent_records": recent_records,
    }


def _user_dict(user: User) -> dict:
    return {"id": user.id, "name": user.name, "role": user.role}
