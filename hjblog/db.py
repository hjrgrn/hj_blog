import os
import sqlite3
from datetime import datetime

from flask import g, current_app, Flask
import click


def get_db() -> sqlite3.Connection:
    """Checks if `g` object contains a connection to
    the database, if it does it will be returned, otherwise
    a new connection will be enstablished and then returned.
    """
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"], detect_types=sqlite3.PARSE_DECLTYPES
        )

        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(__e__=None):
    """If a database connection exists in `g`, it will be removed and closed.
    Note: The `e` parameter is required for compatibility with teardown handlers.
    """
    db: sqlite3.Connection = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None | Exception:
    """Initializes the database."""
    db = get_db()

    try:
        with current_app.open_resource("schema.sql") as var:
            db.executescript(var.read().decode("utf-8"))
    except (FileNotFoundError, PermissionError) as e:
        # File related Exceptions
        return e
    except sqlite3.Error as e:
        # sqlite3 related Exceptions
        return e
    except Exception as e:
        # Unexpected behaviour
        return e


def clear_old_files():
    """Clears old files, use it before initializing a new database"""
    profile_pics_dir = current_app.config["UPLOAD_DIR"]
    for file_name in os.listdir(profile_pics_dir):
        file = os.path.join(profile_pics_dir, file_name)
        try:
            # NOTE: Assumes `file` is not a directory. If it is, an error will be raised.
            os.remove(file)
        except (FileNotFoundError, PermissionError) as e:
            click.echo(message=f"Could not remove: {file}\nReason: {e}", err=True)
        except IsADirectoryError as e:
            click.echo(
                message=f"Could not remove: {file}\nReason: {e}\nThis directory should contain only image files.",
                err=True,
            )
        except Exception as e:
            click.echo(
                message=f"Unexpected Exception occurred.\nCould not remove: {file}\nReason: {e}",
                err=True,
            )


@click.command("init-db")
def init_db_command():
    """Defines a CLI command that initializes the database. Can be invoked via:
    `flask --app hjblog:create --debug init-db`.
    """
    clear_old_files()
    res = init_db()
    if isinstance(res, Exception):
        click.echo(message=f"Failed to initialize the database:\n{res}", err=True)
    else:
        click.echo("Database initialized.")


def init_app(app: Flask):
    """Takes a Flask instance and appends to it
    the command specified by `init_db_command`.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)


sqlite3.register_converter("timestamp", lambda v: datetime.fromisoformat(v.decode()))
