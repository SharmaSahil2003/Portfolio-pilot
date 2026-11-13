from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field, model_validator


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class Experience(BaseModel):
    company: str = ""
    role: str = ""
    period: str = ""


class Project(BaseModel):
    name: str = ""
    description: str = ""
    stack: list[str] = Field(default_factory=list)


class Profile(BaseModel):
    name: str = ""
    headline: str = ""
    email: str = ""
    location: str = ""
    about: str = ""
    skills: list[str] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def replace_null_values_with_defaults(cls, value):
        # Resume extraction may return JSON null for facts that were not found.
        # Treat those as missing profile fields instead of rejecting generation.
        if not isinstance(value, dict):
            return value
        normalized = value.copy()
        for field in ("name", "headline", "email", "location", "about"):
            if normalized.get(field) is None:
                normalized[field] = ""
        for field in ("skills", "experience", "projects"):
            if normalized.get(field) is None:
                normalized[field] = []
        return normalized


class GenerationRequest(BaseModel):
    mode: Literal["sync", "page", "workspace"]
    page: str | None = None


class VariableDefinition(BaseModel):
    key: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z_][A-Za-z0-9_.-]*$")
    description: str = Field(min_length=1, max_length=500)
    sample_json: Any | None = None


class VariableEntry(VariableDefinition):
    value: Any = None


class VariableGenerationRequest(BaseModel):
    definitions: list[VariableDefinition] = Field(min_length=1, max_length=100)


class VariableUpdateRequest(BaseModel):
    variables: list[VariableEntry] = Field(max_length=100)


class DatabaseConnectionRequest(BaseModel):
    engine: Literal["postgresql", "mysql"]
    host: str = Field(min_length=1, max_length=253)
    port: int = Field(gt=0, le=65535)
    database: str = Field(min_length=1, max_length=128)
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(default="", max_length=512)
    schema: str | None = Field(default=None, max_length=128)
    table: str = Field(min_length=1, max_length=128)
    key_column: str = Field(min_length=1, max_length=128)
    response_column: str = Field(min_length=1, max_length=128)
    description_column: str = Field(min_length=1, max_length=128)
    version_column: str = Field(min_length=1, max_length=128)
    ssl: bool = False


class DatabaseProposalRequest(BaseModel):
    mode: Literal["sync", "page"]
    expected_version: str | int | None = None
    records: list[dict[str, Any]] = Field(min_length=1, max_length=100)


class DatabasePublishRequest(BaseModel):
    mode: Literal["sync", "page"]
    expected_version: str | int | None = None
    records: list[dict[str, Any]] = Field(min_length=1, max_length=100)


class GenerationResponse(BaseModel):
    id: str
    status: str
    message: str
    version: dict


class VersionOut(BaseModel):
    id: str
    label: str
    mode: str
    createdAt: str
    status: str
    changes: list[str]
    previewUrl: str | None = None
    versionNumber: int | None = None
