from flask.testing import FlaskClient
from conftest import AuthActions


def check_navbar(client: FlaskClient, auth: AuthActions):
    """This is a function used with procedure of unit testing,
    it tests if:
    - not logged in user is presented with a specific navbar
    - logged(not admin) in user is presented with another navbar(with logout and user)
    - logged(admin) in user is presented with another navbar(with logout and user page)
    """
    # not logged in
    res = client.get("/")
    assert b'<a href="/auth/register" class="link">Register</a>' in res.data
    assert b'<a href="/auth/login" class="link">Log In</a>' in res.data

    # logged in no admin
    auth.login(username="prova", password="prova")
    res_after_login = client.get("/index")
    assert b'<a href="/auth/logout" class="link">Log Out</a>' in res_after_login.data
    client.get("/auth/logout")

    # logged in admin
    auth.login(username="admin", password="prova")
    res_after_login_admin = client.get("/")
    assert (
        b'<a href="/auth/logout" class="link">Log Out</a>' in res_after_login_admin.data
    )
    assert (
        b'<a href="/user/new_post" class="link">Post</a>'
        in res_after_login_admin.data
    )

    # logout
    client.get("/auth/logout")
