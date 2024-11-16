import sqlite3
import pyotp
import logging

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    url_for,
    session,
    g,
)
from werkzeug.security import check_password_hash, generate_password_hash

from hjblog.bps.user_actions.auxiliaries import Coordinates
from hjblog.db import get_db
from hjblog.auxiliaries import login_forbidden, login_required, login_user, logout_user
from .forms import LogInForm, RegisterForm, VerifyForm, VerifyForm2FA

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=["GET", "POST"])
@login_forbidden
def register():
    """Route responsable for registering the user."""

    form = RegisterForm()
    db = None

    if form.validate_on_submit():
        name = form.username.data
        password = form.password.data
        hash_pass = generate_password_hash(password)
        email = form.email.data
        city = form.city.data
        db = get_db()
        try:
            if len(city) == 0:
                db.execute(
                    "INSERT INTO users (username, email, hash_pass) VALUES (?, ?, ?)",
                    (name, email, hash_pass),
                )
                db.commit()
            else:
                coordinates = Coordinates(city, "", "")
                if coordinates.status_code > 399 or coordinates.status_code < 200:
                    abort(coordinates.status_code)
                city_id = db.execute(
                    "SELECT id FROM cities WHERE (name = ?)", (coordinates.city,)
                ).fetchone()["id"]

                db.execute(
                    "INSERT INTO users (username, email, city_id, hash_pass) VALUES (?, ?, ?, ?)",
                    (name, email, city_id, hash_pass),
                )
                db.commit()
            id = db.execute(
                "SELECT id FROM users WHERE (username = ?)", (name,)
            ).fetchone()["id"]
            login_user(id)
            flash(
                "Congratulation, you have been registered correctly.",
                category="alert-success",
            )
            return redirect(url_for("index"))
        except sqlite3.Error as e:
            logging.exception(e)
            abort(500)
        except Exception as e:
            logging.exception(e)
            abort(500)
    if form.errors != {}:
        for err_msg in form.errors.values():
            flash(f"{err_msg[0]}", category="alert-danger")

    return render_template("/auth/register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
@login_forbidden
def login():
    """Route responsable for loggin in the user"""
    # TODO: this may not be the best way to implement this
    db = get_db()
    form = LogInForm()
    if form.validate_on_submit():
        username = form.username.data
        info = db.execute(
            "SELECT id, is_two_factor_authentication_enabled FROM users WHERE (username = ?)",
            (username,),
        ).fetchone()
        if info is None:
            flash(
                "This username is not registerd, register now!", category="alert-danger"
            )
            return redirect(url_for("auth.register"))
        if info["is_two_factor_authentication_enabled"]:
            return redirect(url_for("auth.verification_with_2fa", id=info["id"]))
        return redirect(url_for("auth.verification", id=info["id"]))
    if form.errors != {}:
        for v in form.errors.values():
            flash(f"{v[0]}", category="alert-danger")

    return render_template("auth/login.html", form=form)


@bp.route("/authenticate/<int:id>", methods=["GET", "POST"])
@login_forbidden
def verification(id: int):
    """View used for verifying password."""
    db = get_db()
    user = db.execute(
        "SELECT id, is_two_factor_authentication_enabled, hash_pass FROM users WHERE (id = ?)",
        (id,),
    ).fetchone()
    if user is None:
        flash("This username is not registerd, register now!", category="alert-danger")
        return redirect(url_for("auth.register"))

    if user["is_two_factor_authentication_enabled"]:
        return redirect(url_for("auth.verification_with_2fa", id=user["id"]))
    form = VerifyForm()
    if form.validate_on_submit():
        plain_pass = form.password.data
        if not check_password_hash(user["hash_pass"], plain_pass):
            flash("Incorrect credentials, retry", category="alert-danger")
            return redirect(url_for("auth.login"))
        login_user(user["id"])
        flash("Welcome back!", category="alert-success")
        return redirect(url_for("index"))
    if form.errors != {}:
        for error in form.errors.values():
            flash(f"{error[0]}", category="alert-danger")
        return redirect(url_for("profile.manage_profile", id=user["id"]))

    return render_template("auth/verification.html", form=form)


@bp.route("/2fa-verification/<int:id>", methods=["POST", "GET"])
@login_forbidden
def verification_with_2fa(id: int):
    """View used for verifying password and totp."""
    db = get_db()
    user = db.execute(
        "SELECT id, username, is_two_factor_authentication_enabled, hash_pass, secret_token FROM users WHERE (id = ?)",
        (id,),
    ).fetchone()
    if user is None:
        flash("This username is not registerd, register now!", category="alert-danger")
        return redirect(url_for("auth.register"))

    if not user["is_two_factor_authentication_enabled"]:
        flash("2fa is not enabled on this account.", category="alert-danger")
        return redirect(url_for("auth.verification", id=user["id"]))

    uri = pyotp.totp.TOTP(user["secret_token"]).provisioning_uri(
        name=user["username"], issuer_name=current_app.config["APP_NAME"]
    )

    form = VerifyForm2FA()
    if form.validate_on_submit():
        totp_server = pyotp.parse_uri(uri)
        plain_pass = form.password.data
        client_totp = form.totp.data
        if not check_password_hash(user["hash_pass"], plain_pass):
            flash("Incorrect credentials, retry", category="alert-danger")
            return redirect(url_for("auth.login"))
        if not totp_server.verify(client_totp):
            flash("Incorrect credentials, retry", category="alert-danger")
            return redirect(url_for("auth.login"))
        login_user(user["id"])
        flash("Welcome back!", category="alert-success")
        return redirect(url_for("index"))
    if form.errors != {}:
        for v in form.errors.values():
            flash(f"{v[0]}", category="alert-danger")

    return render_template("auth/verification_with_2fa.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    """Route responsable for logging out the user."""
    id = session.get("user_id", None)
    if id:
        logout_user()
        flash("See you space cowboy.", category="alert-success")
    return redirect(url_for("index"))


@bp.before_app_request
def load_logged_in_user():
    """`before_app_request` registers a function that runs before
    the view function, no matter what URL is requested, even
    on views that aren't in this specific blueprint
    """
    # TODO: error handling on the database query
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = (
            get_db()
            .execute(
                "SELECT id, username, email, city_id, is_admin, is_two_factor_authentication_enabled, secret_token FROM users WHERE id = ?",
                (user_id,),
            )
            .fetchone()
        )
