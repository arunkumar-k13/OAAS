"""
Bidirectional hierarchy generator resolving superClassOf, subClassOf, and Condition Group for ICD-10 terms.
"""

from typing import Any, Dict, List
from transformer.hierarchy import HierarchyGenerator
from utils.logger import mapping_logger


class ICD10HierarchyGenerator(HierarchyGenerator):
    """Hierarchy generator tailored for ICD-10 parent-child linkages and Condition Group propagation."""

    def build_bidirectional_links(self, terms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Populate, synchronize, and resolve `superClassOf`, `subClassOf`, and `Condition Group` to Concept Names for ICD-10.
        """
        mapping_logger.info(f"Generating ICD-10 bidirectional hierarchy links across {len(terms)} terms...")
        return super().build_bidirectional_links(terms)
