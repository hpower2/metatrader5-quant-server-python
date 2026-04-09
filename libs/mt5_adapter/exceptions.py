class MT5AdapterError(Exception):
    """Base MT5 adapter error."""


class MT5RequestError(MT5AdapterError):
    """Raised when the remote API returns a non-success response."""


class MT5ResponseError(MT5AdapterError):
    """Raised when the remote API payload is invalid."""


class MT5UnavailableError(MT5AdapterError):
    """Raised when the remote health check indicates the provider is unavailable."""

