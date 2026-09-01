"""
Bidirectional hierarchy generator resolving superClassOf, subClassOf, and Condition Group to Concept Names.
"""

from collections import deque
from typing import Any, Dict, List, Set
from utils.logger import mapping_logger


class HierarchyGenerator:
    """Enforces bidirectional parent-child links and resolves URIs/IDs/Condition Group to concept Names."""

    def __init__(self, resolve_to_name: bool = True):
        self.resolve_to_name = resolve_to_name

    def build_bidirectional_links(self, terms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Populate, synchronize, and resolve `superClassOf`, `subClassOf`, and `Condition Group` to Concept Names.

        Args:
            terms: List of mapped OAAS ontology dictionaries.

        Returns:
            Updated list of terms with fully resolved bidirectional Concept Name links and Condition Groups.
        """
        mapping_logger.info(f"Generating bidirectional hierarchy links across {len(terms)} terms...")

        # Build lookup maps by URI and ID
        term_map: Dict[str, Dict[str, Any]] = {}
        for term in terms:
            uri = term.get("URI")
            term_id = term.get("ID")
            if uri:
                term_map[uri] = term
            if term_id:
                term_map[term_id] = term

        # Pass 1: Bidirectional link propagation (parent <-> child)
        for term in terms:
            current_uri = term.get("URI")
            current_id = term.get("ID")
            parents = term.get("subClassOf", [])

            for parent_ref in list(parents):
                parent_term = term_map.get(parent_ref)
                if parent_term:
                    super_list = parent_term.get("superClassOf", [])
                    target_ref = current_uri or current_id
                    if target_ref and target_ref not in super_list:
                        super_list.append(target_ref)
                        parent_term["superClassOf"] = super_list

        for term in terms:
            current_uri = term.get("URI")
            current_id = term.get("ID")
            children = term.get("superClassOf", [])

            for child_ref in list(children):
                child_term = term_map.get(child_ref)
                if child_term:
                    sub_list = child_term.get("subClassOf", [])
                    target_ref = current_uri or current_id
                    if target_ref and target_ref not in sub_list:
                        sub_list.append(target_ref)
                        child_term["subClassOf"] = sub_list

        # Pass 2: Propagate Condition Group from top-level Chapters down to descendants
        mapping_logger.info("Propagating top-level Chapter Names as Condition Group...")

        # Top-level chapter terms are terms whose parent URI ends with '/mms' or contains 'Mortality and Morbidity'
        chapters: List[Dict[str, Any]] = []
        for term in terms:
            parents = term.get("subClassOf", [])
            is_chapter = any(
                str(p).rstrip("/").endswith("/mms")
                or "Mortality and Morbidity" in str(p)
                or str(p).rstrip("/").endswith("/release/10/2019")
                or "10th Revision" in str(p)
                for p in parents
            )
            if is_chapter:
                chapters.append(term)

        for chap in chapters:
            chap_name = chap.get("Name", "General")
            chap["Condition Group"] = chap_name

            # BFS traversal to assign chap_name to all descendants
            queue = deque(chap.get("superClassOf", []))
            visited = set()

            while queue:
                child_ref = queue.popleft()
                if child_ref in visited:
                    continue
                visited.add(child_ref)

                child_term = term_map.get(child_ref)
                if child_term:
                    child_term["Condition Group"] = chap_name
                    # Queue child's children
                    queue.extend(child_term.get("superClassOf", []))

        # Pass 3: Resolve URIs/IDs to Concept Names (Labels)
        if self.resolve_to_name:
            mapping_logger.info("Resolving superClassOf and subClassOf URIs to Concept Names (Labels)...")
            for term in terms:
                # Resolve subClassOf
                resolved_parents = []
                for p_ref in term.get("subClassOf", []):
                    ref_target = term_map.get(p_ref)
                    if ref_target and ref_target.get("Name"):
                        resolved_parents.append(ref_target["Name"])
                    else:
                        clean_ref = str(p_ref).rstrip("/").split("/")[-1] if str(p_ref).startswith("http") else str(p_ref)
                        resolved_parents.append(f"ICD11:{clean_ref}" if clean_ref and not clean_ref.startswith("ICD11") else str(p_ref))

                # Resolve superClassOf
                resolved_children = []
                for c_ref in term.get("superClassOf", []):
                    ref_target = term_map.get(c_ref)
                    if ref_target and ref_target.get("Name"):
                        resolved_children.append(ref_target["Name"])
                    else:
                        clean_ref = str(c_ref).rstrip("/").split("/")[-1] if str(c_ref).startswith("http") else str(c_ref)
                        resolved_children.append(f"ICD11:{clean_ref}" if clean_ref and not clean_ref.startswith("ICD11") else str(c_ref))

                # Deduplicate while preserving order
                term["subClassOf"] = list(dict.fromkeys(resolved_parents))
                term["superClassOf"] = list(dict.fromkeys(resolved_children))

        mapping_logger.info("Bidirectional hierarchy generation, Condition Group propagation, and Name resolution complete.")
        return terms
