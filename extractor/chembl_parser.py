"""
ChEMBL 37 Bioactive Compounds Extractor and Parser.
Fetches ChEMBL compound records via REST API or SQLite file and ingests into MongoDB.
Includes chemical structures (SMILES, InChI, InChIKey), trade names, target details (action type, organism, UniProt ID), indications, mechanisms, and DBXref cross-references.
"""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

from config.constants import COLLECTION_CHEMBL_RAW
from database.mongo import get_db
from utils.logger import api_logger


class ChEMBLParser:
    """Parser & Fetcher for EMBL-EBI ChEMBL 37 Bioactive Compounds."""

    BASE_API_URL = "https://www.ebi.ac.uk/chembl/api/data"

    def __init__(self, db=None):
        self.db = db if db is not None else get_db()
        self.raw_col = self.db[COLLECTION_CHEMBL_RAW]

    def fetch_sample_chunk(self, limit: int = 200, max_phase: Optional[int] = 4) -> int:
        """
        Fetch a test sample chunk of compounds via ChEMBL REST API.
        """
        api_logger.info(f"Fetching sample chunk of {limit} ChEMBL compounds (max_phase={max_phase})...")
        self.raw_col.delete_many({})

        raw_docs = []
        offset = 0
        batch_size = min(limit, 100)
        headers = {"Accept": "application/json"}

        with requests.Session() as session:
            session.headers.update(headers)
            while len(raw_docs) < limit:
                url = f"{self.BASE_API_URL}/molecule?limit={batch_size}&offset={offset}"
                if max_phase is not None:
                    url += f"&max_phase={max_phase}"

                try:
                    resp = session.get(url, timeout=30.0)
                    resp.raise_for_status()
                    data = resp.json()
                    molecules = data.get("molecules", [])

                    if not molecules:
                        break

                    for mol in molecules:
                        chembl_id = mol.get("molecule_chembl_id")
                        if not chembl_id:
                            continue

                        # Extract synonyms and trade names
                        synonyms = []
                        trade_names = []
                        for syn in mol.get("molecule_synonyms", []) or []:
                            s_name = syn.get("molecule_synonym")
                            s_type = str(syn.get("syn_type") or "").upper()

                            if s_name:
                                if "TRADE" in s_type or "BRAND" in s_type:
                                    if s_name not in trade_names:
                                        trade_names.append(s_name)
                                else:
                                    if s_name not in synonyms:
                                        synonyms.append(s_name)

                        # Extract structure details
                        structs = mol.get("molecule_structures") or {}
                        props = mol.get("molecule_properties") or {}

                        # Extract cross references (PubChem, DrugBank, UniProt, ChemSpider, ATC, etc.)
                        cross_refs = []
                        for xr in mol.get("cross_references") or []:
                            src = xr.get("xref_src") or xr.get("src_id")
                            id_val = xr.get("xref_id")
                            name_val = xr.get("xref_name")
                            if src and id_val:
                                xref_str = f"{src}:{id_val}"
                                if xref_str not in cross_refs:
                                    cross_refs.append(xref_str)
                            elif src and name_val:
                                xref_str = f"{src}:{name_val}"
                                if xref_str not in cross_refs:
                                    cross_refs.append(xref_str)

                        # ATC classification codes
                        atc_codes = mol.get("atc_classifications") or []
                        for atc in atc_codes:
                            atc_str = f"ATC:{atc}"
                            if atc_str not in cross_refs:
                                cross_refs.append(atc_str)

                        doc = {
                            "chembl_id": chembl_id,
                            "pref_name": mol.get("pref_name") or chembl_id,
                            "molecule_type": mol.get("molecule_type") or "Small molecule",
                            "max_phase": mol.get("max_phase"),
                            "first_approval": mol.get("first_approval"),
                            "black_box_warning": mol.get("black_box_warning"),
                            "synonyms": synonyms,
                            "trade_names": trade_names,
                            "canonical_smiles": structs.get("canonical_smiles") or "",
                            "standard_inchi": structs.get("standard_inchi") or "",
                            "standard_inchi_key": structs.get("standard_inchi_key") or "",
                            "molecular_formula": props.get("full_molformula") or "",
                            "full_mwt": props.get("full_mwt") or "",
                            "cross_references": cross_refs,
                            "indications": [],
                            "mechanisms": [],
                            "target_action_types": [],
                            "target_organisms": [],
                            "target_uniprot_ids": [],
                            "targets": [],
                            "parent_chembl_id": (mol.get("molecule_hierarchy") or {}).get("parent_chembl_id"),
                        }

                        raw_docs.append(doc)
                        if len(raw_docs) >= limit:
                            break

                    offset += len(molecules)
                    api_logger.info(f"Fetched {len(raw_docs)} / {limit} sample compounds...")

                except Exception as e:
                    api_logger.error(f"Error fetching ChEMBL API page at offset {offset}: {e}")
                    break

        if raw_docs:
            self.raw_col.insert_many(raw_docs)
            api_logger.info(f"Inserted {len(raw_docs)} raw ChEMBL sample documents into `{COLLECTION_CHEMBL_RAW}`.")

        return len(raw_docs)

    def parse_sqlite_file(self, db_filepath: Path, limit: Optional[int] = None, max_phase: Optional[int] = None) -> int:
        """
        Parse local ChEMBL SQLite database file (chembl_37.db).
        """
        if not db_filepath.exists():
            api_logger.error(f"ChEMBL SQLite file not found at: {db_filepath}")
            raise FileNotFoundError(f"ChEMBL SQLite file not found: {db_filepath}")

        api_logger.info(f"Parsing ChEMBL SQLite database from: {db_filepath} (max_phase={max_phase}, limit={limit})")
        self.raw_col.delete_many({})

        conn = sqlite3.connect(str(db_filepath))
        cursor = conn.cursor()

        # 1. Bulk load synonyms & trade names
        api_logger.info("Loading synonyms and trade names from SQLite...")
        syns_map = {}
        trades_map = {}
        cursor.execute("SELECT molregno, synonyms, syn_type FROM molecule_synonyms")
        for molregno, syn, stype in cursor.fetchall():
            if not syn:
                continue
            stype_str = str(stype or "").upper()
            if "TRADE" in stype_str or "BRAND" in stype_str:
                trades_map.setdefault(molregno, []).append(syn)
            else:
                syns_map.setdefault(molregno, []).append(syn)

        # 2. Bulk load indications
        api_logger.info("Loading indications from SQLite...")
        ind_map = {}
        cursor.execute("SELECT molregno, mesh_heading FROM drug_indication")
        for molregno, heading in cursor.fetchall():
            if heading:
                ind_map.setdefault(molregno, []).append(heading)

        # 3. Bulk load mechanisms & action types
        api_logger.info("Loading mechanisms from SQLite...")
        mech_map = {}
        act_map = {}
        cursor.execute("SELECT molregno, mechanism_of_action, action_type FROM drug_mechanism")
        for molregno, moa, act in cursor.fetchall():
            if moa:
                mech_map.setdefault(molregno, []).append(moa)
            if act:
                act_map.setdefault(molregno, []).append(act)

        # 4. Bulk load ATC codes
        api_logger.info("Loading ATC classifications from SQLite...")
        atc_map = {}
        cursor.execute("SELECT molregno, level5 FROM molecule_atc_classification")
        for molregno, atc in cursor.fetchall():
            if atc:
                atc_map.setdefault(molregno, []).append(f"ATC:{atc}")

        # 5. Execute main compound query
        query = """
            SELECT md.molregno, md.chembl_id, md.pref_name, md.molecule_type, md.max_phase, md.first_approval,
                   md.black_box_warning, ms.canonical_smiles, ms.standard_inchi, ms.standard_inchi_key,
                   mp.full_molformula, mp.full_mwt, mh2.chembl_id AS parent_chembl_id
            FROM molecule_dictionary md
            LEFT JOIN compound_structures ms ON md.molregno = ms.molregno
            LEFT JOIN compound_properties mp ON md.molregno = mp.molregno
            LEFT JOIN molecule_hierarchy mh ON md.molregno = mh.molregno
            LEFT JOIN molecule_dictionary mh2 ON mh.parent_molregno = mh2.molregno
        """
        where_clauses = []
        if max_phase is not None:
            where_clauses.append(f"md.max_phase >= {max_phase}")

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        if limit and limit > 0:
            query += f" LIMIT {limit}"

        api_logger.info("Executing compound query...")
        cursor.execute(query)
        rows = cursor.fetchall()

        raw_docs = []
        batch_size = 5000

        for r in rows:
            (molregno, chembl_id, pref_name, mol_type, max_p, first_app, bb_warn,
             smiles, inchi, inchi_key, formula, mwt, parent_id) = r

            doc = {
                "chembl_id": chembl_id,
                "pref_name": pref_name or chembl_id,
                "molecule_type": mol_type or "Small molecule",
                "max_phase": max_p,
                "first_approval": first_app,
                "black_box_warning": bb_warn,
                "synonyms": syns_map.get(molregno, []),
                "trade_names": trades_map.get(molregno, []),
                "canonical_smiles": smiles or "",
                "standard_inchi": inchi or "",
                "standard_inchi_key": inchi_key or "",
                "molecular_formula": formula or "",
                "full_mwt": mwt or "",
                "cross_references": atc_map.get(molregno, []),
                "indications": ind_map.get(molregno, []),
                "mechanisms": mech_map.get(molregno, []),
                "target_action_types": act_map.get(molregno, []),
                "target_organisms": [],
                "target_uniprot_ids": [],
                "targets": [],
                "parent_chembl_id": parent_id or chembl_id,
            }

            raw_docs.append(doc)
            if len(raw_docs) >= batch_size:
                self.raw_col.insert_many(raw_docs)
                raw_docs.clear()

        if raw_docs:
            self.raw_col.insert_many(raw_docs)
            raw_docs.clear()

        conn.close()
        total = self.raw_col.count_documents({})
        api_logger.info(f"Total ChEMBL raw documents stored in MongoDB: {total:,}")
        return total

