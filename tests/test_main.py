from flask.testing import FlaskClient

from auxiliaries import check_navbar
from conftest import AuthActions


def test_index(client: FlaskClient, auth: AuthActions):
    """Index route should:
    - respond with a 200 OK to a GET req
    - have a working navbar
    - it should display posts if there are posts, a message otherwise
    TODO
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
