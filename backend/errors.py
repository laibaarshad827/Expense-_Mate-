"""Errors raised by the service layer."""


class ServiceError(Exception):
    """A business rule was broken (e.g. 'User not found.').

    The message is written for the end user: the controller turns it into the
    (False, message, None) response that the screens already understand.
    """