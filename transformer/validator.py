"""
Validation engine for checking ontology integrity, hierarchy consistency, and metadata quality.
"""

from typing import Any, Dict, List, Set
from collections import defaultdict
from models.responses import ValidationReport
from utils.logger import validation_logger


class OntologyValidator:
    """Validates OAAS Ontology terms for completeness, hierarchy anomalies, and duplicates."""

    def __init__(self):
        pass

    def validate(self, terms: List[Dict[str, Any]]) -> ValidationReport:
        """
        Execute comprehensive validation checks on mapped ontology terms.

        Args:
            terms: List of mapped OAAS ontology dictionaries.

        Returns:
            ValidationReport detailing counts, flag, and issue descriptions.
        """
        validation_logger.info(f"Starting validation on {len(terms)} ontology terms...")

        missing_names = 0
        missing_codes = 0
        duplicate_ids = 0
        broken_hierarchy = 0
        circular_references = 0
        missing_parents = 0
        missing_children = 0
        duplicate_synonyms = 0

        details: List[str] = []

        known_identifiers: Set[str] = set()
        seen_ids: Set[str] = set()

        # Build index of known identifiers (URIs, IDs, and Concept Names)
        for term in terms:
            uri = term.get("URI")
            term_id = term.get("ID")
            name = term.get("Name")

            if uri:
                known_identifiers.add(uri)
                if uri in seen_ids:
                    duplicate_ids += 1
                    details.append(f"Duplicate URI detected: '{uri}'")
                seen_ids.add(uri)

            if term_id:
                known_identifiers.add(term_id)

            if name:
                known_identifiers.add(name)

        # Track global synonyms for cross-term duplicates
        global_synonyms: Dict[str, List[str]] = defaultdict(list)

        for term in terms:
            name = term.get("Name", "")
            code = term.get("Term ID", "")
            uri = term.get("URI") or term.get("ID") or "Unknown"
            parents = term.get("subClassOf", [])
            children = term.get("superClassOf", [])
            synonyms = term.get("Synonyms", [])

            # Check 1: Missing Name
            if not name or name.startswith("Unnamed Entity"):
                missing_names += 1
                details.append(f"Entity '{uri}' is missing a valid Name.")

            # Check 2: Missing Code / Term ID
            if not code:
                missing_codes += 1

            # Check 3: Hierarchy - Missing Parents (Roots / Orphans)
            if not parents:
                missing_parents += 1

            # Check 4: Hierarchy - Missing Children (Leaves)
            if not children:
                missing_children += 1

            # Check 5: Broken Hierarchy Links
            for parent_ref in parents:
                if parent_ref not in known_identifiers:
                    broken_hierarchy += 1
                    details.append(f"Entity '{name}' references non-existent parent '{parent_ref}'.")

                # Check 6: Self-referential Circular Reference
                if parent_ref == uri or parent_ref == name:
                    circular_references += 1
                    details.append(f"Entity '{name}' self-references as its own parent.")

            for child_ref in children:
                if child_ref not in known_identifiers:
                    broken_hierarchy += 1
                    details.append(f"Entity '{name}' references non-existent child '{child_ref}'.")

                if child_ref == uri or child_ref == name:
                    circular_references += 1
                    details.append(f"Entity '{name}' self-references as its own child.")

            # Check 7: Duplicate Synonyms within term & across terms
            syn_set = set()
            for syn in synonyms:
                if syn in syn_set:
                    duplicate_synonyms += 1
                    details.append(f"Entity '{name}' has internal duplicate synonym '{syn}'.")
                syn_set.add(syn)
                global_synonyms[syn].append(name)

        # Cross-term duplicate synonym check
        for syn, term_names in global_synonyms.items():
            if len(term_names) > 1:
                duplicate_synonyms += 1

        is_valid = (missing_names == 0 and broken_hierarchy == 0 and circular_references == 0 and duplicate_ids == 0)

        report = ValidationReport(
            missing_names=missing_names,
            missing_codes=missing_codes,
            duplicate_ids=duplicate_ids,
            broken_hierarchy=broken_hierarchy,
            circular_references=circular_references,
            missing_parents=missing_parents,
            missing_children=missing_children,
            duplicate_synonyms=duplicate_synonyms,
            total_entities_validated=len(terms),
            is_valid=is_valid,
            details=details[:100],  # Limit details list for clean output
        )

        validation_logger.info(
            f"Validation finished. Total: {len(terms)}, Valid: {is_valid}, Missing Names: {missing_names}, "
            f"Broken Links: {broken_hierarchy}, Circular Refs: {circular_references}"
        )
        return report
