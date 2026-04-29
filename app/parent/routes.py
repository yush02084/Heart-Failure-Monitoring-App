import secrets
from datetime import timedelta
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.parent import bp
from app.parent.forms import DailyInputForm
from app.extensions import db
from app.models import DailyRecord, Invitation
from app.core.tz import now_jst, today_jst
from app.core.alert_logic import calc_alert_level, ALERT_LOGIC_VERSION


@bp.route("/home")
@login_required
def home():
    if not current_user.is_parent():
        return redirect(url_for("watcher.dashboard"))

    today = today_jst()

    today_record = DailyRecord.query.filter_by(
        parent_user_id=current_user.id,
        record_date=today,
    ).filter(DailyRecord.deleted_at.is_(None)).first()

    # 今日未入力なら入力画面へ直接飛ばす
    if today_record is None:
        return redirect(url_for("parent.input"))

    recent_records = (
        DailyRecord.query
        .filter_by(parent_user_id=current_user.id)
        .filter(DailyRecord.deleted_at.is_(None))
        .order_by(DailyRecord.record_date.desc())
        .limit(7)
        .all()
    )

    recent_dicts = [r.to_dict(base_weight=current_user.base_weight) for r in recent_records]

    return render_template(
        "parent/home.html",
        user={"id": current_user.id, "name": current_user.name},
        today_record=today_record.to_dict(current_user.base_weight) if today_record else None,
        recent_records=recent_dicts,
    )


@bp.route("/input", methods=["GET", "POST"])
@login_required
def input():
    if not current_user.is_parent():
        return redirect(url_for("watcher.dashboard"))

    form = DailyInputForm()
    today = today_jst()

    # 既存レコード（今日分）があれば pre-fill
    existing = DailyRecord.query.filter_by(
        parent_user_id=current_user.id,
        record_date=today,
    ).filter(DailyRecord.deleted_at.is_(None)).first()

    if form.validate_on_submit():
        weight = form.weight.data
        breath = form.breath_condition.data

        # アラートレベル算出（base_weight を基準に使用）
        ref_weight = current_user.base_weight or weight
        alert_level = calc_alert_level(weight, breath, ref_weight)

        if existing:
            existing.weight = weight
            existing.breath_condition = breath
            existing.alert_level = alert_level
            existing.alert_logic_version = ALERT_LOGIC_VERSION
            existing.updated_at = now_jst()
        else:
            record = DailyRecord(
                parent_user_id=current_user.id,
                record_date=today,
                weight=weight,
                breath_condition=breath,
                alert_level=alert_level,
                alert_logic_version=ALERT_LOGIC_VERSION,
            )
            db.session.add(record)

        try:
            db.session.commit()
            flash("記録を保存しました。", "success")
            return redirect(url_for("parent.home"))
        except Exception:
            db.session.rollback()
            flash("保存に失敗しました。しばらく後にお試しください。", "error")

    # GET 時: 既存データがあれば pre-fill
    if request.method == "GET" and existing:
        form.weight.data = existing.weight
        form.breath_condition.data = existing.breath_condition

    return render_template(
        "parent/input.html",
        form=form,
        today_str=f"{today.year}年{today.month:02d}月{today.day:02d}日（{'月火水木金土日'[today.weekday()]}）",
        existing=existing is not None,
    )


@bp.route("/invite", methods=["POST"])
@login_required
def invite():
    if not current_user.is_parent():
        return jsonify({"error": "forbidden"}), 403

    # 未使用の有効なトークンがあれば再利用
    existing = (
        Invitation.query
        .filter_by(parent_user_id=current_user.id)
        .filter(Invitation.used_at.is_(None))
        .filter(Invitation.expires_at > now_jst())
        .first()
    )
    if existing:
        invite_url = url_for("auth.register_watcher", token=existing.sharing_token, _external=True)
        return jsonify({"url": invite_url})

    token = secrets.token_urlsafe(32)
    inv = Invitation(
        parent_user_id=current_user.id,
        sharing_token=token,
        expires_at=now_jst() + timedelta(minutes=30),
    )
    db.session.add(inv)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "生成に失敗しました"}), 500

    invite_url = url_for("auth.register_watcher", token=token, _external=True)
    return jsonify({"url": invite_url})
