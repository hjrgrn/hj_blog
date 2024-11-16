from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_wtf.csrf import logging
from hjblog.bps.main.globals import MAX_PER_PAGE, PAGE_SPAN
from hjblog.bps.main.helpers import get_posts
from hjblog.bps.general_auxiliaries.auxiliaries import get_indexes, get_offset

from hjblog.db import get_db


bp = Blueprint("index", __name__)


@bp.route("/")
@bp.route("/index")
def index():
    """Home route"""

    db = get_db()

    posts = db.execute(
        "SELECT users.username, posts.id, posts.title, posts.content, posts.path_to_file, posts.posted FROM posts JOIN users ON (users.id = posts.author_id) ORDER BY posts.posted DESC, posts.id DESC LIMIT 7"
    ).fetchall()

    return render_template(
        "main/index.html",
        title="Home",
        current_user=g.user,
        posts=posts,
        len=len(posts),
    )


@bp.route("/blog")
def blog():
    """Blog route"""
    db = get_db()
    more_posts = False

    # variable used to manage the functionality
    # of displaying older posts
    o = request.args.get("o", None)
    o, offset = get_offset(o)

    # max amount of post that you can have per page
    max_per_page = MAX_PER_PAGE
    # amount of pages that will be displayed into the imagination
    page_span = PAGE_SPAN

    # maximum page index, for inpagination
    max_page = None
    try:
        count = (
            int(db.execute("SELECT COUNT(id) FROM posts;").fetchone()["COUNT(id)"])
            - offset
        )
        if count > 99:
            count = 99
            more_posts = True
        max_page = count // max_per_page
    except TypeError:
        if offset > 0:
            flash("There aren't any more posts.", category="alert-danger")
            return redirect(url_for("main.blog"))
    except Exception as e:
        logging.exception(e)
        abort(500)

    if max_page is None:
        return render_template(
            "main/blog.html",
            title="Home",
            current_user=g.user,
            posts=None,
            prev_pages=0,
            next_pages=0,
            current_page=0,
            pages=0,
            o=o,
            more_posts=more_posts,
        )

    index, prev_pages, next_pages = get_indexes(page_span, max_page)

    posts = get_posts(index, max_per_page, offset=offset)

    return render_template(
        "main/blog.html",
        title="Home",
        current_user=g.user,
        posts=posts,
        prev_pages=prev_pages,
        next_pages=next_pages,
        current_page=index,
        pages=max_page,
        o=o,
        more_posts=more_posts,
    )
