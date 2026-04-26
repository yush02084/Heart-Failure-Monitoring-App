"""
デモデータ投入スクリプト
起動時にDBが空の場合、自動的に実行される。
"""
from datetime import date, timedelta, datetime, timezone, timedelta as td
import secrets

JST = timezone(td(hours=9))


def seed():
    from app.extensions import db, bcrypt
    from app.models.user import User
    from app.models.watch_relationship import WatchRelationship
    from app.models.invitation import Invitation
    from app.models.daily_record import DailyRecord
    from app.core.alert_logic import calc_alert_level, ALERT_LOGIC_VERSION

    now = datetime.now(JST)
    today = now.date()

    # ── 親ユーザー ──
    parent = User(
        login_id="parent01",
        pin_hash=bcrypt.generate_password_hash("1234").decode("utf-8"),
        role="parent",
        name="山田太郎",
        phone_number="+819012345678",
        base_weight=65.0,
        base_weight_updated_at=now,
    )
    db.session.add(parent)

    # ── 子ユーザー ──
    watcher = User(
        login_id="watcher01",
        pin_hash=bcrypt.generate_password_hash("password1").decode("utf-8"),
        role="watcher",
        name="山田花子",
        email="hanako@example.com",
        phone_number="+819087654321",
    )
    db.session.add(watcher)
    db.session.flush()

    # ── 見守り関係 ──
    rel = WatchRelationship(
        parent_user_id=parent.id,
        watcher_user_id=watcher.id,
        status="active",
        invited_at=now,
        accepted_at=now,
    )
    db.session.add(rel)

    # ── 招待トークン（テスト用） ──
    inv = Invitation(
        parent_user_id=parent.id,
        sharing_token="demo-token",
        expires_at=now + td(days=30),
    )
    db.session.add(inv)

    # ── 過去7日分のレコード（警戒シナリオ含む） ──
    demo_records = [
        # (日前, 体重, 息切れ)
        (0, 67.2, 3),  # 今日: 警戒（+2.2kg、息切れあり）
        (1, 66.8, 2),  # 昨日: 注意
        (2, 66.1, 1),  # 2日前: 通常
        (3, 65.5, 1),  # 3日前: 通常（基準日）
        (4, 65.2, 1),  # 4日前: 通常
        (5, 65.0, 1),  # 5日前: 通常
        (6, 64.8, 1),  # 6日前: 通常
    ]

    for days_ago, weight, breath in demo_records:
        rec_date = today - timedelta(days=days_ago)
        # 3日前のレコードを基準体重として使う
        ref = None
        for d, w, _ in demo_records:
            if d == days_ago + 3:
                ref = w
                break
        if ref is None:
            ref = parent.base_weight
        level = calc_alert_level(weight, breath, ref)

        record = DailyRecord(
            parent_user_id=parent.id,
            record_date=rec_date,
            weight=weight,
            breath_condition=breath,
            alert_level=level,
            alert_logic_version=ALERT_LOGIC_VERSION,
        )
        db.session.add(record)

    db.session.commit()
    print("[seed] デモデータを投入しました")
    print("  親:  login_id=parent01   PIN=1234")
    print("  子:  login_id=watcher01  password=password1")
    print("  招待トークン: demo-token (30日有効)")
