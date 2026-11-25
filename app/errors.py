"""Application errors. No web-framework imports: any layer may raise these."""


class AppError(Exception):
    status = 500
    title = "Application error"
    code = "app_error"

    def __init__(self, detail=None, errors=None):
        self.detail = detail or self.title
        self.errors = errors or []
        super().__init__(self.detail)


class ValidationFailed(AppError):
    status = 422
    title = "Validation failed"
    code = "validation_failed"


class NotFound(AppError):
    status = 404
    title = "Resource not found"
    code = "not_found"


class Conflict(AppError):
    status = 409
    title = "Request conflicts with current state"
    code = "conflict"
