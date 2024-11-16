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
    #IDEA: we may refactor this in a function that takes index instead of extracting the index variable from the request itself
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
    """This function is used to create the values necessaries for
    creating the correct pagination. It checks if the `o` variable has been passed
    correctly to the caller function, `o` represent a chunk of the total amount of elements,
    `offset` are the elements that will be skipped for the display:
    100 element are loaded per run, meaning that if we are at
    chunk 2(the third one) we need to skip the first `offset` * 2
    (the value of `o`) elements.
    If `o` wasn't passed or the value has been provided incorrectly a default
    value of 0 (which is functional) is passed
    for both `o` and `offset`.
    """
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
