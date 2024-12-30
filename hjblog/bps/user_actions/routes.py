import sqlite3
from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
    g,
)
from flask_wtf.csrf import logging

from hjblog.auxiliaries import admin_only, login_required
from hjblog.bps.general_auxiliaries.auxiliaries import get_indexes, get_offset
from hjblog.bps.user_actions.auxiliaries import (
    Coordinates,
    WeatherForecast,
)
from hjblog.bps.user_actions.forms import CommentPost, NewPost, QueryMeteoAPI
from hjblog.bps.user_profile.auxiliaries import get_profile_pic
from hjblog.db import get_db

bp = Blueprint("user", __name__, url_prefix="/user")


@bp.route("/new_post", methods=["GET", "POST"])
@admin_only
def new_post():
    """New Post route"""
    form = NewPost()
    user = g.get("user", None)

    db = get_db()

    if form.validate_on_submit():
        title = request.form.get("title", None)
        content = request.form.get("content", None)
        try:
            db.execute(
                "INSERT INTO posts (title, content, author_id) VALUES (?, ?, ?)",
                (title, content, user["id"]),
            )
            db.commit()
        except sqlite3.Error as e:
            logging.exception(e)
            flash(
                "Something went wrong, procedure aborted. Please wait some time then try again.",
                category="alert-danger",
            )
            return render_template(
                "/user_actions/new_post.html", form=form, title="New Post"
            )
        except Exception as e:
            logging.exception(e)
            abort(500)
        flash(f'The post "{title}" has been published.', category="alert-success")
        return redirect(url_for("index"))

    if form.errors != {}:
        for error in form.errors.values():
            flash(f"{error[0]}", category="alert-danger")

    return render_template(
        "/user_actions/new_post.html",
        form=form,
        title="New Post",
        current_user=user,
    )


@bp.route("/visit_post/<int:index>", methods=["GET", "POST"])
def visit_post(index: int):
    """Visit Post route"""
    identified = False

    db = get_db()

    user = g.get("user", None)

    post = db.execute(
        "SELECT title, content, posted, username, users.id AS author_id, posts.id FROM posts JOIN users ON (posts.author_id = users.id) WHERE (posts.id = ?)",
        (index,),
    ).fetchone()
    if not post:
        abort(404)

    # Display comments
    comments = db.execute(
        "SELECT comments.id AS id, users.id as author_id, post_id, content, username, written FROM comments JOIN users ON (users.id = comments.author_id) WHERE (post_id = ?) ORDER BY written DESC LIMIT 7",
        (index,),
    ).fetchall()

    profile_pic = None
    if user is not None:
        profile_pic = get_profile_pic(user["profile_pic"])
        if user["id"] == post["author_id"]:
            identified = True

    return render_template(
        "/user_actions/visit_post.html",
        title=f"{post['title']}",
        post=post,
        identified=identified,
        current_user=user,
        comments=comments,
        profile_pic=profile_pic,
    )


@bp.route("/delete_post/<int:index>", methods=["GET"])
@admin_only
def delete_post(index: int):
    """Delete Post route"""
    db = get_db()

    post = db.execute(
        "SELECT id, author_id FROM posts WHERE (id = ?)", (index,)
    ).fetchone()
    if not post:
        abort(404)

    if g.user["id"] != post["author_id"]:
        abort(404)

    try:
        db.execute("DELETE FROM posts WHERE (id = ?)", (index,))
    except sqlite3.Error as e:
        logging.exception(e)
        abort(500)
    except Exception as e:
        logging.exception(e)
        abort(500)

    try:
        db.execute("DELETE FROM comments WHERE (post_id = ?)", (index,))
    except sqlite3.Error as e:
        logging.exception(e)
        abort(500)
    except Exception as e:
        logging.exception(e)
        abort(500)

    try:
        db.commit()
    except sqlite3.Error as e:
        logging.exception(e)
        abort(500)
    except Exception as e:
        logging.exception(e)
        abort(500)

    flash("The post was removed correctly.", category="alert-success")
    return redirect(url_for("index"))


@bp.route("/comment/<int:index>", methods=["GET", "POST"])
@login_required
def comment_post(index: int):
    """Comment Post route"""
    db = get_db()

    user = g.get("user", None)
    # User should never be `None`
    profile_pic = get_profile_pic(user["profile_pic"])

    post = db.execute(
        "SELECT posts.id, posted, title, content, username FROM posts JOIN users ON (posts.author_id = users.id) WHERE (posts.id = ?)",
        (index,),
    ).fetchone()
    if not post:
        return abort(404)

    form = CommentPost()

    if form.validate_on_submit():
        try:
            content = form.content.data
            # NOTE: `g.user["id"] should always be valid becouse of `login_required`
            db.execute(
                "INSERT INTO comments (post_id, content, author_id) VALUES (?, ?, ?)",
                (post["id"], content, g.user["id"]),
            )
            db.commit()
        except sqlite3.Error as e:
            logging.exception(e)
            abort(500)
        except Exception as e:
            logging.exception(e)
            abort(500)
        flash("Success, your comment has been posted.", category="alert-success")
        return redirect(url_for("user.visit_post", index=post["id"]))

    if form.errors != {}:
        for error in form.errors.values():
            flash(f"{error[0]}", category="alert-danger")

    return render_template(
        "/user_actions/comment_post.html",
        title=post["title"],
        username=post["username"],
        content=post["content"],
        date=post["posted"],
        current_user=g.user,
        form=form,
        profile_pic=profile_pic,
    )


@bp.route("/all_comments/<int:post_id>")
def all_comments(post_id: int):
    """This route shows all the comments relative to a specific posts,
    allows user interactions.
    """
    db = get_db()
    user = g.get("user", None)
    profile_pic = None
    if user is not None:
        profile_pic = get_profile_pic(user["profile_pic"])
    comments = None
    more_comments = False
    msg_no_comments = None
    count = None
    o = request.args.get("o", None)
    o, offset = get_offset(o)

    post = db.execute(
        "SELECT id, author_id, content, title, posted FROM posts WHERE (id = ?)",
        (post_id,),
    ).fetchone()
    if not post:
        abort(404)

    max_per_page = 15
    page_span = 4

    try:
        count = db.execute(
            "SELECT COUNT(id) FROM comments WHERE (post_id = ?)",
            (post["id"],),
        ).fetchone()["COUNT(id)"]
        if count == 0:
            msg_no_comments = (
                "No comment to display so far, be the first one to leave a comment."
            )
        count = count - offset
        if count > 100:
            count = 100
            more_comments = True
    except TypeError:
        msg_no_comments = "No more comments are avaible."
        count = 0
    except Exception as e:
        # Unexpected behaviour
        logging.exception(e)
        abort(500)

    if count == 0:
        flash(
            msg_no_comments,
            category="alert-danger",
        )
        return redirect(url_for("user.visit_post", index=post_id))

    max_page = int(count / max_per_page)

    index, prev_pages, next_pages = get_indexes(page_span, max_page)

    batch = db.execute(
        "SELECT comments.author_id as author_id, users.username, comments.id, comments.content, comments.written FROM comments JOIN users ON (users.id = comments.author_id) WHERE (comments.post_id = ?) ORDER BY (comments.written) LIMIT 100 OFFSET (?)",
        (post["id"], offset),
    )

    for _ in range(0, index + 1):
        comments = batch.fetchmany(max_per_page)

    if not comments:
        flash(
            "No comment to display so far, be the first one to leave a comment",
            category="alert-danger",
        )
        return redirect(url_for("user.visit_post", index=post_id))

    return render_template(
        "/user_actions/all_comments.html",
        title=post["id"],
        current_user=user,
        post=post,
        current_page=index,
        prev_pages=prev_pages,
        next_pages=next_pages,
        pages=max_page,
        comments=comments,
        o=o,
        more_comments=more_comments,
        profile_pic=profile_pic,
    )


@bp.route("/delete_comment/<int:index>")
@login_required
def delete_comment(index: int):
    """Deletes a comment associated with the post with id `index`"""
    db = get_db()
    user_id = session.get("user_id", None)
    post = db.execute(
        "SELECT id, author_id FROM posts WHERE (id = ?);", (index,)
    ).fetchone()
    if post is None:
        abort(404)

    # id of the comment that will be canceled
    comment_id = request.args.get("cid", None)
    if comment_id is None:
        abort(400)
    comment = db.execute(
        "SELECT id, author_id, post_id FROM comments WHERE (id = ?)", (comment_id,)
    ).fetchone()
    # check if the user is authorized to perform the action
    if user_id != comment["author_id"] and user_id != post["author_id"]:
        abort(401)

    # check if the comment belong to the post
    if index != comment["post_id"]:
        abort(400)

    # act
    try:
        db.execute("DELETE FROM comments WHERE (id = ?)", (comment_id,))
        db.commit()
    except sqlite3.Error as e:
        logging.exception(e)
        abort(500)
    except Exception as e:
        # Unexpected behaviour
        logging.exception(e)
        abort(500)

    flash("The comment was deleted correctly.", category="alert-success")
    return redirect(url_for("user.visit_post", index=index))


@bp.route("/weather", methods=["GET", "POST"])
@login_required
def weather():
    """Route that allows the logged in user to access informations relative to the weather of his city or another city of his choice."""
    user = g.get("user", None)
    # User should never be `None`
    profile_pic = get_profile_pic(user["profile_pic"])
    city_id = user["city_id"]
    city_name = None
    forecasts = None

    form = QueryMeteoAPI()
    if form.validate_on_submit():
        city = form.city.data
        latitude = form.latitude.data
        longitude = form.longitude.data
        # TODO: think about input sanitation, we have a regex in the form
        # TODO: test the API
        coordinates: Coordinates = Coordinates(city, latitude, longitude)
        if coordinates.status_code > 399 or coordinates.status_code < 200:
            abort(coordinates.status_code)

        forecasts = WeatherForecast(coordinates)
        if forecasts.status_code < 200 or forecasts.status_code > 399:
            abort(forecasts.status_code)
        return render_template(
            "/user_actions/weather.html",
            title="Weather",
            city_name=city,
            form=form,
            current_user=g.user,
            forecasts=forecasts,
            profile_pic=profile_pic
        )
    else:
        db = get_db()
        if city_id is not None:
            try:
                city_name = db.execute(
                    "SELECT name FROM cities WHERE (id = ?)", (city_id,)
                ).fetchone()["name"]
            except sqlite3.Error as e:
                logging.exception(e)
                abort(500)
            except Exception as e:
                logging.exception(e)
                abort(500)
            coordinates = Coordinates(city_name, "", "")
            # NOTE: this should not happen since the information should be in the database already
            if coordinates.status_code > 399 or coordinates.status_code < 200:
                abort(coordinates.status_code)
            forecasts = WeatherForecast(coordinates)
        if user is None:
            # this should not happen becouse of `@login_required`
            abort(500)

    if form.errors != {}:
        for error in form.errors.values():
            flash(f"{error[0]}", category="alert-danger")

    return render_template(
        "/user_actions/weather.html",
        title="Weather",
        city_name=city_name,
        form=form,
        current_user=g.user,
        forecasts=forecasts,
        profile_pic=profile_pic
    )
