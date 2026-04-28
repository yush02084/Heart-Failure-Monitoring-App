from flask import Blueprint

bp = Blueprint("watcher", __name__)

from app.watcher import routes  # noqa
