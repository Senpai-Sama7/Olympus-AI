from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class Event(BaseModel):
    id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    type: str
    data: Dict[str, Any]


class Fact(BaseModel):
    id: str
    source: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Embedding(BaseModel):
    id: str
    fact_id: str
    vector: List[float]
    model: str


class Entity(BaseModel):
    id: str
    name: str
    type: str


class Relation(BaseModel):
    id: str
    source_entity_id: str
    target_entity_id: str
    type: str


class CacheItem(BaseModel):
    key: str
    value: Any
    expires_at: Optional[datetime] = None
