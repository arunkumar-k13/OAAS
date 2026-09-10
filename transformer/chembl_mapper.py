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
        mapping_logger.info(f"Transforming {len(raw_documents)} raw ChEMBL compound records...")

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
                    "Term ID": [],
                    "URI": [],
                    "Molecule Type": [],
                    "Max Phase": [],
                    "First Approval Year": [],
                    "Black Box Warning": [],
                    "Synonyms": [],
                    "Trade Names": [],
                    "SMILES": [],
                    "InChI": [],
                    "InChI Key": [],
                    "Molecular Formula": [],
                    "Molecular Weight": [],
                    "Indications": [],
                    "Mechanisms": [],
                    "Target Action Type": [],
                    "Target Organism": [],
                    "Target UniProt ID": [],
                    "Biological Targets": [],
                    "Version": "ChEMBL 37",
                    "mcXref": "",  # Strictly blank
                    "forMapping": "True",
                    "hasDbXref": [],  # Populated with external cross-references
                    "PossiblePrefix": "ChEMBL",
                    "superClassOf": [],
                    "subClassOf": [],
                }

            entry = grouped[name]

            # Term ID: CHEMBL_ID
            if chembl_id:
                term_id_str = f"{chembl_id}|ChEMBL:{chembl_id}"
                if term_id_str not in entry["Term ID"]:
                    entry["Term ID"].append(term_id_str)

                # URI
                uri_str = f"https://www.ebi.ac.uk/chembl/compound_report_card/{chembl_id}/"
                if uri_str not in entry["URI"]:
                    entry["URI"].append(uri_str)

            # Map fields
            self._append_unique(entry, "Molecule Type", doc.get("molecule_type"))

            # Format Max Phase float -> readable label ("Approved", "Phase I", etc.)
            raw_phase = str(doc.get("max_phase") or "").strip()
            phase_label = self.PHASE_MAP.get(raw_phase, raw_phase)
            self._append_unique(entry, "Max Phase", phase_label)

            self._append_unique(entry, "First Approval Year", doc.get("first_approval"))
            self._append_unique(entry, "Black Box Warning", doc.get("black_box_warning"))
            self._append_unique(entry, "SMILES", doc.get("canonical_smiles"))
            self._append_unique(entry, "InChI", doc.get("standard_inchi"))
            self._append_unique(entry, "InChI Key", doc.get("standard_inchi_key"))
            self._append_unique(entry, "Molecular Formula", doc.get("molecular_formula"))
            self._append_unique(entry, "Molecular Weight", doc.get("full_mwt"))

            # Synonyms & Trade Names
            syns = doc.get("synonyms") or []
            if isinstance(syns, str):
                syns = [syns]
            for syn in syns:
                self._append_unique(entry, "Synonyms", syn)

            trades = doc.get("trade_names") or []
            if isinstance(trades, str):
                trades = [trades]
            for tr in trades:
                self._append_unique(entry, "Trade Names", tr)

            # External Cross-References (hasDbXref)
            xrefs = doc.get("cross_references") or []
            if isinstance(xrefs, str):
                xrefs = [xrefs]
            for xr in xrefs:
                self._append_unique(entry, "hasDbXref", xr)

            # Indications
            inds = doc.get("indications") or []
            if isinstance(inds, str):
                inds = [inds]
            for ind in inds:
                self._append_unique(entry, "Indications", ind)

            # Mechanisms & Target details
            mechs = doc.get("mechanisms") or []
            if isinstance(mechs, str):
                mechs = [mechs]
            for m in mechs:
                self._append_unique(entry, "Mechanisms", m)

            act_types = doc.get("target_action_types") or []
            if isinstance(act_types, str):
                act_types = [act_types]
            for at in act_types:
                self._append_unique(entry, "Target Action Type", at)

            orgs = doc.get("target_organisms") or []
            if isinstance(orgs, str):
                orgs = [orgs]
            for og in orgs:
                self._append_unique(entry, "Target Organism", og)

            uids = doc.get("target_uniprot_ids") or []
            if isinstance(uids, str):
                uids = [uids]
            for uid in uids:
                self._append_unique(entry, "Target UniProt ID", uid)

            targets = doc.get("targets") or []
            if isinstance(targets, str):
                targets = [targets]
            for tgt in targets:
                self._append_unique(entry, "Biological Targets", tgt)

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

        mapping_logger.info(f"Transformed into {len(transformed_terms)} clean, unique ChEMBL compound terms.")
        return transformed_terms

    @staticmethod
    def _append_unique(entry: Dict, field: str, value) -> None:
        """Append a non-empty value to a list field if not already present."""
        if value is None:
            return
        val_str = str(value).strip()
        if val_str and val_str not in entry[field]:
            entry[field].append(val_str)
