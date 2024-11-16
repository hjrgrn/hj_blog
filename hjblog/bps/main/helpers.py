from datetime import datetime
from sqlite3 import Connection, Cursor
from hjblog.db import get_db


def get_posts(
    index: int,
    max_per_page: int,
    author_id: int | None = None,
    offset: int | None = None,
) -> list[dict[str, str | str, datetime]]:
    """Given specific parameters returns the correct posts that will be displayed
    inside a page, if `author_id` is passed only posts relative to that specific
    author will be taken into consideration, if `offset` is passed first `offset`
    results will be skipped.
    """
    db: Connection = get_db()
    batch: Cursor = None
    posts = None

    if author_id:
        if offset:
            batch = db.execute(
                "SELECT users.username, posts.id, posts.title, posts.content, posts.path_to_file, posts.posted FROM posts JOIN users ON (users.id = posts.author_id) WHERE (posts.author_id = ?) ORDER BY posts.posted DESC, posts.id DESC LIMIT (100) OFFSET (?)",
                (author_id, offset),
            )
        else:
            batch = db.execute(
                "SELECT users.username, posts.id, posts.title, posts.content, posts.path_to_file, posts.posted FROM posts JOIN users ON (users.id = posts.author_id) WHERE (posts.author_id = ?) ORDER BY posts.posted DESC, posts.id DESC LIMIT 100",
                (author_id,),
            )
    else:
        if offset:
            batch = db.execute(
                "SELECT users.username, posts.id, posts.title, posts.content, posts.path_to_file, posts.posted FROM posts JOIN users ON (users.id = posts.author_id) ORDER BY posts.posted DESC, posts.id DESC LIMIT (100) OFFSET (?)",
                (offset,),
            )
        else:
            batch = db.execute(
                "SELECT users.username, posts.id, posts.title, posts.content, posts.path_to_file, posts.posted FROM posts JOIN users ON (users.id = posts.author_id) ORDER BY posts.posted DESC, posts.id DESC LIMIT 100"
            )
    for _ in range(0, index + 1):
        posts = batch.fetchmany(max_per_page)
        if len(posts) == 0:
            break

    return posts
