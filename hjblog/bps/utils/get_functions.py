import logging
from flask import request


def get_indexes(page_span: int, max_page: int) -> tuple[int, int, int]:
    """Returns the correct indexes that will be used to extract posts from
    the database: `index`(the current page), `prev_pages`(the pages before
    `index`), `next_pages`(the pages after `index`).
    This function needs to be called in a route that implement the method `GET`,
    an eventual `GET` variable called `index` needs to be passed, this will be the current
    page to display.
    The parameter `max_page` needs to be obtained by dividing the total amount of comments/posts by
    the number of comments/posts to be displayed on the document.
    """
    # IDEA: we may refactor this in a function that takes index instead of extracting the index variable from the request itself
    index = None

    try:
        index = int(request.args.get("index", None))
    except TypeError:
        index = None
    except Exception as e:
        logging.exception(e)
        index = None

    if index is None:
        index = 0
    if index < 0:
        index = 0
    if index > max_page:
        index = max_page
    prev_pages = index - page_span
    if prev_pages < 0:
        prev_pages = 0
    next_pages = index + page_span
    if next_pages > max_page:
        next_pages = max_page

    return index, prev_pages, next_pages


def get_offset(o: str | None) -> tuple[int, int]:
    """This function creates the necessary values for correct pagination.
    It checks whether the `o` parameter (representing a chunk/index of the data)
    has been passed correctly from the caller.

    The `offset` determines how many elements to skip when displaying results.
    Since 100 elements are loaded per request, the offset is `100 * o`.

    If `o` is not provided or is invalid, the function defaults both `o` and `offset` to 0,
    which ensures the default case."""
    if o is None:
        return 0, 0
    try:
        o = int(o)
    except TypeError:
        o = 0
    except Exception as e:
        logging.exception(e)
        o = 0
    if o < 0:
        o = 0
    offset = o * 100
    return o, offset
