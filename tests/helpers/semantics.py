from contextlib import contextmanager


@contextmanager
def assert_not_raises():
    """Context manager that does nothing.

    When an exception occurs, it will be allowed raise.  This is semantic
    sugar for the reader to know that the purpose of a line is to ensure that
    the line does not raise an exception.
    """
    yield
