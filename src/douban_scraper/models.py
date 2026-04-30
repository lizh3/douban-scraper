from pathlib import Path

from pydantic import BaseModel, ConfigDict


class FrodoSubject(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    title: str
    url: str
    cover: str | None = None
    rating: dict
    type: str
    subtype: str | None = None
    year: str | None = None
    card_subtitle: str | None = None


class FrodoInterest(BaseModel):
    model_config = ConfigDict(extra="allow")

    comment: str | None = None
    rating: dict | None = None
    create_time: str
    subject: FrodoSubject
    status: str
    tags: list[str]


class FrodoInterestsResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    count: int
    start: int
    total: int
    interests: list[FrodoInterest]


class RexxBroadcast(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    text: str
    created_at: str
    comments_count: int
    likes_count: int
    subject: dict | None = None
    reshared_status: dict | None = None


class RexxBroadcastsResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    items: list[RexxBroadcast]
    count: int
    total: int


class ExportConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    user_id: str
    types: list[str]
    status: str
    output_dir: Path
    cookie: str | None = None
    delay: float
    max_items: int
    force: bool
    api_key: str
    api_secret: str
