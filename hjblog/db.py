import os
import sqlite3

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
    """If a connection to the database is present
    in `g`, it will be popped and then closed.
    NOTE: `e` is necessary.
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
    profile_pics_dir = os.path.join(current_app.root_path, "static/profile_pics")
    for file_name in os.listdir(profile_pics_dir):
        file = os.path.join(profile_pics_dir, file_name)
        try:
            os.remove(file)
        except (FileNotFoundError, PermissionError) as e:
            click.echo(message=f"Failed to remove: {file}\nBecouse: {e}", err=True)
        except Exception as e:
            click.echo(
                message=f"Unexpected Exception occurred.\nFailed to remove: {file}\nBecouse: {e}",
                err=True,
            )


@click.command("init-db")
def init_db_command():
    """Defines a command that will
    call `init_db` function, the command will be
    `flask --app hjblog:create --debug init-db`.
    """
    clear_old_files()
    res = init_db()
    if isinstance(res, Exception):
        click.echo(message=f"Failed to initialize the database:\n{res}", err=True)
    else:
        click.echo("Database initialized.")


def init_app(app: Flask):
    """Takes an instance of flask and append to it
    the command that we have specified with
    `init_db_command`.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
