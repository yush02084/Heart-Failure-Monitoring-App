from flask import render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.auth import bp
from app.auth.forms import LoginForm, RegisterWatcherForm, RegisterParentForm
from app.extensions import db, bcrypt
from app.models import User, Invitation, WatchRelationship
from app.core.tz import now_jst


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(
            login_id=form.login_id.data
        ).filter(User.deleted_at.is_(None)).first()

        # ユーザー不在でもbcryptを走らせてタイミング攻撃を防ぐ
        if user is None:
            try:
                bcrypt.check_password_hash(
                    "$2b$12$invalidhashXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                    form.pin.data,
                )
            except Exception:
                pass
            flash("ログインIDまたはPIN/パスワードが間違っています。", "error")
            return render_template("auth/login.html", form=form)

        # ロックアウト確認
        if user.locked_until and user.locked_until > now_jst():
            flash("アカウントがロックされています。しばらく後にお試しください。", "error")
            return render_template("auth/login.html", form=form)

        # パスワード照合
        if bcrypt.check_password_hash(user.pin_hash, form.pin.data):
            user.failed_attempts = 0
            user.locked_until = None
            db.session.commit()
            login_user(user)
            return _redirect_by_role(user)
        else:
            from datetime import timedelta
            from flask import current_app
            user.failed_attempts = (user.failed_attempts or 0) + 1
            max_attempts = current_app.config.get("LOGIN_MAX_ATTEMPTS", 5)
            lock_minutes = current_app.config.get("LOGIN_LOCK_MINUTES", 15)
            if user.failed_attempts >= max_attempts * 2:
                user.locked_until = now_jst() + timedelta(hours=1)
            elif user.failed_attempts >= max_attempts:
                user.locked_until = now_jst() + timedelta(minutes=lock_minutes)
            db.session.commit()
            flash("ログインIDまたはPIN/パスワードが間違っています。", "error")

    return render_template("auth/login.html", form=form)


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@bp.route("/register/watcher/<token>", methods=["GET", "POST"])
def register_watcher(token):
    invitation = Invitation.query.filter_by(sharing_token=token).first()

    if not invitation or not invitation.is_valid():
        return render_template("auth/token_error.html"), 400

    parent = invitation.parent
    form = RegisterWatcherForm()
    form.token.data = token

    if form.validate_on_submit():
        # login_id 重複チェック（削除済みユーザーは除外）
        if User.query.filter_by(login_id=form.login_id.data).filter(User.deleted_at.is_(None)).first():
            flash("このログインIDはすでに使われています。", "error")
            return render_template("auth/register_watcher.html", form=form, parent_name=parent.name)

        # トランザクション
        pw_hash = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        watcher = User(
            login_id=form.login_id.data,
            pin_hash=pw_hash,
            role="watcher",
            name=form.name.data,
            email=form.email.data,
            phone_number=form.phone_number.data or None,
        )
        db.session.add(watcher)
        db.session.flush()  # watcher.id を取得

        rel = WatchRelationship(
            parent_user_id=invitation.parent_user_id,
            watcher_user_id=watcher.id,
            status="active",
            accepted_at=now_jst(),
        )
        db.session.add(rel)

        invitation.used_at = now_jst()
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("登録に失敗しました。しばらく後にお試しください。", "error")
            return render_template("auth/register_watcher.html", form=form, parent_name=parent.name, token=token)

        login_user(watcher)
        return redirect(url_for("watcher.dashboard"))

    return render_template("auth/register_watcher.html", form=form, parent_name=parent.name, token=token)


@bp.route("/register/parent", methods=["GET", "POST"])
def register_parent():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    form = RegisterParentForm()
    if form.validate_on_submit():
        if User.query.filter_by(login_id=form.login_id.data).filter(User.deleted_at.is_(None)).first():
            flash("このログインIDはすでに使われています。", "error")
            return render_template("auth/register_parent.html", form=form)

        pw_hash = bcrypt.generate_password_hash(form.pin.data).decode("utf-8")
        parent = User(
            login_id=form.login_id.data,
            pin_hash=pw_hash,
            role="parent",
            name=form.name.data,
            phone_number=form.phone_number.data or None,
            base_weight=float(form.base_weight.data),
            base_weight_updated_at=now_jst(),
        )
        db.session.add(parent)
        try:
            db.session.commit()
            login_user(parent)
            return redirect(url_for("parent.home"))
        except Exception:
            db.session.rollback()
            flash("登録に失敗しました。しばらく後にお試しください。", "error")

    return render_template("auth/register_parent.html", form=form)


def _redirect_by_role(user):
    if user.role == "parent":
        return redirect(url_for("parent.home"))
    return redirect(url_for("watcher.dashboard"))
