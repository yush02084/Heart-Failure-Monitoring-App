from flask import render_template, abort
from flask_login import login_required, current_user
from app.watcher import bp
from app.watcher.services import get_dashboard_context, get_parent_detail_context


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
