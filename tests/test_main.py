import pytest
from flask.testing import FlaskClient

from auxiliaries import check_navbar
from conftest import AuthActions


def test_index(client: FlaskClient, auth: AuthActions):
    """Index route should:
    - respond with a 200 OK to a GET req
    - have a working navbar
    - it should display posts if there are posts, a message otherwise
    """
    # logged out
    res = client.get("/")
    assert res.status_code == 200

    # navbar
    check_navbar(client, auth)

    # posts
    assert (
        b'<a class="posts_compact_link" href="/user/visit_post/1">test-title-0</a>'
        in res.data
    )

    # delete posts
    auth.login(username="admin", password="prova")
    client.get("/user/delete_post/1")
    client.get("/user/delete_post/2")
    client.get("/user/delete_post/3")

    # no posts
    res_after_delete = client.get("/")
    assert (
        b'<span class="posts_compact_error">Currently there are no posts to be displayed, please try again later.</span>'
        in res_after_delete.data
    )


@pytest.mark.parametrize(
    "path",
    (
        "/auth/logout",
        "/manage_profile",
        "/change_picture",
        "/change_city",
        "/change_username",
        "/change_email",
        "/change_password",
        "/setup-2fa",
        "/disable-2fa",
        "/delete_account",
        "/delete_account_2fa",
        "/user/comment/1",
        "/user/delete_comment/1",
        "/user/weather",
    ),
)
def test_login_required(path: str, client: FlaskClient):
    """
    Responses with 302 when trying to access a protected route when not logged in
    """
    res = client.get(path)
    assert res.status_code == 302
    assert res.headers["Location"] == "/auth/login"


@pytest.mark.parametrize(
    "path",
    ("/user/new_post",),
)
def test_admin_only(path: str, client: FlaskClient, auth: AuthActions):
    """
    Responses with 302 when trying to access a protected route when not logged in
    Responses with 403 when trying to access a protected route when logged in as non admin
    """
    res = client.get(path)
    assert res.status_code == 302
    assert res.headers["Location"] == "/auth/login"

    auth.login(username="prova", password="prova")
    res = client.get(path)
    assert res.status_code == 403


@pytest.mark.parametrize(
    "path",
    (
        "/auth/register",
        "/auth/login",
        "/auth/authenticate/1",
        "/auth/2fa-verification/1",
    ),
)
def test_login_forbidden(path: str, client: FlaskClient, auth: AuthActions):
    """
    Redirects you to "/"
    Displays the phrase: "Log out before accessing this page"
    """
    auth.login(username="prova", password="prova")
    res = client.get(path)
    assert res.status_code == 302
    assert res.headers["Location"] == "/"
    res = client.get("/")
    assert b"Log out before accessing this page" in res.data
