"""
Pydantic data models for raw WHO ICD-11 entities.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WHOTextElement(BaseModel):
    """Represents multi-language text elements returned by WHO API."""
    label: str = Field(default="", alias="@value")
    lang: str = Field(default="en", alias="@language")


class WHOEntity(BaseModel):
    """Raw entity payload structure from WHO ICD-11 API."""
    id: str = Field(default="", alias="@id")
    title: Optional[Dict[str, Any]] = None
    definition: Optional[Dict[str, Any]] = None
    code: Optional[str] = None
    parent: List[str] = Field(default_factory=list)
    child: List[str] = Field(default_factory=list)
    synonym: List[Dict[str, Any]] = Field(default_factory=list)
    inclusion: List[Dict[str, Any]] = Field(default_factory=list)
    exclusion: List[Dict[str, Any]] = Field(default_factory=list)
    browserUrl: Optional[str] = None
    release: Optional[str] = None

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }
