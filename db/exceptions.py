class BusinessException(Exception):  
    """Expected, data-driven failure — e.g. invoice already posted."""

class ApplicationException(Exception):
    """Unexpected, system-driven failure — e.g. database connection error."""
