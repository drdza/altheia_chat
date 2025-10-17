#app/models/schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional, Any

class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    chat_id: str

class RephraseRequest(BaseModel):
    text: str
    style: str | None = None

class DocChunk(BaseModel):
    doc_id: str
    chunk_id: str
    text: str
    metadata: dict[str, Any] | None = None

class IngestRequest(BaseModel):
    namespace: str = "default"
    documents: List[DocChunk]

class UpsertRequest(BaseModel):
    namespace: str = "default"
    chunks: List[DocChunk]

class DeleteRequest(BaseModel):
    namespace: str = "default"
    doc_ids: List[str]


# ---- RESPONSES ----
class ChatResponse(BaseModel):
    answer: str

class RephraseResponse(BaseModel):
    rephrased: str    

class StatusResponse(BaseModel):
    status: str
    message: str

class ResetResponse(BaseModel):
    status: str
    message: str
    detail: Optional[str] = None

class IngestResponse(BaseModel):
    ingested: int

class UpsertResponse(BaseModel):
    upserted: int

class DeleteResponse(BaseModel):
    deleted_doc_ids: List[str]

class IngestRawResponse(BaseModel):
    doc_id: str
    chunks: int

class IngestFileResponse(BaseModel):
    doc_id: str
    chunks: int

class GenericCountResponse(BaseModel):
    ingested: int

class FileIngestResponse(BaseModel):
    doc_id: str
    chunks: int

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"    