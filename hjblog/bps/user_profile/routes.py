import logging
import sqlite3
from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
import pyotp

from hjblog.auxiliaries import login_required, logout_user
from hjblog.bps.auth.forms import VerifyForm, VerifyForm2FA
from hjblog.bps.user_actions.auxiliaries import Coordinates
from hjblog.bps.user_profile.auxiliaries import (
    get_b64encoded_qr_image,
    get_profile_pic,
    save_picture,
)
from hjblog.bps.user_profile.forms import (
    ChangeCity,
    ChangeEmail,
    ChangeName,
    ChangePassword,
    ChangePicture,
)
from hjblog.db import get_db


bp = Blueprint("profile", __name__)


@bp.route("/manage_profile")
@login_required
def manage_profile():
    """View used by the user to manage the profile."""
    db = get_db()
    user = g.get("user", None)
    # User should never be `None`
    profile_pic = get_profile_pic(user["profile_pic"])
    city_id = user["city_id"]
    city_name = None
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
    return render_template(
        "user_profile/manage_profile.html",
        current_user=user,
        city_name=city_name,
        profile_pic=profile_pic,
    )


@bp.route("/change_picture", methods=["POST", "GET"])
@login_required
def change_picture():
    """View used to change user's profile picture."""
    db = get_db()
    user = g.get("user", None)
    # User should never be `None`
    profile_pic = get_profile_pic(user["profile_pic"])

    form = ChangePicture()

    if form.validate_on_submit():
        if form.picture.data:
            pic_name = save_picture(user["profile_pic"], form.picture.data)
            if isinstance(pic_name, int):
                abort(pic_name)
            try:
                db.execute(
                    r"UPDATE users SET profile_pic = ? WHERE (id = ?)",
                    (pic_name, user["id"]),
                )
                db.commit()
            except sqlite3.Error as e:
                logging.exception(e)
                abort(500)
            except Exception as e:
                # Unexpected behaviour
                logging.exception(e)
                abort(500)
        flash(
            "You have updated your profile picture correctly.", category="alert-success"
        )
        return redirect(url_for("profile.manage_profile"))

    if form.errors != {}:
        for error in form.errors.values():
            flash(f"{error[0]}", category="alert-danger")
        return redirect(url_for("profile.manage_profile"))

    return render_template(
        "user_profile/change_picture.html",
        current_user=user,
        profile_pic=profile_pic,
        form=form,
    )


@bp.route("/change_city", methods=["POST", "GET"])
@login_required
def change_city():
    """View used to change user's city"""
    user = g.get("user", None)
    # User should never be `None`
    profile_pic = get_profile_pic(user["profile_pic"])
    city_id = user["city_id"]
    city_name = None

    db = get_db()

    form = ChangeCity()
    if form.validate_on_submit():
        new_city = form.city.data
        if new_city == "":
            # field left empty in the form
            city_id = None
        else:
            coordinates = Coordinates(new_city, "", "")
            if coordinates.status_code > 399 or coordinates.status_code < 200:
                abort(coordinates.status_code)
            try:
                # at this point the city should be in the database
                city_id = db.execute(
                    "SELECT id FROM cities WHERE (name = ?)", (new_city,)
                ).fetchone()["id"]
            except sqlite3.Error as e:
                logging.exception(e)
                abort(500)
            except Exception as e:
                # Unexpected behaviour
                logging.exception(e)
                abort(500)
        try:
            db.execute(
                "UPDATE users SET city_id = ? WHERE (id = ?)", (city_id, user["id"])
            )
            db.commit()
            flash(
                "Informations about the city updated correctly.",
                category="alert-success",
            )
        except sqlite3.Error as e:
            logging.exception(e)
            abort(500)
        except Exception as e:
            # Unexpected behaviour
            logging.exception(e)
            abort(500)
        return redirect(url_for("profile.manage_profile"))
    else:
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

    if form.errors != {}:
        for error in form.errors.values():
            flash(f"{error[0]}", category="alert-danger")
        return redirect(url_for("profile.manage_profile"))

    return render_template(
        "user_profile/change_city.html",
        current_user=user,
        form=form,
        city_name=city_name,
        profile_pic=profile_pic,
    )


@bp.route("/change_username", methods=["POST", "GET"])
@login_required
def change_username():
    """View used to change username"""
    user = g.get("user", None)
    # User should never be `None`
    profile_pic = get_profile_pic(user["profile_pic"])

    form = ChangeName()
    if form.validate_on_submit():
        new_name = form.username.data
        db = get_db()
        try:
            db.execute(
                "UPDATE users SET username = ? WHERE (id = ?)", (new_name, user["id"])
            )
            db.commit()
        except sqlite3.Error as e:
            logging.exception(e)
            abort(500)
        except Exception as e:
            # Unexpected behaviour
            logging.exception(e)
            abort(500)
        flash("Username updated correctly.", category="alert-success")
        return redirect(url_for("profile.manage_profile"))

    if form.errors != {}:
        for error in form.errors.values():
            flash(f"{error[0]}", category="alert-danger")
        return redirect(url_for("profile.manage_profile"))

    return render_template(
        "user_profile/change_username.html",
        current_user=user,
        form=form,
        profile_pic=profile_pic,
    )


@bp.route("/change_email", methods=["POST", "GET"])
@login_required
def change_email():
    """View used to change email"""
    user = g.get("user", None)
    # User should never be `None`
    profile_pic = get_profile_pic(user["profile_pic"])

    form = ChangeEmail()
    if form.validate_on_submit():
        new_email = form.email.data
        db = get_db()
        try:
            db.execute(
                "UPDATE users SET email = ? WHERE (id = ?)", (new_email, user["id"])
            )
            db.commit()
        except sqlite3.Error as e:
            logging.exception(e)
            abort(500)
        except Exception as e:
            # Unexpected behaviour
            logging.exception(e)
            abort(500)
        flash("Email updated correctly.", category="alert-success")
        return redirect(url_for("profile.manage_profile"))

    if form.errors != {}:
        for error in form.errors.values():
            flash(f"{error[0]}", category="alert-danger")
        return redirect(url_for("profile.manage_profile"))

    return render_template(
        "user_profile/change_email.html",
        current_user=user,
        form=form,
        profile_pic=profile_pic,
    )


@bp.route("/change_password", methods=["POST", "GET"])
@login_required
def change_password():
    """View used to change password"""
    user = g.get("user", None)
    # User should never be `None`
    profile_pic = get_profile_pic(user["profile_pic"])

    form = ChangePassword()
    if form.validate_on_submit():
        new_pass = form.password.data
        new_hash = generate_password_hash(new_pass)
        db = get_db()
        try:
            db.execute(
                "UPDATE users SET hash_pass = ? WHERE (id = ?)", (new_hash, user["id"])
            )
            db.commit()
        except sqlite3.Error as e:
            logging.exception(e)
            abort(500)
        except Exception as e:
            # Unexpected behaviour
            logging.exception(e)
            abort(500)
        flash("Password updated correctly.", category="alert-success")
        return redirect(url_for("profile.manage_profile"))

    if form.errors != {}:
        for error in form.errors.values():
            flash(f"{error[0]}", category="alert-danger")
        return redirect(url_for("profile.manage_profile"))

    return render_template(
        "user_profile/change_password.html",
        current_user=user,
        form=form,
        profile_pic=profile_pic,
    )


@bp.route("/setup-2fa")
@login_required
def setup_two_factor_auth():
    """View used to setup 2fa"""
    # TODO: ask the user for a totp before enabling 2fs
    user = g.get("user", None)
    # User should never be `None`
    profile_pic = get_profile_pic(user["profile_pic"])

    if user["is_two_factor_authentication_enabled"] == True:
        flash("2fa is already enabled for your account.", category="alert-danger")
        return redirect(url_for("index"))

    db = get_db()
    secret = pyotp.random_base32()
    uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user["username"], issuer_name=current_app.config["APP_NAME"]
    )
    qr_image = get_b64encoded_qr_image(uri)

    try:
        db.execute(
            "UPDATE users SET is_two_factor_authentication_enabled = true, secret_token = ? WHERE (id = ?)",
            (secret, user["id"]),
        )
        db.commit()
    except sqlite3.Error as e:
        logging.exception(e)
        abort(500)
    except Exception as e:
        # Unexpected behaviour
        logging.exception(e)
        abort(500)

    flash("Congratulation, 2fa has been enabled.", category="alert-success")

    return render_template(
        "user_profile/setup-2fa.html",
        current_user=user,
        secret=secret,
        qr_image=qr_image,
        profile_pic=profile_pic,
    )


@bp.route("/disable-2fa")
@login_required
def disable_two_factor_auth():
    """View used to disaple 2fa"""
    user = g.get("user", None)
    if user is None:
        # this should not happen
        abort(500)
    if user["is_two_factor_authentication_enabled"] == False:
        flash("2fa is already disabled for your account.", category="alert-danger")
        return redirect(url_for("index"))

    db = get_db()

    try:
        db.execute(
            "UPDATE users SET is_two_factor_authentication_enabled = false, secret_token = NULL WHERE (id = ?)",
            (user["id"],),
        )
        db.commit()
    except sqlite3.Error as e:
        logging.exception(e)
        abort(500)
    except Exception as e:
        # Unexpected behaviour
        logging.exception(e)
        abort(500)

    flash("Congratulation you have disabled 2fa.", category="alert-success")

    return redirect(url_for("profile.manage_profile"))


@bp.route("/delete_account", methods=["GET", "POST"])
@login_required
def delete_account():
    """Route for deleting your account"""
    user = g.get("user", None)
    # This should not happen
    if user is None:
        abort(500)

    if user["is_two_factor_authentication_enabled"]:
        return redirect(url_for("profile.delete_account_with_2fa"))

    db = get_db()

    form = VerifyForm()
    if form.validate_on_submit():
        plain_pass = form.password.data
        if not check_password_hash(user["hash_pass"], plain_pass):
            flash("Incorrect credentials, retry", category="alert-danger")
            return redirect(url_for("profile.delete_account"))
        # TODO: logout_user before of after deletion?
        logout_user()
        try:
            db.execute("DELETE FROM users WHERE (id = ?)", (user["id"],))
            db.commit()
        except sqlite3.Error as e:
            logging.exception(e)
            abort(500)
        except Exception as e:
            # Unexpected behaviour
            logging.exception(e)
            abort(500)

        flash(
            "Your account has been deleted correctly...\nSee you space cowboy",
            category="alert-success",
        )
        return redirect(url_for("index"))
    if form.errors != {}:
        for error in form.errors.values():
            flash(f"{error[0]}", category="alert-danger")
        return redirect(url_for("profile.delete_account", id=user["id"]))

    return render_template("/user_profile/delete_account.html", form=form)


@bp.route("/delete_account_2fa", methods=["GET", "POST"])
@login_required
def delete_account_with_2fa():
    """Route for deleting your account when 2fa is enabled"""
    # TODO:
    user = g.get("user", None)
    # This should not happen
    if user["id"] is None:
        abort(500)

    if not user["is_two_factor_authentication_enabled"]:
        flash("2fa is not enabled on this account.", category="alert-danger")
        return redirect(url_for("profile.delete_account"))

    db = get_db()

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
            return redirect(url_for("profile.delete_account"))
        if not totp_server.verify(client_totp):
            flash("Incorrect credentials, retry", category="alert-danger")
            return redirect(url_for("profile.delete_account"))

        logout_user()
        try:
            db.execute("DELETE FROM users WHERE (id = ?)", (user["id"],))
            db.commit()
        except sqlite3.Error as e:
            logging.exception(e)
            abort(500)
        except Exception as e:
            # Unexpected behaviour
            logging.exception(e)
            abort(500)

        flash(
            "Your account has been deleted correctly...\nSee you space cowboy",
            category="alert-success",
        )
        return redirect(url_for("index"))

    if form.errors != {}:
        for error in form.errors.values():
            flash(f"{error[0]}", category="alert-danger")
        return redirect(url_for("profile.delete_account", id=user["id"]))

    return render_template("/user_profile/delete_account_2fa.html", form=form)

