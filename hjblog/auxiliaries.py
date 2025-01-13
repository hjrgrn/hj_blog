import os
import re
import getpass
import functools
import sys
from typing import Callable, ParamSpec

from flask import abort, flash, g, session, url_for, redirect

from werkzeug.security import generate_password_hash

P = ParamSpec("P")


def create_instance_folder(instance_path: str):
    try:
        os.mkdir(instance_path)
    except OSError:
        pass

    upload_folder = os.path.join(instance_path, "uploads")
    try:
        os.mkdir(upload_folder)
    except OSError:
        pass


def get_admin_credencials() -> tuple[str, str, str] | None:
    """Gets the credentials for creating a new admin
    account directly from the user, returns `None`
    if the values provided aren't good.

    :returns: (username, email, password_hash)
    """
    username = input("Username: ")
    if len(username) > 60:
        print(
            "Error: Username provided should not be more than 60 characters long.",
            file=sys.stderr,
        )
        return None

    email = input("Email: ")
    if len(email) > 300:
        print(
            "Error: Email provided should not be more than 300 characters long.",
            file=sys.stderr,
        )
        return None
    # TODO: email validation
    good = re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email)
    if not good:
        print("Error: The email format is not correct.", file=sys.stderr)
        return None

    plain_password = getpass.getpass("Password: ")
    if len(plain_password) > 200:
        print(
            "Error: Password provided should not be more than 200 characters long.",
            file=sys.stderr,
        )
        return None

    confirm_plain_password = getpass.getpass("Type your password again: ")
    if plain_password != confirm_plain_password:
        print(
            "Error: The confirmation password is different from the password you provided.",
            file=sys.stderr,
        )
        return None

    password_hash = generate_password_hash(plain_password)

    return (username, email, password_hash)


def login_user(user_id: int):
    """Auxilliary function that logs the user in
    the current session.
    """
    session.clear()
    session["user_id"] = user_id


def logout_user():
    """Auxilliary functions that logs the user out
    from the current session.
    """
    session.clear()


def login_required(view: Callable[P, str]) -> Callable[P, str]:
    """Decorator that forbids to reach a certain page
    if the user is not logged in.
    """

    @functools.wraps(view)
    def wrapper(*args: P.args, **kwargs: P.kwargs):
        if g.user is None:
            flash("Login required to view this page.", category="alert-danger")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapper


def login_forbidden(view: Callable[P, str]) -> Callable[P, str]:
    """Decorator that forbids to reach a certain page
    if the user is logged in.
    """

    @functools.wraps(view)
    def wrapper(*args: P.args, **kwargs: P.kwargs):
        if g.user is not None:
            flash("Log out before accessing this page", category="alert-danger")
            return redirect(url_for("index"))
        return view(*args, **kwargs)

    return wrapper


def admin_only(view: Callable[P, str]) -> Callable[P, str]:
    """Decorator that forbids to reach a certain page
    if you are not an admin.
    """

    @functools.wraps(view)
    def wrapper(*args: P.args, **kwargs: P.kwargs):
        if g.user is None:
            flash("Login required to view this page.", category="alert-danger")
            return redirect(url_for("auth.login"))
        if g.user["is_admin"] == False:
            abort(403)

        return view(*args, **kwargs)

    return wrapper
