from flask import render_template, Blueprint

"""
Error handlers
"""

bp = Blueprint('errors', __name__)


@bp.app_errorhandler(404)
def error_404(__error__):
    return render_template('errors/404.html'), 404



@bp.app_errorhandler(403)
def error_403(__error__):
    return render_template('errors/403.html'), 403




@bp.app_errorhandler(500)
def error_500(__error__):
    return render_template('errors/500.html'), 500
