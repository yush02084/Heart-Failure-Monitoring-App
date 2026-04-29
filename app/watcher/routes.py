from flask import render_template, abort, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.watcher import bp
from app.watcher.services import get_dashboard_context, get_parent_detail_context
from app.auth.forms import WatcherSettingsForm
from app.extensions import db, bcrypt
from app.models import Invitation, WatchRelationship
from app.core.tz import now_jst


@bp.route("/dashboard")
@login_required
def dashboard():
    if not current_user.is_watcher():
        abort(403)
    ctx = get_dashboard_context(current_user)
    return render_template("watcher/dashboard.html", **ctx)


@bp.route("/parent/<int:parent_id>")
@login_required
def parent_detail(parent_id: int):
    if not current_user.is_watcher():
        abort(403)
    ctx = get_parent_detail_context(current_user, parent_id)
    if ctx is None:
        abort(404)
    return render_template("watcher/parent_detail.html", **ctx)


@bp.route("/join", methods=["GET", "POST"])
@login_required
def join():
    if not current_user.is_watcher():
        abort(403)

    if request.method == "POST":
        raw = request.form.get("token", "").strip()
        # URLから末尾トークンを抽出（URLごと貼り付けても動く）
        token = raw.split("/")[-1]

        inv = Invitation.query.filter_by(sharing_token=token).first()
        if not inv or not inv.is_valid():
            flash("招待リンクが無効または期限切れです。", "error")
            return render_template("watcher/join.html")

        # 既に見守り関係があるか確認
        existing = WatchRelationship.query.filter_by(
            watcher_user_id=current_user.id,
            parent_user_id=inv.parent_user_id,
        ).first()
        if existing:
            flash("すでにこの方を見守り登録しています。", "info")
            return redirect(url_for("watcher.dashboard"))

        rel = WatchRelationship(
            watcher_user_id=current_user.id,
            parent_user_id=inv.parent_user_id,
            status="active",
        )
        db.session.add(rel)
        inv.used_at = now_jst()
        try:
            db.session.commit()
            flash("見守り登録が完了しました。", "success")
            return redirect(url_for("watcher.dashboard"))
        except Exception:
            db.session.rollback()
            flash("登録に失敗しました。しばらく後にお試しください。", "error")

    return render_template("watcher/join.html")


@bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if not current_user.is_watcher():
        abort(403)

    relationships = (WatchRelationship.query
                     .filter_by(watcher_user_id=current_user.id, status="active")
                     .all())

    form = WatcherSettingsForm(obj=current_user)
    if form.validate_on_submit():
        if not bcrypt.check_password_hash(current_user.pin_hash, form.current_password.data):
            flash("現在のパスワードが正しくありません。", "error")
            return render_template("watcher/settings.html", form=form, relationships=relationships)

        if form.new_login_id.data:
            from app.models.user import User as _User
            dup = _User.query.filter_by(login_id=form.new_login_id.data)\
                             .filter(_User.deleted_at.is_(None))\
                             .filter(_User.id != current_user.id).first()
            if dup:
                flash("このログインIDはすでに使われています。", "error")
                return render_template("watcher/settings.html", form=form, relationships=relationships)
            current_user.login_id = form.new_login_id.data

        current_user.name = form.name.data
        current_user.phone_number = form.phone_number.data or None
        current_user.email = form.email.data or None
        current_user.updated_at = now_jst()

        if form.new_password.data:
            current_user.pin_hash = bcrypt.generate_password_hash(
                form.new_password.data).decode("utf-8")

        try:
            db.session.commit()
            flash("設定を保存しました。", "success")
            return redirect(url_for("watcher.settings"))
        except Exception:
            db.session.rollback()
            flash("保存に失敗しました。しばらく後にお試しください。", "error")

    return render_template("watcher/settings.html", form=form, relationships=relationships)


@bp.route("/unwatch/<int:parent_id>", methods=["POST"])
@login_required
def unwatch(parent_id):
    if not current_user.is_watcher():
        abort(403)
    rel = WatchRelationship.query.filter_by(
        watcher_user_id=current_user.id,
        parent_user_id=parent_id,
        status="active",
    ).first_or_404()
    rel.status = "inactive"
    db.session.commit()
    flash("見守りを解除しました。", "success")
    return redirect(url_for("watcher.settings"))


@bp.route("/notifications")
@login_required
def notifications():
    if not current_user.is_watcher():
        abort(403)
    ctx = get_dashboard_context(current_user)
    notifs = [
        p for p in ctx["watched_parents"]
        if p["alert_level"] >= 2
        or p["days_since_last_input"] is None
        or p["days_since_last_input"] >= 2
    ]
    return render_template("watcher/notifications.html", notifs=notifs, user=ctx["user"])
