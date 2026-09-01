"""
Unit tests for hierarchy generator and bidirectional superClassOf / subClassOf link resolution.
"""

import pytest
from transformer.hierarchy import HierarchyGenerator


def test_bidirectional_hierarchy_linking():
    parent_term = {
        "Name": "Infectious diseases",
        "ID": "chap1",
        "URI": "http://id.who.int/icd/release/11/2024-01/mms/chap1",
        "subClassOf": [],
        "superClassOf": [],
    }

    child_term = {
        "Name": "Cholera",
        "ID": "cholera_123",
        "URI": "http://id.who.int/icd/release/11/2024-01/mms/cholera_123",
        "subClassOf": ["http://id.who.int/icd/release/11/2024-01/mms/chap1"],
        "superClassOf": [],
    }

    terms = [parent_term, child_term]

    generator = HierarchyGenerator()
    updated_terms = generator.build_bidirectional_links(terms)

    updated_parent = next(t for t in updated_terms if t["ID"] == "chap1")
    updated_child = next(t for t in updated_terms if t["ID"] == "cholera_123")

    # Parent should now list child Name in superClassOf
    assert "Cholera" in updated_parent["superClassOf"]
    # Child should list parent Name in subClassOf
    assert "Infectious diseases" in updated_child["subClassOf"]
