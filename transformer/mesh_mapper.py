"""
MeSH 2026 Mapper and Schema Transformer.
Transforms raw MeSH records into Descriptor, Concept, and Qualifier schemas.
Groups by Name and Term Type to guarantee zero duplicate name import errors within class.
"""

from typing import Any, Dict, List
import re
from config.constants import MESH_DESCRIPTOR_FIELDS
from utils.logger import mapping_logger


class MeSHMapper:
    """Mapper for NLM MeSH 2026 Ontology terms."""

    def transform_batch(self, raw_documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform raw MeSH documents into mapped schemas grouped by (Name, Term Type).
        """
        mapping_logger.info(f"Transforming {len(raw_documents)} raw MeSH records...")

        grouped = {}

        for doc in raw_documents:
            name = str(doc.get("name") or doc.get("Name") or "").strip()
            if not name:
                continue

            term_type = str(doc.get("term_type") or doc.get("Term Type") or "Descriptor").strip()
            group_key = (name, term_type)

            if group_key not in grouped:
                grouped[group_key] = {
                    "Name": name,
                    "Term Type": term_type,
                    "ID": "",  # Blank for Lexicon auto-generation
                    "Term ID": [],
                    "URI": [],
                    "Tree Number": [],
                    "Synonyms": [],
                    "EntryTerm Name": [],
                    "Mapped To Descriptor": [],
                    "Note": [],
                    "History note": [],
                    "Public MeSH note": [],
                    "Version": "MeSH 2026",
                    "PossiblePrefix": "MeSH",
                    "superClassOf": [],
                    "subClassOf": [],
                    "hasDbXref": "",
                    "mcXref": "",
                    "forMapping": "True"
                }

            entry = grouped[group_key]

            # Populate Term ID & URI
            ui = doc.get("ui") or doc.get("ID") or ""
            if ui:
                term_id_str = f"{ui}|MeSH:{ui}"
                if term_id_str not in entry["Term ID"]:
                    entry["Term ID"].append(term_id_str)
                uri_str = f"https://meshb.nlm.nih.gov/record/ui?ui={ui}"
                if uri_str not in entry["URI"]:
                    entry["URI"].append(uri_str)

            # Populate Mapped To Descriptor (for Concept records)
            mapped_desc = doc.get("mapped_to_descriptor") or doc.get("Mapped To Descriptor")
            if mapped_desc and str(mapped_desc).strip():
                s = str(mapped_desc).strip()
                if s not in entry["Mapped To Descriptor"]:
                    entry["Mapped To Descriptor"].append(s)

            # Populate Tree Numbers
            tns = doc.get("tree_numbers") or doc.get("Tree Number") or []
            if isinstance(tns, str):
                tns = [tns]
            for tn in tns:
                if tn and str(tn).strip() not in entry["Tree Number"]:
                    entry["Tree Number"].append(str(tn).strip())

            # Populate Synonyms
            syns = doc.get("synonyms") or doc.get("Synonyms") or []
            if isinstance(syns, str):
                syns = [syns]
            for syn in syns:
                if syn and str(syn).strip() not in entry["Synonyms"]:
                    entry["Synonyms"].append(str(syn).strip())

        # Clean and format pipe-joined strings
        transformed_terms = []
        for (name, term_type), entry in grouped.items():
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

        mapping_logger.info(f"Transformed into {len(transformed_terms)} clean, unique MeSH terms across term types.")
        return transformed_terms
