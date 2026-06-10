from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    friendly_error = []
    for error_details in exc.errors():
        where_it_is = "->".join(str(part) for part in error_details["loc"])
        what_went_wrong = error_details["msg"]
        friendly_error.append({"field": where_it_is, "message": what_went_wrong})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"validation_issues": friendly_error},
    )
