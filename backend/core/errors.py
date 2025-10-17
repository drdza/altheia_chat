# app/core/errors.py

from fastapi import HTTPException, status

class Unauthorized(HTTPException):
    def __init__(self, detail="Unauthorized"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

class BadGateway(HTTPException):
    def __init__(self, detail="Upstream error"):
        super().__init__(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)
