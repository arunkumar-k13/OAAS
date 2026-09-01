"""
Pydantic data models for the OAAS Ontology Schema.
"""

from typing import List, Optional, Union
from pydantic import BaseModel, Field


class OAASOntologyTerm(BaseModel):
    """Represents a single ontology term in the OAAS schema."""

    Name: str = Field(..., description="Primary label or title of the term")
    ID: str = Field(default="", description="Unique identifier within OAAS")
    Term_ID: Union[str, List[str]] = Field(default_factory=list, alias="Term ID", description="Short entity code / term codes")
    URI: str = Field(default="", description="Canonical WHO ICD-11 URI")
    BrowserUrl: str = Field(default="", alias="BrowserUrl", description="Human-openable WHO ICD-11 Browser URL")
    Synonyms: List[str] = Field(default_factory=list, description="Alternative names or synonyms")
    Short_Description: str = Field(default="", alias="Short Description", description="Brief description or coding note")
    Long_Description: str = Field(default="", alias="Long Description", description="Extended description")
    Condition_Group: str = Field(default="General", alias="Condition Group", description="Category or condition grouping")
    hasDbXref: List[str] = Field(default_factory=list, description="Cross-database references (e.g. UMLS, SNOMED)")
    Definition: str = Field(default="", description="Formal WHO textual definition")
    Type_I_Exclude: List[str] = Field(default_factory=list, alias="Type I Exclude", description="Type I exclusion terms")
    Type_II_Exclude: List[str] = Field(default_factory=list, alias="Type II Exclude", description="Type II exclusion terms")
    Includes: List[str] = Field(default_factory=list, description="Inclusion terms or criteria")
    Applicable_To: List[str] = Field(default_factory=list, alias="Applicable To", description="Applicability scope")
    forMapping: bool = Field(default=True, description="Flag indicating if available for mapping")
    mcXref: List[str] = Field(default_factory=list, description="Medical/clinical cross-references")
    Version: str = Field(default="ICD-11 2024-01", description="ICD-11 linearization release version")
    PossiblePrefix: str = Field(default="ICD11", description="Prefix code for OAAS identification")

    # Hierarchy fields
    superClassOf: List[str] = Field(default_factory=list, description="Child concept identifiers")
    subClassOf: List[str] = Field(default_factory=list, description="Parent concept identifiers")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }
