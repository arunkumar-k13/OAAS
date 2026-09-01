"""
Unit tests for ontology validator checks (missing names, duplicate IDs, broken links, circular refs).
"""

import pytest
from transformer.validator import OntologyValidator


def test_validator_detects_anomalies():
    term1 = {
        "Name": "Cholera",
        "Term ID": "1A00",
        "ID": "1001",
        "URI": "http://id.who.int/icd/release/11/2024-01/mms/1001",
        "subClassOf": ["http://id.who.int/icd/release/11/2024-01/mms/non_existent"],
        "superClassOf": [],
        "Synonyms": ["Cholera", "Cholera"],
    }

    term2 = {
        "Name": "Unnamed Entity (1A01)",
        "Term ID": "",
        "ID": "1002",
        "URI": "http://id.who.int/icd/release/11/2024-01/mms/1002",
        "subClassOf": ["http://id.who.int/icd/release/11/2024-01/mms/1002"],  # Circular self reference
        "superClassOf": [],
        "Synonyms": [],
    }

    validator = OntologyValidator()
    report = validator.validate([term1, term2])

    assert report.total_entities_validated == 2
    assert report.missing_names == 1
    assert report.missing_codes == 1
    assert report.broken_hierarchy >= 1
    assert report.circular_references >= 1
    assert report.duplicate_synonyms >= 1
    assert report.is_valid is False


def test_validator_passes_clean_ontology():
    term1 = {
        "Name": "Infectious Diseases",
        "Term ID": "01",
        "ID": "100",
        "URI": "http://id.who.int/icd/release/11/2024-01/mms/100",
        "subClassOf": [],
        "superClassOf": ["http://id.who.int/icd/release/11/2024-01/mms/101"],
        "Synonyms": [],
    }
    term2 = {
        "Name": "Cholera",
        "Term ID": "1A00",
        "ID": "101",
        "URI": "http://id.who.int/icd/release/11/2024-01/mms/101",
        "subClassOf": ["http://id.who.int/icd/release/11/2024-01/mms/100"],
        "superClassOf": [],
        "Synonyms": ["Asiatic cholera"],
    }

    validator = OntologyValidator()
    report = validator.validate([term1, term2])

    assert report.missing_names == 0
    assert report.broken_hierarchy == 0
    assert report.circular_references == 0
    assert report.is_valid is True
