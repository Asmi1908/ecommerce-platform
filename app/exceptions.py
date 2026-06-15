from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

def validation_exception_handler(request : Request, exc : RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append({
            "field":"->".join(str(x) for x in error["loc"]),
            "message": error["msg"]
        })
    return JSONResponse(
        satus_code = 422,
        content = {"detail": "Validation error","errors":errors}
    )
async def general_exception_handler(request: Request, exc : Exception):
    return JSONResponse(
        satus_code = 500,
        content = {"detail": "Internal Server error","errors":str(exc)}
    )