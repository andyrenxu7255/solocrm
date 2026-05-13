class NotFoundError(Exception):
    def __init__(self, entity: str, identifier: str | None = None) -> None:
        detail = f"{entity} not found"
        if identifier:
            detail = f"{entity} with id={identifier} not found"
        super().__init__(detail)
        self.entity = entity
        self.identifier = identifier


class ValidationError(Exception):
    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field


class ExternalServiceError(Exception):
    def __init__(self, service: str, detail: str) -> None:
        super().__init__(f"{service} error: {detail}")
        self.service = service
        self.detail = detail
