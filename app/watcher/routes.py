from flask import render_template, abort, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.watcher import bp
from app.watcher.services import get_dashboard_context, get_parent_detail_context
from app.extensions import db
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
