"""
Configurable mapper transforming WHO ICD-11 JSON entities into OAAS Ontology Schema documents.
"""

from typing import Any, Dict, List, Optional
import yaml
from pathlib import Path

from config.constants import MAPPING_YAML_PATH
from config.settings import settings
from models.ontology import OAASOntologyTerm
from transformer.normalizer import extract_label_value, normalize_list, normalize_text
from utils.logger import mapping_logger


class ICD11Mapper:
    """Transforms raw WHO ICD-11 API JSON entities into OAAS Ontology schema models."""

    def __init__(self, mapping_config_path: Optional[Path] = None):
        self.config_path = mapping_config_path or MAPPING_YAML_PATH
        self.rules = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load mapping rules from YAML configuration file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception as err:
                mapping_logger.warning(f"Failed to parse mapping YAML at {self.config_path}: {err}. Using built-in defaults.")
        return {}

    def map_entity(self, raw_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map a single raw WHO ICD-11 JSON dictionary to OAAS Ontology Schema dictionary.

        Args:
            raw_json: Raw JSON payload returned by WHO ICD-11 API.

        Returns:
            Dictionary matching the exact OAAS Ontology Schema.
        """
        uri = normalize_text(raw_json.get("@id") or raw_json.get("uri"))
        # Extract full entity ID path relative to linearization root /mms/
        if uri and "/mms/" in uri:
            entity_id = uri.split("/mms/")[-1].strip("/")
        elif uri:
            entity_id = uri.rstrip("/").split("/")[-1]
        else:
            entity_id = ""

        code = normalize_text(raw_json.get("code"))
        name = extract_label_value(raw_json.get("title"))

        if not name:
            name = f"Unnamed Entity ({code or entity_id})"

        definition = extract_label_value(raw_json.get("definition"))
        
        # Combine synonyms and index terms
        raw_syns = raw_json.get("synonym", [])
        raw_index = raw_json.get("indexTerm", [])
        combined_syns = normalize_list(raw_syns) + normalize_list(raw_index)
        
        seen_syns = set()
        synonyms = []
        for s in combined_syns:
            if s and s not in seen_syns:
                seen_syns.add(s)
                synonyms.append(s)

        includes = normalize_list(raw_json.get("inclusion"))
        type1_exclude = normalize_list(raw_json.get("exclusion"))
        
        # Populate ICD-11 related ID values in 'Term ID' per Lexicon requirements:
        # Format for 'Term ID': code | ICD11:code | entity_id | ICD11:entity_id
        # Example: 01 | ICD11:01 | 1435254666 | ICD11:1435254666
        term_id_list = []
        if code:
            term_id_list.append(code)
            term_id_list.append(f"ICD11:{code}")
        if entity_id:
            term_id_list.append(entity_id)
            term_id_list.append(f"ICD11:{entity_id}")

        term_id_list = list(dict.fromkeys(term_id_list))

        # hasDbXref is reserved for external database cross-references
        db_xref = []

        short_desc = extract_label_value(raw_json.get("codingNote"))
        long_desc = extract_label_value(raw_json.get("longDefinition"))

        # Human-openable WHO ICD-11 Browser URL (ensuring 2026-01 release version consistency)
        browser_url = normalize_text(raw_json.get("browserUrl", "")) or ""
        if "2024-01" in browser_url:
            browser_url = browser_url.replace("2024-01", "2026-01")
        elif not browser_url and entity_id:
            browser_url = f"https://icd.who.int/browse/2026-01/mms/en#{entity_id}"
        # Hierarchy fields (initially URIs/IDs, resolved to Concept Names in HierarchyGenerator)
        parents = normalize_list(raw_json.get("parent"))
        children = normalize_list(raw_json.get("child"))

        version = normalize_text(raw_json.get("release")) or f"ICD-11 {settings.icd11_release_id}"

        # Construct OAAS Ontology Term Pydantic Model
        term = OAASOntologyTerm(
            Name=name,
            ID="",
            Term_ID=term_id_list,
            URI=uri,
            BrowserUrl=browser_url,
            Synonyms=synonyms,
            Short_Description=short_desc,
            Long_Description=long_desc,
            Condition_Group="General",
            hasDbXref=db_xref,
            Definition=definition,
            Type_I_Exclude=type1_exclude,
            Type_II_Exclude=[],
            Includes=includes,
            Applicable_To=[],
            forMapping=True,
            mcXref=[],
            Version=version,
            PossiblePrefix="ICD11",
            superClassOf=children,
            subClassOf=parents,
        )


        return term.model_dump(by_alias=True)

    def map_batch(self, raw_entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Map a list of raw entities to OAAS schema dictionaries."""
        mapped = []
        for raw in raw_entities:
            try:
                mapped.append(self.map_entity(raw))
            except Exception as err:
                uri = raw.get("@id") or raw.get("uri")
                mapping_logger.error(f"Failed to map entity at URI '{uri}': {err}")
        return mapped
