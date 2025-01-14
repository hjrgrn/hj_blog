from flask import url_for
from flask.testing import FlaskClient

from auxiliaries import check_navbar
from conftest import AuthActions
from hjblog.db import get_db


def test_manage_profie(client: FlaskClient, auth: AuthActions):
    """Manage Profile should:
    - having a working navbar
    - refuse the connection if not logged in. 302 redirect to login.
    - grant access if you are registered. 200.
    - display the profile picture
    - display user information
    - present links to routes for changing information
    """

    check_navbar(client, auth)

    res = client.get("/manage_profile")
    assert res.status_code == 302
    assert res.headers["Location"] == "/auth/login"

    auth.login(username="admin", password="prova")
    res = client.get("/manage_profile")
    assert res.status_code == 200

    assert b'<img class="profile-picture" src="' in res.data

    assert b"<p>Username: admin</p>" in res.data
    assert b"<p>Email: admin@admin.com</p>" in res.data
    assert b"<p>Email: admin@admin.com</p>" in res.data
    assert b"<p>City: Not yet configured</p>" in res.data

    with client.application.test_request_context():
        url = url_for("profile.change_username")
        html_tag = f'<form action="{url}" method="get" accept-charset="utf-8">'.encode(
            "utf-8"
        )
        assert html_tag in res.data
        url = url_for("profile.change_email")
        html_tag = f'<form action="{url}" method="get" accept-charset="utf-8">'.encode(
            "utf-8"
        )
        assert html_tag in res.data
        url = url_for("profile.change_password")
        html_tag = f'<form action="{url}" method="get" accept-charset="utf-8">'.encode(
            "utf-8"
        )
        assert html_tag in res.data
        url = url_for("profile.change_city")
        html_tag = f'<form action="{url}" method="get" accept-charset="utf-8">'.encode(
            "utf-8"
        )
        assert html_tag in res.data
        url = url_for("profile.change_picture")
        html_tag = f'<form action="{url}" method="get" accept-charset="utf-8">'.encode(
            "utf-8"
        )
        assert html_tag in res.data
        url = url_for("profile.setup_two_factor_auth")
        html_tag = f'<form action="{url}" method="get" accept-charset="utf-8">'.encode(
            "utf-8"
        )
        assert html_tag in res.data
        url = url_for("profile.delete_account")
        html_tag = f'<form action="{url}" method="get" accept-charset="utf-8">'.encode(
            "utf-8"
        )
        assert html_tag in res.data


def test_change_username(client: FlaskClient, auth: AuthActions):
    """Change Username should:
    - having a working navbar
    - refuse the connection if not logged in. 302 redirect to login, both get and post
    - accept a get request if logged in, 200.
    - a link for going back to `manage_profile` route
    - display old username
    - change the username when logged in through a post request, 200
    """
    check_navbar(client, auth)

    res = client.get("/change_username")
    assert res.status_code == 302
    assert res.headers["Location"] == "/auth/login"
    res = client.post("/change_username")
    assert res.status_code == 302
    assert res.headers["Location"] == "/auth/login"

    auth.login(username="admin", password="prova")
    res = client.get("/change_username")
    assert res.status_code == 200

    with client.application.test_request_context():
        url = url_for("profile.manage_profile")
        html_tag = f'<a href="{url}" class="auth_link">profile</a>'.encode("utf-8")
        assert html_tag in res.data

    assert b"<p>Old username: admin</p>" in res.data

    id = None
    with client.application.test_request_context():
        db = get_db()
        id = db.execute(
            "SELECT id FROM users WHERE username = ?", ("admin",)
        ).fetchone()["id"]
    assert id is not None
    username = "mario"
    res = client.post(
        "/change_username", data={"username": username, "submit": "Submit"}
    )
    with client.application.test_request_context():
        db = get_db()
        stored_username = db.execute(
            "SELECT username FROM users WHERE id = ?", (id,)
        ).fetchone()["username"]
        assert stored_username == username


def test_change_email(client: FlaskClient, auth: AuthActions):
    """Change Email should:
    - having a working navbar
    - refuse the connection if not logged in. 302 redirect to login, both get and post
    - accept a get request if logged in, 200.
    - a link for going back to `manage_profile` route
    - display old email
    - change the email when logged in through a post request, 200
    """
    check_navbar(client, auth)

    res = client.get("/change_email")
    assert res.status_code == 302
    assert res.headers["Location"] == "/auth/login"
    res = client.post("/change_email")
    assert res.status_code == 302
    assert res.headers["Location"] == "/auth/login"

    auth.login(username="admin", password="prova")
    res = client.get("/change_email")
    assert res.status_code == 200

    with client.application.test_request_context():
        url = url_for("profile.manage_profile")
        html_tag = f'<a href="{url}" class="auth_link">profile</a>'.encode("utf-8")
        assert html_tag in res.data

    assert b"<p>Old email: admin@admin.com</p>" in res.data

    id = None
    with client.application.test_request_context():
        db = get_db()
        id = db.execute(
            "SELECT id FROM users WHERE username = ?", ("admin",)
        ).fetchone()["id"]
    assert id is not None
    email = "mario@mario.com"
    res = client.post("/change_email", data={"email": email, "submit": "Submit"})
    with client.application.test_request_context():
        db = get_db()
        stored_email = db.execute(
            "SELECT email FROM users WHERE id = ?", (id,)
        ).fetchone()["email"]
        assert stored_email == email


def test_change_password(client: FlaskClient, auth: AuthActions):
    """Change Password should:
    - having a working navbar
    - refuse the connection if not logged in. 302 redirect to login, both get and post
    - accept a get request if logged in, 200.
    - a link for going back to `manage_profile` route
    - change the password when logged in through a post request, 200
    """
    check_navbar(client, auth)

    res = client.get("/change_password")
    assert res.status_code == 302
    assert res.headers["Location"] == "/auth/login"
    res = client.post("/change_password")
    assert res.status_code == 302
    assert res.headers["Location"] == "/auth/login"

    auth.login(username="admin", password="prova")
    res = client.get("/change_password")
    assert res.status_code == 200

    with client.application.test_request_context():
        url = url_for("profile.manage_profile")
        html_tag = f'<a href="{url}" class="auth_link">profile</a>'.encode("utf-8")
        assert html_tag in res.data

    id = None
    with client.application.test_request_context():
        db = get_db()
        id = db.execute(
            "SELECT id FROM users WHERE username = ?", ("admin",)
        ).fetchone()["id"]
    assert id is not None
    password = "222"
    res = client.post(
        "/change_password",
        data={"password": password, "confirm": password, "submit": "Submit"},
    )
    auth.logout()
    auth.login(username="admin", password="222")
    # Using a protected route to see if we can login
    res = client.get("/change_password")
    assert res.status_code == 200


def test_change_city(client: FlaskClient, auth: AuthActions):
    """Change Email should:
    - having a working navbar
    - refuse the connection if not logged in. 302 redirect to login, both get and post
    - accept a get request if logged in, 200.
    - a link for going back to `manage_profile` route
    - display old city or `Not yet configured`
    - change the email when logged in through a post request, 200
    """
    check_navbar(client, auth)

    res = client.get("/change_city")
    assert res.status_code == 302
    assert res.headers["Location"] == "/auth/login"
    res = client.post("/change_city")
    assert res.status_code == 302
    assert res.headers["Location"] == "/auth/login"

    auth.login(username="admin", password="prova")
    res = client.get("/change_city")
    assert res.status_code == 200

    with client.application.test_request_context():
        url = url_for("profile.manage_profile")
        html_tag = f'<a href="{url}" class="auth_link">profile</a>'.encode("utf-8")
        assert html_tag in res.data

    assert b"<p>Old city: Not yet configured</p>" in res.data

    id = None
    with client.application.test_request_context():
        db = get_db()
        id = db.execute(
            "SELECT id FROM users WHERE username = ?", ("admin",)
        ).fetchone()["id"]
    assert id is not None
    city = "Rome"
    res = client.post("/change_city", data={"city": city, "submit": "Submit"})
    with client.application.test_request_context():
        db = get_db()
        city_id = db.execute(
            "SELECT city_id FROM users WHERE id = ?", (id,)
        ).fetchone()["city_id"]
        stored_city = db.execute(
            "SELECT name FROM cities WHERE id = ?", (city_id,)
        ).fetchone()["name"]
        assert stored_city == city


def test_change_picture(client: FlaskClient, auth: AuthActions):
    """Change Picture should:
    - having a working navbar
    - refuse the connection if not logged in. 302 redirect to login, both get and post
    - accept a get request if logged in, 200.
    - a link for going back to `manage_profile` route
    - display old picture, the default `anonymous_user.png` is a picture hasn't been provided.
    - update to a new picture using the post route
    - new picture being displayed
    """
    check_navbar(client, auth)

    res = client.get("/change_picture")
    assert res.status_code == 302
    assert res.headers["Location"] == "/auth/login"
    res = client.post("/change_picture")
    assert res.status_code == 302
    assert res.headers["Location"] == "/auth/login"

    auth.login(username="admin", password="prova")
    res = client.get("/change_picture")
    assert res.status_code == 200

    with client.application.test_request_context():
        url = url_for("profile.manage_profile")
        html_tag = f'<a href="{url}" class="auth_link">profile</a>'.encode("utf-8")
        assert html_tag in res.data

    # No picture provided
    with client.application.test_request_context():
        db = get_db()
        profile_pic_name = db.execute(
            "SELECT profile_pic FROM users WHERE username = ?", ("admin",)
        ).fetchone()["profile_pic"]
        assert profile_pic_name is None
    assert (
        b'<img src="/static/default_files/anonymous_user.png" alt="profile picture"/>'
        in res.data
    )

    res = client.post(
        "/change_picture",
        data={
            "picture": (
                open("hjblog/static/default_files/anonymous_user.png", "rb"),
                "anonymous_user.png",
            ),
            "submit": "Submit",
        },
    )
    assert res.status_code == 302
    assert res.headers["Location"] == "/manage_profile"
    pic_name = None
    with client.application.test_request_context():
        db = get_db()
        pic_name = db.execute(
            "SELECT profile_pic FROM users WHERE username = ?", ("admin",)
        ).fetchone()["profile_pic"]
        assert pic_name is not None
        res = client.get("/manage_profile")
        assert b"You have updated your profile picture correctly" in res.data
        # New picture is being displayed
        assert (
            url_for("index.profile_pictures", pic_name=pic_name).encode("utf-8")
            in res.data
        )


def test_2fa(client: FlaskClient, auth: AuthActions):
    """Functionality for 2FA should:
    - refuse the connection if not logged in. 302 redirect to login
    - respond 405 to post request
    - not allow you to disable 2fa if it's already disabled
    - enables 2fa if not already enabled
    - not allow you to enable 2fa if it's already enabled
    - disable 2fa if not already disabled
    """
    res = client.get("/setup-2fa")
    check_navbar(client, auth)
    assert res.status_code == 302
    assert res.headers["Location"] == "/auth/login"
    res = client.post("/setup-2fa")
    assert res.status_code == 405
    res = client.get("/disable-2fa")
    assert res.status_code == 302
    assert res.headers["Location"] == "/auth/login"
    res = client.post("/disable-2fa")
    assert res.status_code == 405

    auth.login(username="admin", password="prova")
    _ = client.get("/disable-2fa")
    res = client.get("/manage_profile")
    assert b"2fa is already disabled for your account." in res.data

    _ = client.get("/setup-2fa")
    res = client.get("/manage_profile")
    # link has changed to `/disable-2fa`
    assert (
        b'<form action="/disable-2fa" method="get" accept-charset="utf-8">' in res.data
    )

    _ = client.get("/setup-2fa")
    res = client.get("/manage_profile")
    assert b"2fa is already enabled for your account." in res.data

    _ = client.get("/disable-2fa")
    res = client.get("/manage_profile")
    # link has changed to `/setup-2fa`
    assert b'<form action="/setup-2fa" method="get" accept-charset="utf-8">' in res.data


def delete_account(client: FlaskClient, auth: AuthActions):
    """Functionality for 2FA should:
    - refuse the connection if not logged in. 302 redirect to login
    - respond with 200 if user is logged in
    - delete account with a post request and 302 redirect to index
    - redirect you to delete_account_with_2fa if 2fa is enabled
    """
    res = client.get("/delete_account")
    check_navbar(client, auth)
    assert res.status_code == 302
    assert res.headers["Location"] == "/auth/login"

    auth.login(username="admin", password="prova")
    res = client.get("/delete_account")
    assert res.status_code == 200

    res = client.post("/delete_account", data={"password": "prova", "submit": "Submit"})
    assert res.status_code == 302
    assert res.headers["Location"] == "/"

    with client.application.app_context():
        db = get_db()
        res = db.execute("SELECT id FROM users WHERE (username = admin)").fetchone()
        assert res is None

    auth.login(username="prova", password="prova")
    _ = client.get("/setup-2fa")
    res = client.get("/delete_account")
    assert res.status_code == 302
    assert res.headers["Location"] == "/delete_account_2fa"
