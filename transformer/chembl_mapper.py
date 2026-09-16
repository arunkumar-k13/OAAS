"""
ChEMBL 37 Mapper and Schema Transformer.
Transforms raw ChEMBL compound records into Lexicon-ready ontology schema.
Groups by Name (pref_name) to guarantee zero duplicate name import errors.
Converts Max Phase numbers to human-readable labels (4.0 -> Approved).
Populates Trade Names, Target Action Type, Target Organism, Target UniProt ID, and DBXref cross-references.
"""

import re
from typing import Any, Dict, List
from utils.logger import mapping_logger


class ChEMBLMapper:
    """Mapper for EMBL-EBI ChEMBL 37 Bioactive Compounds to Lexicon schema."""

    PHASE_MAP = {
        "4.0": "Approved",
        "4": "Approved",
        "3.0": "Phase III",
        "3": "Phase III",
        "2.0": "Phase II",
        "2": "Phase II",
        "1.0": "Phase I",
        "1": "Phase I",
        "0.0": "Preclinical",
        "0": "Preclinical",
    }

    def transform_batch(self, raw_documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform raw ChEMBL documents into mapped Lexicon schemas grouped by Name.
        Deduplication: Groups by pref_name (Name) and pipe-merges all distinct attribute values.
        """
        try:
            total_count = f"{len(raw_documents):,}"
        except TypeError:
            total_count = "streaming"
        mapping_logger.info(f"Transforming {total_count} raw ChEMBL compound records...")

        grouped = {}

        for doc in raw_documents:
            chembl_id = str(doc.get("chembl_id") or "").strip()
            name = str(doc.get("pref_name") or chembl_id or "").strip()

            if not name:
                continue

            if name not in grouped:
                grouped[name] = {
                    "Name": name,
                    "ID": "",  # Blank for Lexicon auto-generation
                    "Term ID": set(),
                    "URI": set(),
                    "Molecule Type": set(),
                    "Max Phase": set(),
                    "First Approval Year": set(),
                    "Black Box Warning": set(),
                    "Synonyms": set(),
                    "Trade Names": set(),
                    "SMILES": set(),
                    "InChI": set(),
                    "InChI Key": set(),
                    "Molecular Formula": set(),
                    "Molecular Weight": set(),
                    "Indications": set(),
                    "Mechanisms": set(),
                    "Target Action Type": set(),
                    "Target Organism": set(),
                    "Target UniProt ID": set(),
                    "Biological Targets": set(),
                    "Version": "ChEMBL 37",
                    "mcXref": "",  # Strictly blank
                    "forMapping": "True",
                    "hasDbXref": set(),  # Populated with external cross-references
                    "PossiblePrefix": "ChEMBL",
                    "superClassOf": set(),
                    "subClassOf": set(),
                }

            entry = grouped[name]

            # Term ID & URI
            if chembl_id:
                entry["Term ID"].add(f"{chembl_id}|ChEMBL:{chembl_id}")
                entry["URI"].add(f"https://www.ebi.ac.uk/chembl/compound_report_card/{chembl_id}/")

            # Map single attributes
            self._add_to_set(entry["Molecule Type"], doc.get("molecule_type"))

            raw_phase = str(doc.get("max_phase") or "").strip()
            phase_label = self.PHASE_MAP.get(raw_phase, raw_phase)
            self._add_to_set(entry["Max Phase"], phase_label)

            self._add_to_set(entry["First Approval Year"], doc.get("first_approval"))
            self._add_to_set(entry["Black Box Warning"], doc.get("black_box_warning"))
            self._add_to_set(entry["SMILES"], doc.get("canonical_smiles"))
            self._add_to_set(entry["InChI"], doc.get("standard_inchi"))
            self._add_to_set(entry["InChI Key"], doc.get("standard_inchi_key"))
            self._add_to_set(entry["Molecular Formula"], doc.get("molecular_formula"))
            self._add_to_set(entry["Molecular Weight"], doc.get("full_mwt"))

            # Map list attributes
            self._add_list_to_set(entry["Synonyms"], doc.get("synonyms"))
            self._add_list_to_set(entry["Trade Names"], doc.get("trade_names"))
            self._add_list_to_set(entry["hasDbXref"], doc.get("cross_references"))
            self._add_list_to_set(entry["Indications"], doc.get("indications"))
            self._add_list_to_set(entry["Mechanisms"], doc.get("mechanisms"))
            self._add_list_to_set(entry["Target Action Type"], doc.get("target_action_types"))
            self._add_list_to_set(entry["Target Organism"], doc.get("target_organisms"))
            self._add_list_to_set(entry["Target UniProt ID"], doc.get("target_uniprot_ids"))
            self._add_list_to_set(entry["Biological Targets"], doc.get("targets"))

        # Clean and format pipe-joined strings
        transformed_terms = []
        for name, entry in grouped.items():
            cleaned_term = {}
            for k, v in entry.items():
                if isinstance(v, set):
                    cleaned_term[k] = "|".join(sorted(v))
                else:
                    cleaned_term[k] = str(v).strip()
            transformed_terms.append(cleaned_term)

        mapping_logger.info(f"Transformed into {len(transformed_terms):,} clean, unique ChEMBL compound terms.")
        return transformed_terms

    @staticmethod
    def _add_to_set(s: set, val) -> None:
        """Add non-empty string value to set."""
        if val is not None:
            v_str = str(val).strip()
            if v_str:
                s.add(v_str)

    @staticmethod
    def _add_list_to_set(s: set, val_list) -> None:
        """Add list or pipe-separated string values to set."""
        if not val_list:
            return
        if isinstance(val_list, str):
            val_list = [val_list]
        for v in val_list:
            if v is not None:
                v_str = str(v).strip()
                if v_str:
                    for part in v_str.split("|"):
                        p_clean = part.strip()
                        if p_clean:
                            s.add(p_clean)

