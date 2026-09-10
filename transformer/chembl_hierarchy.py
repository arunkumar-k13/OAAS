"""
ChEMBL Hierarchy Generator.
Generates bidirectional superClassOf <-> subClassOf relationships
between parent molecules and salt derivatives.
"""

from typing import Any, Dict, List
from database.mongo import get_db
from utils.logger import mapping_logger


class ChEMBLHierarchyGenerator:
    """Builds bidirectional parent/child hierarchy for ChEMBL compounds."""

    def __init__(self, db=None):
        self.db = db if db is not None else get_db()

    def build_bidirectional_links(self, terms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build superClassOf and subClassOf fields based on ChEMBL parent/child molecule links.
        """
        mapping_logger.info(f"Building ChEMBL hierarchy for {len(terms)} compound terms...")

        # Build chembl_id -> Name lookup
        chembl_to_name = {}
        for term in terms:
            term_ids = term.get("Term ID", "")
            if term_ids:
                for part in term_ids.split("|"):
                    part_clean = part.strip().replace("ChEMBL:", "")
                    if part_clean:
                        chembl_to_name[part_clean] = term["Name"]

        # Fetch parent links from raw collection
        raw_col = self.db.get_collection("chembl_37_raw")
        parents_map = {term["Name"]: set() for term in terms}
        children_map = {term["Name"]: set() for term in terms}

        linked = 0
        for raw_doc in raw_col.find({"parent_chembl_id": {"$ne": None}}, {"_id": 0, "chembl_id": 1, "parent_chembl_id": 1}):
            child_id = raw_doc.get("chembl_id")
            parent_id = raw_doc.get("parent_chembl_id")

            if not child_id or not parent_id or child_id == parent_id:
                continue

            child_name = chembl_to_name.get(child_id)
            parent_name = chembl_to_name.get(parent_id)

            if child_name and parent_name and child_name != parent_name:
                parents_map[child_name].add(parent_name)
                children_map[parent_name].add(child_name)
                linked += 1

        # Apply to terms
        parent_count = 0
        child_count = 0

        for term in terms:
            name = term["Name"]

            existing_sub = set(filter(None, term.get("subClassOf", "").split("|")))
            existing_sub.update(parents_map.get(name, set()))
            term["subClassOf"] = "|".join(sorted(existing_sub))
            if existing_sub:
                parent_count += 1

            existing_super = set(filter(None, term.get("superClassOf", "").split("|")))
            existing_super.update(children_map.get(name, set()))
            term["superClassOf"] = "|".join(sorted(existing_super))
            if existing_super:
                child_count += 1

        mapping_logger.info(
            f"ChEMBL hierarchy completed. {linked} links built. "
            f"{parent_count} terms with subClassOf, {child_count} terms with superClassOf."
        )
        return terms
