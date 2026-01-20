"""Tracer-specific exceptions."""


class ValgrindNotFoundError(Exception):
    """Valgrind is not installed or not in PATH."""
    pass


class TracingError(Exception):
    """Error during trace collection."""
    pass
