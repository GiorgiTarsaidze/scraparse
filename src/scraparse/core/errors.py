class ScraparseError(Exception):
    """Base error for scraparse."""


class ConfigError(ScraparseError):
    pass


class LimitExceededError(ScraparseError):
    def __init__(self, limit_name: str, message: str, current: dict[str, float | int], limit: float | int):
        super().__init__(message)
        self.limit_name = limit_name
        self.current = current
        self.limit = limit


class FetchError(ScraparseError):
    pass


class AIError(ScraparseError):
    pass


class ValidationError(ScraparseError):
    pass
