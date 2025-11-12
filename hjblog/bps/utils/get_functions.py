import logging
from flask import request


def get_indexes(page_span: int, max_page: int) -> tuple[int, int, int]:
    """Returns the correct indexes for extracting comments/posts from the database:
    - `index`: the current page (from the GET parameter)
    - `prev_pages`: list of pages before the current one
    - `next_pages`: list of pages after the current one

    This function should be called in a GET route that accepts an optional `index` parameter,
    representing the current page to display. If not provided, it will default to 0.

    The `max_page` parameter must be calculated by dividing the total number of
    comments/posts by the number of comments/posts to display per page (rounded up
    to the nearest integer).
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
