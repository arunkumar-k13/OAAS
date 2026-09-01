"""
LOINC 2026 Mapper and Schema Transformer.
Transforms raw LOINC records into Lexicon-ready ontology schema.
Groups by LONG_COMMON_NAME (Name) to guarantee zero duplicate name import errors.
"""

import re
from typing import Any, Dict, List
from utils.logger import mapping_logger


# Map CLASSTYPE numeric codes to human-readable labels
CLASSTYPE_MAP = {
    "1": "Laboratory",
    "2": "Clinical",
    "3": "Claims Attachment",
    "4": "Survey",
}


class LOINCMapper:
    """Mapper for Regenstrief LOINC 2026 Observation Codes to Lexicon schema."""

    def transform_batch(self, raw_documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform raw LOINC documents into mapped Lexicon schemas grouped by Name.
        Deduplication: Groups by LONG_COMMON_NAME and pipe-merges all distinct attribute values.
        """
        mapping_logger.info(f"Transforming {len(raw_documents)} raw LOINC records...")

        grouped = {}

        for doc in raw_documents:
            loinc_num = str(doc.get("loinc_num") or "").strip()
            name = str(doc.get("long_common_name") or "").strip()

            # Use LOINC_NUM as fallback Name if LONG_COMMON_NAME is empty
            if not name:
                name = loinc_num
            if not name:
                continue

            if name not in grouped:
                grouped[name] = {
                    "Name": name,
                    "ID": "",  # Blank for Lexicon auto-generation
                    "Term ID": [],
                    "URI": [],
                    "Component": [],
                    "Property": [],
                    "Time Aspect": [],
                    "System (Specimen)": [],
                    "Scale Type": [],
                    "Method Type": [],
                    "Class": [],
                    "Class Type": [],
                    "Status": [],
                    "Short Name": [],
                    "Consumer Name": [],
                    "Order/Observation": [],
                    "Synonyms": [],
                    "Long Description": [],
                    "Units Required": [],
                    "Version": "LOINC 2026",
                    "mcXref": "",
                    "forMapping": "True",
                    "hasDbXref": "",
                    "PossiblePrefix": "LOINC",
                    "superClassOf": [],
                    "subClassOf": [],
                }

            entry = grouped[name]

            # Term ID: LOINC_NUM
            if loinc_num:
                term_id_str = f"{loinc_num}|LOINC:{loinc_num}"
                if term_id_str not in entry["Term ID"]:
                    entry["Term ID"].append(term_id_str)

                # URI
                uri_str = f"https://loinc.org/{loinc_num}"
                if uri_str not in entry["URI"]:
                    entry["URI"].append(uri_str)

            # Map fields
            self._append_unique(entry, "Component", doc.get("component"))
            self._append_unique(entry, "Property", doc.get("property"))
            self._append_unique(entry, "Time Aspect", doc.get("time_aspct"))
            self._append_unique(entry, "System (Specimen)", doc.get("system"))
            self._append_unique(entry, "Scale Type", doc.get("scale_typ"))
            self._append_unique(entry, "Method Type", doc.get("method_typ"))
            self._append_unique(entry, "Class", doc.get("class"))
            self._append_unique(entry, "Status", doc.get("status"))
            self._append_unique(entry, "Short Name", doc.get("shortname"))
            self._append_unique(entry, "Consumer Name", doc.get("consumer_name"))
            self._append_unique(entry, "Order/Observation", doc.get("order_obs"))
            self._append_unique(entry, "Units Required", doc.get("units_required"))

            # Class Type: numeric → human-readable
            classtype_raw = str(doc.get("classtype") or "").strip()
            classtype_label = CLASSTYPE_MAP.get(classtype_raw, classtype_raw)
            self._append_unique(entry, "Class Type", classtype_label)

            # Definition → Long Description
            self._append_unique(entry, "Long Description", doc.get("definition"))

            # Related Names → Synonyms (semicolon-separated in original)
            related = doc.get("related_names") or ""
            if related:
                for syn in related.split(";"):
                    syn_clean = syn.strip()
                    if syn_clean and syn_clean not in entry["Synonyms"]:
                        entry["Synonyms"].append(syn_clean)

        # Clean and format pipe-joined strings
        transformed_terms = []
        for name, entry in grouped.items():
            cleaned_term = {}
            for k, v in entry.items():
                if isinstance(v, list):
                    clean_items = []
                    for item in v:
                        if item and str(item).strip():
                            parts = [p.strip() for p in re.split(r"\|+", str(item)) if p.strip()]
                            for p in parts:
                                if p not in clean_items:
                                    clean_items.append(p)
                    cleaned_term[k] = "|".join(clean_items)
                else:
                    cleaned_term[k] = str(v).strip()
            transformed_terms.append(cleaned_term)

        mapping_logger.info(f"Transformed into {len(transformed_terms)} clean, unique LOINC terms.")
        return transformed_terms

    @staticmethod
    def _append_unique(entry: Dict, field: str, value) -> None:
        """Append a non-empty value to a list field if not already present."""
        if value is None:
            return
        val_str = str(value).strip()
        if val_str and val_str not in entry[field]:
            entry[field].append(val_str)
