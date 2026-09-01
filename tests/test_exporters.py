"""
Unit tests for JSON, CSV, and OAAS Lexicon exporters.
"""

import json
import csv
import pytest
from pathlib import Path
from exporter.json_export import export_json
from exporter.csv_export import export_csv
from exporter.oaas_export import export_oaas_format


@pytest.fixture
def sample_terms():
    return [
        {
            "Name": "Cholera",
            "ID": "1435254666",
            "Term ID": "1A00",
            "URI": "http://id.who.int/icd/release/11/2024-01/mms/1435254666",
            "Synonyms": ["Asiatic cholera", "Epidemic cholera"],
            "Short Description": "Acute diarrhoeal infection",
            "Long Description": "",
            "Condition Group": "General",
            "hasDbXref": [],
            "Definition": "Infection due to Vibrio cholerae",
            "Type I Exclude": [],
            "Type II Exclude": [],
            "Includes": ["Cholera due to Vibrio cholerae 01"],
            "Applicable To": [],
            "forMapping": True,
            "mcXref": [],
            "Version": "ICD-11 2024-01",
            "PossiblePrefix": "ICD11",
            "superClassOf": [],
            "subClassOf": ["http://id.who.int/icd/release/11/2024-01/mms/chap1"],
        }
    ]


def test_export_json(tmp_path, sample_terms):
    target_path = tmp_path / "test_ontology.json"
    result_path = export_json(sample_terms, target_path)

    assert result_path.exists()
    with open(result_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert len(loaded) == 1
    assert loaded[0]["Name"] == "Cholera"


def test_export_csv(tmp_path, sample_terms):
    target_path = tmp_path / "test_ontology.csv"
    result_path = export_csv(sample_terms, target_path)

    assert result_path.exists()
    with open(result_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    assert rows[0]["Name"] == "Cholera"
    assert rows[0]["Synonyms"] == "Asiatic cholera | Epidemic cholera"


def test_export_oaas_format(tmp_path, sample_terms):
    target_path = tmp_path / "test_oaas_import.json"
    result_path = export_oaas_format(sample_terms, target_path)

    assert result_path.exists()
    with open(result_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    assert "lexicon_name" in loaded
    assert loaded["total_terms"] == 1
    assert loaded["terms"][0]["Name"] == "Cholera"
