"""
Unit tests for text normalizers and WHO-to-OAAS schema mapper.
"""

import pytest
from transformer.normalizer import normalize_text, extract_label_value, normalize_list
from transformer.mapper import ICD11Mapper


def test_normalizers():
    assert normalize_text("  Cholera &amp; Diarrhea  \n") == "Cholera & Diarrhea"
    assert extract_label_value({"@value": "Tuberculosis", "@language": "en"}) == "Tuberculosis"
    assert normalize_list([{"@value": "Synonym 1"}, "Synonym 2", None]) == ["Synonym 1", "Synonym 2"]


def test_map_entity_to_oaas_schema():
    raw_payload = {
        "@id": "http://id.who.int/icd/release/11/2024-01/mms/1435254666",
        "code": "1A00",
        "title": {"@value": "Cholera", "@language": "en"},
        "definition": {"@value": "An acute diarrhoeal infection caused by ingestion of Vibrio cholerae."},
        "synonym": [{"label": {"@value": "Asiatic cholera"}}],
        "inclusion": [{"label": {"@value": "Infection due to Vibrio cholerae"}}],
        "exclusion": [{"label": {"@value": "Non-pathogenic vibrio infection"}}],
        "parent": ["http://id.who.int/icd/release/11/2024-01/mms/chapter1"],
        "child": ["http://id.who.int/icd/release/11/2024-01/mms/sub1"],
        "release": "ICD-11 2024-01",
        "browserUrl": "https://icd.who.int/browse11/l-m/en#/http%3A%2F%2Fid.who.int%2Ficd%2Frelease%2F11%2F2024-01%2Fmms%2F1435254666",
    }

    mapper = ICD11Mapper()
    mapped = mapper.map_entity(raw_payload)

    assert mapped["Name"] == "Cholera"
    assert mapped["Term ID"] == "1A00"
    assert mapped["ID"] == "1435254666"
    assert mapped["URI"] == "http://id.who.int/icd/release/11/2024-01/mms/1435254666"
    assert mapped["Definition"].startswith("An acute diarrhoeal")
    assert "Asiatic cholera" in mapped["Synonyms"]
    assert "Infection due to Vibrio cholerae" in mapped["Includes"]
    assert "Non-pathogenic vibrio infection" in mapped["Type I Exclude"]
    assert "http://id.who.int/icd/release/11/2024-01/mms/chapter1" in mapped["subClassOf"]
    assert "http://id.who.int/icd/release/11/2024-01/mms/sub1" in mapped["superClassOf"]
    assert "ICD11:1A00" in mapped["hasDbXref"]
    assert mapped["forMapping"] is True
    assert mapped["PossiblePrefix"] == "ICD11"


def test_map_batch():
    raw_list = [
        {
            "@id": "http://id.who.int/icd/release/11/2024-01/mms/1",
            "code": "1A00",
            "title": {"@value": "Cholera"},
        },
        {
            "@id": "http://id.who.int/icd/release/11/2024-01/mms/2",
            "code": "1A01",
            "title": {"@value": "Typhoid fever"},
        },
    ]

    mapper = ICD11Mapper()
    mapped_batch = mapper.map_batch(raw_list)

    assert len(mapped_batch) == 2
    assert mapped_batch[0]["Name"] == "Cholera"
    assert mapped_batch[1]["Name"] == "Typhoid fever"
