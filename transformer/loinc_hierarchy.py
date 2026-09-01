"""
LOINC Hierarchy Generator.
Generates bidirectional superClassOf <-> subClassOf relationships
using the LOINC ComponentHierarchyBySystem.csv parent-child data.

The hierarchy uses LP codes (LOINC Part codes) as grouping nodes
and LOINC codes (e.g., 595-9) as leaf nodes. We build relationships
between LOINC terms that share the same immediate LP parent,
treating the LP parent group as a common ancestor.
"""

from typing import Any, Dict, List, Set
from database.mongo import get_db
from utils.logger import mapping_logger


class LOINCHierarchyGenerator:
    """Builds bidirectional parent/child hierarchy for LOINC terms."""

    def __init__(self, db=None):
        self.db = db if db is not None else get_db()

    def build_bidirectional_links(self, terms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build superClassOf and subClassOf using LOINC hierarchy data.

        Strategy:
        1. For each LOINC code in the hierarchy, find its immediate LP parent.
        2. Walk up the LP chain to find the nearest ancestor LP whose CODE_TEXT
           matches a LOINC term name (Long Common Name). That term becomes the parent.
        3. If no ancestor matches, use the LP parent's direct LOINC code children
           to find sibling groups.
        """
        mapping_logger.info(f"Building LOINC hierarchy for {len(terms)} terms...")

        hier_col = self.db.get_collection("loinc_hierarchy")
        hier_count = hier_col.count_documents({})

        if hier_count == 0:
            mapping_logger.warning("No hierarchy data found. Hierarchy links will be empty.")
            return terms

        mapping_logger.info(f"Found {hier_count:,} hierarchy records. Building lookup maps...")

        # Build LOINC_NUM -> Name lookup
        loinc_to_name = {}
        name_set = set()
        for term in terms:
            term_ids = term.get("Term ID", "")
            name = term["Name"]
            name_set.add(name)
            if term_ids:
                for part in term_ids.split("|"):
                    part_clean = part.strip().replace("LOINC:", "")
                    if part_clean:
                        loinc_to_name[part_clean] = name

        mapping_logger.info(f"Built {len(loinc_to_name):,} LOINC code to Name mappings.")

        # Build hierarchy maps
        code_to_parent = {}
        code_to_text = {}
        parent_to_children = {}

        for doc in hier_col.find({}, {"_id": 0}):
            code = doc.get("code", "").strip()
            parent = doc.get("immediate_parent", "").strip()
            text = doc.get("code_text", "").strip()
            if not code:
                continue
            code_to_parent[code] = parent
            code_to_text[code] = text
            if parent:
                if parent not in parent_to_children:
                    parent_to_children[parent] = []
                parent_to_children[parent].append(code)

        mapping_logger.info(f"Parsed {len(code_to_parent):,} hierarchy entries.")

        # Build parent-child relationships
        parents_map = {term["Name"]: set() for term in terms}
        children_map = {term["Name"]: set() for term in terms}

        # For each LP parent, find its LOINC code children.
        # LOINC codes that share an LP parent are siblings.
        # We also build parent links by walking up the tree.
        linked = 0

        # Group LOINC codes by their immediate LP parent
        lp_to_loinc_children = {}
        for code, parent in code_to_parent.items():
            # Is this code a real LOINC term?
            if code in loinc_to_name and parent:
                if parent not in lp_to_loinc_children:
                    lp_to_loinc_children[parent] = []
                lp_to_loinc_children[parent].append(code)

        mapping_logger.info(f"Found {len(lp_to_loinc_children):,} LP groups with LOINC children.")

        # For each LP parent, walk up the tree to find an ancestor
        # whose CODE_TEXT or code matches a term name.
        # That ancestor becomes the "parent term" for all LOINC codes under it.
        for lp_code, loinc_children in lp_to_loinc_children.items():
            # Walk up from lp_code to find nearest matching term
            parent_name = None
            current = lp_code
            depth = 0
            while current and depth < 20:
                # Check if current LP's text matches a term name
                current_text = code_to_text.get(current, "")
                if current_text in name_set:
                    parent_name = current_text
                    break
                # Check if current code itself is a LOINC code that maps to a term
                if current in loinc_to_name:
                    parent_name = loinc_to_name[current]
                    break
                # Go up one level
                current = code_to_parent.get(current, "")
                depth += 1

            if parent_name:
                for child_code in loinc_children:
                    child_name = loinc_to_name[child_code]
                    if child_name != parent_name:
                        parents_map[child_name].add(parent_name)
                        if parent_name in children_map:
                            children_map[parent_name].add(child_name)
                        linked += 1

        mapping_logger.info(f"Built {linked:,} hierarchy links from LP ancestor matching.")

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
            f"LOINC hierarchy completed. "
            f"{parent_count:,} terms with subClassOf, "
            f"{child_count:,} terms with superClassOf."
        )
        return terms
