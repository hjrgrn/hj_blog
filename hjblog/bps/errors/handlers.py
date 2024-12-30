from flask import g, render_template, Blueprint

from hjblog.bps.user_profile.auxiliaries import get_profile_pic

"""
Error handlers
"""

bp = Blueprint("errors", __name__)


@bp.app_errorhandler(404)
def error_404(__error__):
    user = g.get("user", None)
    profile_pic = None
    if user is not None:
        profile_pic = get_profile_pic(user["profile_pic"])
    return (
        render_template("errors/404.html", current_user=user, profile_pic=profile_pic),
        404,
    )


@bp.app_errorhandler(403)
def error_403(__error__):
    user = g.get("user", None)
    profile_pic = None
    if user is not None:
        profile_pic = get_profile_pic(user["profile_pic"])
    return (
        render_template("errors/403.html", current_user=user, profile_pic=profile_pic),
        403,
    )


@bp.app_errorhandler(500)
def error_500(__error__):
    user = g.get("user", None)
    profile_pic = None
    if user is not None:
        profile_pic = get_profile_pic(user["profile_pic"])
    return (
        render_template("errors/500.html", current_user=user, profile_pic=profile_pic),
        500,
    )
