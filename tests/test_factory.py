from hjblog import create


def test_create():
    """Just checks if we are in testing mode or not."""
    assert not create().testing
    assert create({"TESTING": True}).testing
