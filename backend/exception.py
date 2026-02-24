class AppException(Exception):
    def __init__(self, error_code: str, message: str, status_code: int = 400):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code


class AuthenticationError(AppException):
    def __init__(self, message="Authentication failed"):
        super().__init__(
            error_code="AUTH_FAILED",
            message=message,
            status_code=401
        )


class AuthorizationError(AppException):
    def __init__(self, message="Not authorized"):
        super().__init__(
            error_code="NOT_AUTHORIZED",
            message=message,
            status_code=403
        )


class ValidationError(AppException):
    def __init__(self, message="Invalid request"):
        super().__init__(
            error_code="VALIDATION_ERROR",
            message=message,
            status_code=400
        )


class DatabaseError(AppException):
    def __init__(self, message="Database operation failed"):
        super().__init__(
            error_code="DATABASE_ERROR",
            message=message,
            status_code=500
        )
