"""
Mapper transforming WHO ICD-10 API JSON entities into OAAS Ontology Schema documents.
"""

from typing import Any, Dict, List, Optional
from models.ontology import OAASOntologyTerm
from transformer.normalizer import extract_label_value, normalize_list, normalize_text
from utils.logger import mapping_logger


class ICD10Mapper:
    """Transforms raw WHO ICD-10 API JSON entities into OAAS Ontology schema models."""

    def map_entity(self, raw_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map a single raw WHO ICD-10 JSON dictionary to OAAS Ontology Schema dictionary.

        Args:
            raw_json: Raw JSON payload returned by WHO ICD-10 API.

        Returns:
            Dictionary matching the exact OAAS Ontology Schema.
        """
        uri = normalize_text(raw_json.get("@id") or raw_json.get("uri"))
        
        # Extract entity ID relative to ICD-10 release path
        if uri and "/release/10/2019/" in uri:
            entity_id = uri.split("/release/10/2019/")[-1].strip("/")
        elif uri:
            entity_id = uri.rstrip("/").split("/")[-1]
        else:
            entity_id = ""

        code = normalize_text(raw_json.get("code"))
        name = extract_label_value(raw_json.get("title"))

        if not name:
            name = f"Unnamed ICD-10 Entity ({code or entity_id})"

        definition = extract_label_value(raw_json.get("definition"))

        # Synonyms and index terms
        raw_synonyms = raw_json.get("synonym", []) or []
        raw_index_terms = raw_json.get("indexTerm", []) or []
        synonyms = normalize_list(raw_synonyms + raw_index_terms)

        # Exclusions and inclusions
        raw_exclusions = raw_json.get("exclusion", []) or []
        exclusions = normalize_list(raw_exclusions)

        raw_inclusions = raw_json.get("inclusion", []) or []
        inclusions = normalize_list(raw_inclusions)

        # Superclass / Subclass URIs
        parents = normalize_list(raw_json.get("parent", []))
        children = normalize_list(raw_json.get("child", []))

        # Build Term ID list: [code, ICD10:code, entity_id, ICD10:entity_id]
        term_id_list = []
        if code:
            term_id_list.append(code)
            term_id_list.append(f"ICD10:{code}")
        if entity_id:
            term_id_list.append(entity_id)
            term_id_list.append(f"ICD10:{entity_id}")

        # Remove duplicates while maintaining insertion order
        seen = set()
        dedup_term_ids = []
        for tid in term_id_list:
            if tid and tid not in seen:
                seen.add(tid)
                dedup_term_ids.append(tid)

        # Browser URL construction for 2019 ICD-10 release
        if code:
            browser_url = f"https://icd.who.int/browse10/2019/en#{code}"
        elif entity_id:
            browser_url = f"https://icd.who.int/browse10/2019/en#{entity_id}"
        else:
            browser_url = uri

        # Determine forMapping status (ICD-10 coded terms or leaf concepts are forMapping=True)
        is_class = raw_json.get("isClassified", True)
        is_header = bool(raw_json.get("child")) and not code
        for_mapping = not is_header

        term_model = OAASOntologyTerm(
            Name=name,
            ID="",  # Blank for Lexicon sequence auto-generation
            Term_ID=dedup_term_ids,
            URI=uri,
            BrowserUrl=browser_url,
            Synonyms=synonyms,
            Short_Description="",
            Long_Description="",
            Condition_Group="",  # Propagated in hierarchy step
            hasDbXref=[],
            Definition=definition,
            Type_I_Exclude=exclusions,
            Type_II_Exclude=[],
            Includes=inclusions,
            Applicable_To=[],
            forMapping=for_mapping,
            mcXref=[],
            Version="ICD-10 2019",
            PossiblePrefix="ICD10",
            superClassOf=children,
            subClassOf=parents,
        )

        return term_model.model_dump(by_alias=True)

    def map_batch(self, raw_documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Map a batch of raw ICD-10 documents."""
        mapped = []
        for doc in raw_documents:
            raw_payload = doc.get("raw_json", doc)
            mapped.append(self.map_entity(raw_payload))
        return mapped
