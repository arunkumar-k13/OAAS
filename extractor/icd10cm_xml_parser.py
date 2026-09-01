"""
XML Parser for CDC FY 2026 ICD-10-CM Tabular Release (icd10c-tabular-April-1-2026.xml).
Extracts Chapters, Range Headers (e.g. A00-B99, A00-A09), Category Codes, and 7-character clinical codes.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional
from utils.logger import api_logger


class ICD10CMXMLParser:
    """Parses CDC ICD-10-CM Tabular XML release into structured raw entity dictionaries."""

    def __init__(self, xml_filepath: Optional[Path] = None):
        self.xml_filepath = xml_filepath or Path("data/cdc_2026_xml/icd10c-tabular-April-1-2026.xml")

    def _extract_notes(self, element: ET.Element, tag_name: str) -> List[str]:
        """Extract note text lines from XML element (e.g. includes, excludes1, excludes2, note)."""
        notes = []
        container = element.find(tag_name)
        if container is not None:
            for note_node in container.findall("note"):
                text = "".join(note_node.itertext()).strip()
                if text:
                    notes.append(text)
        return notes

    def parse(self) -> List[Dict[str, Any]]:
        """
        Parse the tabular XML file and return a flat list of entity dictionaries with parent-child linkages.
        """
        if not self.xml_filepath.exists():
            raise FileNotFoundError(f"CDC ICD-10-CM XML file not found at {self.xml_filepath}")

        api_logger.info(f"Parsing CDC ICD-10-CM Tabular XML file from {self.xml_filepath}...")
        tree = ET.parse(self.xml_filepath)
        root = tree.getroot()

        entities: List[Dict[str, Any]] = []

        # Root Node entity
        root_entity = {
            "uri": "https://www.icd10data.com/ICD10CM/Codes",
            "code": "ICD10CM-2026",
            "title": "2026 ICD-10-CM Codes (CDC FY 2026 Release)",
            "is_header": True,
            "parent": [],
            "child": [],
            "chapter_name": "Root",
        }
        entities.append(root_entity)

        chapters = root.findall("chapter")
        for chap in chapters:
            chap_name_num = chap.findtext("name", "").strip()
            chap_desc = chap.findtext("desc", "").strip()

            # Extract range code from description e.g. "Certain infectious and parasitic diseases (A00-B99)"
            range_code = ""
            if "(" in chap_desc and chap_desc.endswith(")"):
                range_code = chap_desc.split("(")[-1].rstrip(")").strip()

            chap_code = range_code or f"CHAPTER-{chap_name_num}"
            chap_url_path = f"https://www.icd10data.com/ICD10CM/Codes/{chap_code}"

            chap_entity = {
                "uri": chap_url_path,
                "code": chap_code,
                "title": chap_desc,
                "is_header": True,
                "parent": [root_entity["uri"]],
                "child": [],
                "chapter_name": chap_desc,
                "url_path": chap_url_path,
                "includes": self._extract_notes(chap, "includes"),
                "exclusions": self._extract_notes(chap, "excludes1") + self._extract_notes(chap, "excludes2"),
            }
            root_entity["child"].append(chap_url_path)
            entities.append(chap_entity)

            sections = chap.findall("section")
            for sec in sections:
                sec_id = sec.get("id", "").strip()
                sec_desc = sec.findtext("desc", "").strip()
                sec_url_path = f"{chap_url_path}/{sec_id}"

                sec_entity = {
                    "uri": sec_url_path,
                    "code": sec_id,
                    "title": sec_desc,
                    "is_header": True,
                    "parent": [chap_url_path],
                    "child": [],
                    "chapter_name": chap_desc,
                    "section_name": sec_desc,
                    "url_path": sec_url_path,
                    "includes": self._extract_notes(sec, "includes"),
                    "exclusions": self._extract_notes(sec, "excludes1") + self._extract_notes(sec, "excludes2"),
                }
                chap_entity["child"].append(sec_url_path)
                entities.append(sec_entity)

                # Process recursive diagnostic codes under section
                diags = sec.findall("diag")
                for d in diags:
                    cat_3 = d.findtext("name", "").strip()[:3]
                    self._parse_diag_node(d, parent_uri=sec_url_path, parent_url_path=sec_url_path, chap_desc=chap_desc, sec_desc=sec_desc, chap_code=chap_code, sec_id=sec_id, cat_3=cat_3, entities=entities)

        api_logger.info(f"CDC ICD-10-CM Tabular XML parsing complete. Extracted {len(entities)} total entities.")
        return entities

    def _parse_diag_node(self, diag_node: ET.Element, parent_uri: str, parent_url_path: str, chap_desc: str, sec_desc: str, chap_code: str, sec_id: str, cat_3: str, entities: List[Dict[str, Any]]) -> str:
        """Recursively parse a diag node using exact 4-part icd10data.com URL path."""
        code = diag_node.findtext("name", "").strip()
        desc = diag_node.findtext("desc", "").strip()

        sub_diags = diag_node.findall("diag")
        is_header = len(sub_diags) > 0

        # Exact 4-part URL path for icd10data.com: /Codes/{chap_code}/{sec_id}/{cat_3}-/{code}
        if is_header and len(code) <= 3:
            url_path = f"https://www.icd10data.com/ICD10CM/Codes/{chap_code}/{sec_id}/{code}-"
        else:
            url_path = f"https://www.icd10data.com/ICD10CM/Codes/{chap_code}/{sec_id}/{cat_3}-/{code}"

        diag_entity = {
            "uri": url_path,
            "code": code,
            "title": desc,
            "is_header": is_header,
            "parent": [parent_uri],
            "child": [],
            "chapter_name": chap_desc,
            "section_name": sec_desc,
            "url_path": url_path,
            "includes": self._extract_notes(diag_node, "includes"),
            "exclusions": self._extract_notes(diag_node, "excludes1") + self._extract_notes(diag_node, "excludes2"),
        }

        entities.append(diag_entity)

        # Recursively process children
        for child_diag in sub_diags:
            child_uri = self._parse_diag_node(child_diag, parent_uri=url_path, parent_url_path=url_path, chap_desc=chap_desc, sec_desc=sec_desc, chap_code=chap_code, sec_id=sec_id, cat_3=cat_3, entities=entities)
            diag_entity["child"].append(child_uri)

        return url_path
