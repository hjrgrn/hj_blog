import sys
import click
from flask import Flask

from .auxiliaries import get_admin_credencials
from .db import get_db

import logging


LS = """COMMANDS:
new-admin -> Adds a new admin account.
clear-admins -> Removes all the admin accounts from the database.
remove-one-admin -> Allows the user to select an admin to remove.
gen-posts -> Generates a random amount of posts to insert into the database for testing purpose.
gen-comments -> Generates a random amount of comments to insert into the database for testing purpose.
init-db -> Initializes the database, deleting all the data saved so far.
"""


@click.command("ls")
def display_commands():
    """Displays all the avaible commands."""
    click.echo(LS)


@click.command("new-admin")
def new_admin():
    """Adds a new admin account."""
    db = get_db()

    tup = get_admin_credencials()
    if tup is None:
        return
    (username, email, password_hash) = tup

    try:
        db.execute(
            "INSERT INTO users (username, email, hash_pass, is_admin) VALUES (?, ?, ?, ?)",
            (username, email, password_hash, True),
        )
        db.commit()
    except db.IntegrityError as e:
        print("Error: Couldn't add the new account becouse of: {}", e)
        return
    except Exception as e:
        logging.exception(e)
        raise e

    print(f'Success: New admin with username "{username}" added correctly.')


@click.command("clear-admins")
def clear_admins():
    """Removes all the admin accounts from the database."""
    db = get_db()
    admins = db.execute(
        "SELECT username, email FROM users WHERE (is_admin = TRUE)"
    ).fetchall()

    if len(admins) > 0:
        print("\nThis admins accounts will be removed:")
        for admin in admins:
            print(f'\t{admin["username"]} - {admin["email"]}')
    else:
        print("Currently there are no admin account.")
        return
    procede = input("\nProcede(y, N): ")
    if procede != "y":
        print("Procedure aborted.")
        return

    db.execute("DELETE FROM users WHERE (is_admin = TRUE)")
    db.commit()

    print("\nThese admin accounts have been removed:")
    for admin in admins:
        print(f'\t{admin["username"]}')


@click.command("remove-one-admin")
def remove_one_admin():
    """Allows the user to select an admin to
    remove.
    """
    # arrangement
    db = get_db()
    admins = []
    res = db.execute(
        "SELECT id, username, email FROM users WHERE (is_admin = TRUE)"
    ).fetchall()
    if len(res) == 0:
        print("Currently there are no admins.")
        return

    # get choice
    prompt = 'Select the admin you want to remove or type "0" to abort the procedure:\n[0]: Abort the procedure'
    index = 1
    for admin in res:
        prompt = prompt + f'\n[{index}]: {admin["username"]} - {admin["email"]}'
        admins.append((index, admin))
        index = index + 1

    choice = ask_for_int(prompt, index)
    if choice is None:
        print(
            "Error: an invalid value has been typed. Procedure aborted.",
            file=sys.stderr,
        )
        return
    # aborting the procedure
    elif choice == 0:
        print("Procedure aborted as required.")
        return

    # act
    for i in admins:
        if i[0] == choice:
            db.execute("DELETE FROM users WHERE (id = ?)", (i[1]["id"],))
            db.commit()
            print(f'Admin "{i[1]["username"]}" has been removed.')
            break


@click.command("gen-posts")
def generate_random_posts():
    """Generates a random amount of posts to insert into
    the database for testing purpose.
    """
    # we need an admin
    db = get_db()
    admin = db.execute("SELECT id FROM users WHERE (is_admin = true)").fetchone()
    if admin is None:
        print(
            'At least one admin is to be registered in order to execute this command, use the "new-admin" command.',
            file=sys.stderr,
        )
        return

    amount = ask_for_int(
        "How many post do you want me to generate?(max 100):\n>> ", 100
    )
    if amount is None:
        print(
            "Error: an invalid value has been typed. Procedure aborted.",
            file=sys.stderr,
        )
        return

    for i in range(0, amount):
        title = f"test-title-{i}"
        content = f"this is a test, content {i}."
        db.execute(
            "INSERT INTO posts (title, content, author_id) VALUES (?, ?, ?)",
            (title, content, admin["id"]),
        )

    db.commit()

    print(f"Procedure completed. {amount} posts were generated.")


@click.command("gen-comments")
def generate_random_comments():
    """Generates a random amount of comments to insert into
    the database for testing purpose.
    """
    db = get_db()

    admin = db.execute("SELECT id FROM users WHERE (is_admin = true)").fetchone()
    if admin is None:
        print(
            'At least one admin is to be registered in order to execute this command, user "new-admin" command.',
            file=sys.stderr,
        )
        return

    amount = ask_for_int(
        "How many comments do you want me to generate?(max 100):\n>> ", 100
    )
    if amount is None:
        print(
            "Error: an invalid value has been typed. Procedure aborted.",
            file=sys.stderr,
        )
        return

    some_posts_id = db.execute("SELECT id FROM posts LIMIT 10").fetchall()
    if not some_posts_id:
        print(
            'Currently there are no posts, you need to add a posts before commenting it, consider using the command "gen-posts".',
            file=sys.stderr,
        )
        return

    prompt = "Type the id of the post you want to add comments to, some valid id: "
    for post in some_posts_id:
        prompt = prompt + f' {post["id"]}'
    prompt = prompt + "\n>> "
    post_id = ask_for_int(prompt)
    if post_id is None:
        print("Invalid id, aborting.", file=sys.stderr)
        return

    post = db.execute(
        "SELECT id, title FROM posts WHERE (id = ?)", (post_id,)
    ).fetchone()
    if not post:
        print("Invalid id, aborting.", file=sys.stderr)
        return

    for i in range(0, amount):
        content = f"Dummie comment number {i}"
        try:
            db.execute(
                "INSERT INTO comments (post_id, content, author_id) VALUES (?, ?, ?)",
                (post["id"], content, admin["id"]),
            )
        except Exception as e:
            logging.exception(e)
            raise e
    try:
        db.commit()
    except Exception as e:
        logging.exception(e)
        raise e

    print(f'Success! Added {amount} comments to the post "{post["title"]}".')


def init_app(app: Flask):
    """Adds the click commands defined here
    to the application
    """
    app.cli.add_command(new_admin)
    app.cli.add_command(clear_admins)
    app.cli.add_command(remove_one_admin)
    app.cli.add_command(generate_random_posts)
    app.cli.add_command(generate_random_comments)
    app.cli.add_command(display_commands)


def ask_for_int(prompt: str, limit: int | None = None) -> int | None:
    """Helper function, asks for a positive int and returns it,
    if the int exceeds `limit` `limit` will be returned(if limit was provided), if the
    int is negative None is returned.
    Returns a positive int or None is it was unable to return a
    positive int.
    Unexpected Exceptions will be logged and will be raised.
    """
    amount = input(prompt)
    try:
        amount = int(amount)
    except ValueError as e:
        return None
    except Exception as e:
        logging.exception(e)
        raise e

    if limit:
        if amount > limit:
            amount = limit
    if amount < 0:
        return None

    return amount
