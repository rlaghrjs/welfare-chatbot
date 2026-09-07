from fastapi import Request
from fastapi.responses import JSONResponse

from app.services.welfare_api_common import WelfareAPIError


async def welfare_api_error_handler(request: Request, exc: WelfareAPIError):
    return JSONResponse(status_code=502, content={"detail": str(exc)})
