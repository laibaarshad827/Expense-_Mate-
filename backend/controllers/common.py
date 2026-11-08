"""Small helpers that build the (success, message, data) responses."""


def ok(message, data=None):
    return True, message, data


def fail(message):
    return False, message, None