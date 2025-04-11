class ViewError(Exception):
    """Errors called inside View"""

    pass


class ViewTimeoutError(ViewError):
    """Errors when view timesout"""

    pass
