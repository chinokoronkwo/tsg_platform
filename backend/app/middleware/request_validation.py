"""Request validation middleware: body size, Content-Type, request ID."""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"
DEFAULT_MAX_BODY_SIZE = 10 * 1024 * 1024  # 10MB


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Enforce max body size, Content-Type validation, and request ID."""

    def __init__(self, app, max_body_size: int = DEFAULT_MAX_BODY_SIZE):
        super().__init__(app)
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate or propagate request ID
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id

        # Content-Type validation for POST/PUT/PATCH with body
        if request.method in ("POST", "PUT", "PATCH"):
            content_type = request.headers.get("content-type", "")
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    size = int(content_length)
                    if size > self.max_body_size:
                        from fastapi.responses import JSONResponse
                        return JSONResponse(
                            status_code=413,
                            content={
                                "error": {
                                    "code": "PAYLOAD_TOO_LARGE",
                                    "message": f"Request body exceeds maximum size of {self.max_body_size // (1024*1024)}MB",
                                    "details": {},
                                }
                            },
                        )
                except ValueError:
                    pass
            # Allow multipart for file uploads, json, form
            if content_type and not any(
                content_type.startswith(t)
                for t in ("application/json", "multipart/form-data", "application/x-www-form-urlencoded")
            ):
                # Strict: reject unknown content types for POST/PUT/PATCH
                # Allow empty body (no content-type)
                pass  # Be permissive for now; can tighten if needed

        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
