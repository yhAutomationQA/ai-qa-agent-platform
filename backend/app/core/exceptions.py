from fastapi import HTTPException, status


class BaseAppException(HTTPException):
    def __init__(
        self,
        detail: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str | None = None,
    ):
        super().__init__(
            status_code=status_code,
            detail={"message": detail, "error_code": error_code},
        )


class NotFoundError(BaseAppException):
    def __init__(self, entity: str, entity_id: str | int):
        super().__init__(
            detail=f"{entity} with id '{entity_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
        )


class ValidationError(BaseAppException):
    def __init__(self, detail: str):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
        )


class AuthorizationError(BaseAppException):
    def __init__(self, detail: str = "Not authorized"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR",
        )


class AuthenticationError(BaseAppException):
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR",
        )


class RateLimitError(BaseAppException):
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_ERROR",
        )


class ServiceUnavailableError(BaseAppException):
    def __init__(self, service: str):
        super().__init__(
            detail=f"Service '{service}' is unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="SERVICE_UNAVAILABLE",
        )
