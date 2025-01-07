import sqlite3
from flask.testing import FlaskCliRunner, FlaskClient
import pytest

from hjblog.db import get_db


def test_get_close_db(client: FlaskClient):
    """We test that in the same `app_context` the same
    connection to the database is returned.
    We make sure that when `app_context` is dropped the connection
    to the database is closed, so trying to interact with it will
    raise `sqlite3.ProgrammingError`, 'closed' will be in `error.value`.
    """
    with client.application.test_request_context():
        db = get_db()
        assert db is get_db()

    with pytest.raises(sqlite3.ProgrammingError) as e:
        db.execute("SELECT 1")

    assert "closed" in str(e.value)


def test_init_db_command(runner: FlaskCliRunner, monkeypatch):
    """Pytest’s monkeypatch fixture replaces the `init_db`
    function with one that records that it’s been called, but
    the effect will be the same, this is done by `.setattr`.
    With the runner we invoke `init_db_command` that now encloses
    `fake_init_db`, not `init_db`, so we will be able to see if
    `Recorded.called` has been set to True.
    """

    class Recorder(object):
        called = False

    def fake_init_db():
        Recorder.called = True

    monkeypatch.setattr("hjblog.db.init_db", fake_init_db)
    with runner.app.test_request_context():
        result = runner.invoke(args=["init-db"])
    assert "Database initialized." in result.output
    assert Recorder.called
