import sqlite3
from flask import Flask, g, session
from flask.testing import FlaskClient
import pytest

from hjblog.db import get_db
from conftest import AuthActions


def test_register(client: FlaskClient, app: Flask):
    """Register route should:
    - respond with a 200 OK to a GET req while we are not logged in.
    - on POST with valid data redirect you to `/` and loggs you in.
    - prevent you from accessing '/auth/login' or other 'forbidden if logged in'
        pages if logged in.
    """
    assert client.get("/auth/register").status_code == 200
    # In order for this to work we have to disable all CSRF protection. Otherwise
    # I won't be able to replicate the correct cookie to send to the server
    res = client.post(
        "/auth/register",
        data={
            "username": "test",
            "email": "test@test.com",
            "password": "1111",
            "confirm_pass": "1111",
            "city": "rome",
            "submit": "Register",
        },
    )
    assert res.status_code == 302
    # redirected to index
    res.headers["Location"] == "/"
    # testing the name of the user is displayed on the navbar
    # assert b'>test</a>' in res.data
    # with open('logs/test_register_data.log', 'wb') as var:
    #     var.write(res.data)

    with client:
        # testing we are logged in after registering
        client.get("/")
        assert session["user_id"] == 3
        assert g.user["username"] == "test"

    # If we try and access `/auth/register` while we are
    # logged in we get redirected
    res = client.get("/auth/register")
    assert res.location == "/"

    with app.app_context():
        # testig the user have been registered after the post requet
        db = get_db()
        test_user: sqlite3.Row = db.execute(
            'SELECT * FROM users WHERE (username = "test")'
        ).fetchone()
        assert test_user["email"] == "test@test.com"


@pytest.mark.parametrize(
    ("username", "email", "password", "confirm_pass", "message"),
    (
        ("", "", "", "", b"Username is required."),
        ("aaa", "", "", "", b"Email is required."),
        (
            "a",
            "",
            "",
            "",
            b"Username has to be more then 3 characters long and less then 61 characters long.",
        ),
        (
            "a" * 100,
            "",
            "",
            "",
            b"Username has to be more then 3 characters long and less then 61 characters long.",
        ),
        ("aaa", "aaa@aaa.com", "", "", b"Password is required."),
        ("aaa", "aaa@aaacom", "", "", b"Your email is invalid."),
        ("aaa", "aaa@aaa.com", "111", "", b"Insert your password again."),
        ("aaa", "aaa@aaa.com", "111", "222", b"You typed in two different passwords."),
        (
            "prova",
            "prova@prova.com",
            "111",
            "111",
            b"The username prova has already been taken!",
        ),
        (
            "test",
            "prova@prova.com",
            "111",
            "111",
            b"The email prova@prova.com is already registered.",
        ),
    ),
)
def test_register_validate_input(
    client: FlaskClient,
    username: str,
    email: str,
    password: str,
    confirm_pass: str,
    message: str,
):
    """Checks if the validators work"""
    res = client.post(
        "/auth/register",
        data={
            "username": username,
            "email": email,
            "password": password,
            "confirm_pass": confirm_pass,
            "submit": "Register",
        },
    )

    assert message in res.data


def test_login(client: FlaskClient, auth: AuthActions):
    """Login route should:
    - respond with a 200 OK to a GET req while we are not logged in.
    - redirect to '/' after successfull login.
    - prevent you from accessing '/auth/login' or other 'forbidden if logged in'
        pages if logged in.
    """
    assert client.get("/auth/login").status_code == 200

    response = auth.login(username="prova", password="prova")
    assert response.headers["Location"] == "/"

    with client:
        client.get("/")
        assert session["user_id"] == 1
        assert g.user["username"] == "prova"

    # if we try access `/auth/login` while we are logged in we get redirected
    assert client.get("/auth/login").location == "/"


def test_logout(client: FlaskClient, auth):
    """Logout route should:
    - respond with a 302 OK to a GET req while you are logged in
    - redirect you to '/' after loggin out
    - prevent you from accessing '/auth/logut' or other 'forbidden if not logged in'
        pages if logged in.
    """
    auth.login(username="prova", password="prova")

    res = client.get("/auth/logout")
    assert res.status_code == 302
    assert res.location == "/"

    with client:
        client.get("/")
        assert session.get("user_id", None) is None
