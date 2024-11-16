from flask import Flask
from flask.testing import FlaskClient

from auxiliaries import check_navbar
from conftest import AuthActions
from hjblog.db import get_db


def test_new_post(client: FlaskClient, auth: AuthActions, app: Flask):
    """New Post should:
    - have a working navbar
    - deny access(302 redirecting to login page) if you are not logged in(both GET and POST)
    - deny access(403 forbidden) if you are logged in as a non admin user(both GET and POST)
    - responds 200 OK to a GET request if you are an admin
    - allow you to post through a POST req if you are an admin
    """
    # navbar
    check_navbar(client, auth)

    # logged out
    res = client.get("/user/new_post")
    assert res.status_code == 302
    assert res.headers["Location"] == "/auth/login"
    assert client.post("/user/new_post").status_code == 302
    assert res.headers["Location"] == "/auth/login"
    # logged in non admin
    auth.login(username="prova", password="prova")
    assert client.get("/user/new_post").status_code == 403
    assert client.post("/user/new_post").status_code == 403
    auth.logout()

    # logged in as admin
    auth.login(username="admin", password="prova")
    assert client.get("/user/new_post").status_code == 200
    title = "Post di Prova da Admin"
    content = "Post di prova da Admin, questo è il content."
    # post something
    client.post(
        "/user/new_post", data={"title": title, "content": content, "submit": "Post"}
    )
    # check post has been registered
    with app.app_context():
        db = get_db()
        entry = db.execute("SELECT * FROM posts WHERE (title = ?)", (title,)).fetchone()
        assert entry is not None


def test_visit_post(client: FlaskClient, auth: AuthActions):
    """New Post should:
    - having a working navbar
    - responds 200 OK to a GET if the post exists
    - display correct comments
    - responds 404 NOT FOUND to a GET request that does not exists
    - asks you to comment if you are logged(not admin) in but not to delete the post
    - asks you to comment and to delete if you are logged is as admin
    - display no comments and a message if there are no comments
    """
    # navbar
    check_navbar(client, auth)

    # existing post
    res = client.get("/user/visit_post/1")
    assert res.status_code == 200

    # comment associated with the right post
    assert b"<p>Commento di prova da utente &#39;prova&#39;</p>" in res.data
    # comment not associated with the right post
    assert not b"<p>Questo commento non apparir" in res.data

    # non existing post
    res = client.get("/user/visit_post/30")
    assert res.status_code == 404

    # non admin user
    auth.login(username="prova", password="prova")
    res = client.get("/user/visit_post/1")
    assert (
        b'<a class="visit_post_delete_post" href="/user/comment/1">Comment</a>'
        in res.data
    )
    assert not b'class="visit_post_delete_post">Delete this post</button>' in res.data
    auth.logout()

    # admin user
    auth.login(username="admin", password="prova")
    res = client.get("/user/visit_post/1")
    assert (
        b'<a class="visit_post_delete_post" href="/user/comment/1">Comment</a>'
        in res.data
    )
    assert b'class="visit_post_delete_post">Delete this post</button>' in res.data

    # no comments
    client.get("/user/delete_comment/1?cid=1")
    res = client.get("/user/visit_post/1")
    assert (
        b"<p>Nobody has commented this post yet, be the first one to do so.</p>"
        in res.data
    )


def test_delete_post(client: FlaskClient, auth: AuthActions, app: Flask):
    """Delete post should:
    - delete the post if the user has the right credentials and be redirected to '/', the status should be 302
    - responds 404 NOT FOUND to a GET request to a post that does not exists
    - refuse let you access the route if you are not a registerd user(admin)
    """
    # delete post as admin
    with app.app_context():
        db = get_db()
        entry = db.execute("SELECT * FROM posts WHERE (id = ?)", (1,)).fetchone()
        assert entry is not None
    auth.login(username="admin", password="prova")
    res = client.get("/user/delete_post/1")
    assert res.status_code == 302
    with app.app_context():
        db = get_db()
        entry = db.execute("SELECT * FROM posts WHERE (id = ?)", (1,)).fetchone()
        assert entry is None

    # 404
    res = client.get("/user/delete_post/1")
    assert res.status_code == 404

    # not registered, redirects to login
    auth.logout()
    res = client.get("/user/delete_post/2")
    assert res.status_code == 302
    assert res.headers["Location"] == '/auth/login'

    # registered but not admin, forbidden
    auth.login(username="prova", password="prova")
    res = client.get("/user/delete_post/2")
    assert res.status_code == 403


def test_comment_post(client: FlaskClient, auth: AuthActions):
    """Comment post should:
    - having a working navbar
    - refuse the connection if not logged in. 302 redirect to login.
    - grant access if you are registered. 200.
    - allow you to post a comment if you are registered through well formed POST request.
    - not allow you to post a comment if you are registered and don't provide a welll formed POST request.
    """

    check_navbar(client, auth)

    res = client.get("/user/comment/1")
    assert res.status_code == 302
    assert res.headers["Location"] == '/auth/login'

    auth.login(username="admin", password="prova")
    res = client.get("/user/comment/1")
    assert res.status_code == 200

    comment_body = 'Comment added in "test_comment_post" function.'
    client.post("/user/comment/1", data={"content": comment_body, "submit": "Comment"})

    res = client.get("/user/visit_post/1")
    assert b"Success, your comment has been posted." in res.data
    assert b"<p>Comment added in &#34;test_comment_post&#34; function.</p>" in res.data

    client.post("/user/comment/1", data={"submit": "Comment"})
    res = client.get("/user/visit_post/1")
    assert b"Success, your comment has been posted." not in res.data


def test_all_comments(client: FlaskClient, auth: AuthActions):
    """Comment post should:
    - having a working navbar
    - grant access to a get request if the post exists. 200.
    - 404 if the post doesn't exists.
    - show no comments and display a message if there are no comments to the specified post, asks you to login if you aren't.


    - asks you to comment if you are logged in.
    - asks you to delete a comment if you are the author of the comment or the author of the post.
    - not allow you to post a comment if you are registered and don't provide a welll formed POST request.
    """
    check_navbar(client, auth)

    res = client.get("/user/all_comments/1")
    assert res.status_code == 200

    # This doesn't exists
    res = client.get("/user/all_comments/100")
    assert res.status_code == 404

    client.get("/user/all_comments/3")
    res = client.get("/user/visit_post/3")
    assert (
        b"No comment to display so far, be the first one to leave a comment."
        in res.data
    )
    assert b'<a class="visit_post_delete_post" href="/auth/login">Login</a>' in res.data

    # Author of the post can delete the comment
    auth.login(username="admin", password="prova")
    res = client.get("/user/all_comments/1")
    assert (
        b'<a class="visit_post_delete_post" href="/user/comment/1">Comment</a>'
        in res.data
    )
    assert b"Delete comment" in res.data
    auth.logout()

    # Author of the comment can delete the comment
    auth.login(username="prova", password="prova")
    comment_body = 'Comment added in "test_all_comments" function.'
    client.post("/user/comment/1", data={"content": comment_body, "submit": "Comment"})
    res = client.get("/user/all_comments/1")
    assert b"Delete comment" in res.data
