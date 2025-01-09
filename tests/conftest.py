import os
import sqlite3
import tempfile
from flask import Flask
from flask.testing import FlaskCliRunner, FlaskClient

import pytest
from werkzeug.test import TestResponse

from hjblog import create
from hjblog.db import get_db


with open(os.path.join(os.path.dirname(__file__), "data.sql"), "rb") as var:
    data_sql = var.read().decode("utf-8")


@pytest.fixture
def app():
    """Fixture that returns an app instance configured
    for testsing.
    """
    db_fd, db_path = tempfile.mkstemp()
    upload_dir = tempfile.TemporaryDirectory()

    app = create(
        test_config={
            "TESTING": True,
            "SECRET_KEY": "test",
            "DATABASE": db_path,
            "UPLOAD_DIR": upload_dir.name,
            # This is necessary for unit test, otherwise I wan't be able to
            # send the correct cookie back when testing the forms
            "WTF_CSRF_ENABLED": False,
        }
    )

    with app.app_context():
        db = get_db()
        db.executescript(data_sql)

    yield app

    os.close(db_fd)
    os.unlink(db_path)
    upload_dir.cleanup()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


@pytest.fixture
def runner(app: Flask) -> FlaskCliRunner:
    return app.test_cli_runner()


class AuthActions:
    """
    Class that rappresents a POST request to `bp.auth.login`
    and a GET request to `bp.auth.logout`.
    """

    def __init__(self, client: FlaskClient, app: Flask):
        self._client = client
        self._app = app

    def login(self, username="test", password="test") -> TestResponse:
        test_user: sqlite3.Row = None
        with self._app.app_context():
            db = get_db()
            test_user = db.execute(
                "SELECT * FROM users WHERE (username = ?)", (username,)
            ).fetchone()
        self._client.post(
            "/auth/login", data={"username": username, "submit": "Sign in"}
        )
        verification_url = f"/auth/authenticate/{test_user['id']}"
        return self._client.post(
            verification_url, data={"password": password, "submit": "Submit"}
        )

    def logout(self):
        return self._client.get("/auth/logout")


@pytest.fixture
def auth(client: FlaskClient, app: Flask) -> AuthActions:
    """Function that returns the class that encloses the logic for
    a POST request to `bp.auth.login` and a GET request to `bp.auth.logout`.
    """
    return AuthActions(client, app)
