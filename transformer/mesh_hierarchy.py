"""
MeSH Hierarchy Generator.
Generates bidirectional superClassOf <-> subClassOf relationships using MeSH Tree Numbers.
"""

from typing import Any, Dict, List
from utils.logger import mapping_logger


class MeSHHierarchyGenerator:
    """Builds bidirectional parent/child hierarchy for MeSH terms using Tree Numbers."""

    def build_bidirectional_links(self, terms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build superClassOf and subClassOf fields based on MeSH Tree Numbers.
        """
        mapping_logger.info(f"Building hierarchy for {len(terms)} MeSH terms...")

        tree_to_name = {}
        for term in terms:
            name = term.get("Name", "")
            tns = term.get("Tree Number", "").split("|")
            for tn in tns:
                tn_clean = tn.strip()
                if tn_clean:
                    tree_to_name[tn_clean] = name

        parents_map = {term["Name"]: set() for term in terms}
        children_map = {term["Name"]: set() for term in terms}

        for term in terms:
            name = term.get("Name", "")
            tns = term.get("Tree Number", "").split("|")
            for tn in tns:
                tn_clean = tn.strip()
                if not tn_clean:
                    continue

                if "." in tn_clean:
                    parent_tn = tn_clean.rsplit(".", 1)[0]
                elif len(tn_clean) > 3:
                    parent_tn = tn_clean[:3]
                else:
                    parent_tn = ""

                if parent_tn and parent_tn in tree_to_name:
                    parent_name = tree_to_name[parent_tn]
                    if parent_name != name:
                        parents_map[name].add(parent_name)
                        children_map[parent_name].add(name)

        for term in terms:
            name = term["Name"]

            existing_sub = set(filter(None, term.get("subClassOf", "").split("|")))
            existing_sub.update(parents_map[name])
            term["subClassOf"] = "|".join(sorted(existing_sub))

            existing_super = set(filter(None, term.get("superClassOf", "").split("|")))
            existing_super.update(children_map[name])
            term["superClassOf"] = "|".join(sorted(existing_super))

        mapping_logger.info("MeSH bidirectional hierarchy generation completed.")
        return terms
