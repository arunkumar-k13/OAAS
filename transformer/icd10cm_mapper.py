"""
Mapper transforming CDC 2026 ICD-10-CM entities into OAAS Ontology Schema documents.
"""

from typing import Any, Dict, List
from models.ontology import OAASOntologyTerm
from transformer.normalizer import extract_label_value, normalize_list, normalize_text
from utils.logger import mapping_logger


class ICD10CMMapper:
    """Transforms parsed CDC ICD-10-CM XML entities into OAAS Ontology schema models."""

    def __init__(self):
        self.order_desc_map = self._load_order_file_map()
        self.index_synonyms_map = self._load_index_synonyms_map()

    def _load_index_synonyms_map(self) -> Dict[str, List[str]]:
        """Load synonyms and alphabetical index terms from CDC Index XML file."""
        import xml.etree.ElementTree as ET
        from pathlib import Path

        index_xml = Path("data/cdc_2026_xml/icd10cm-index-April-1-2026-XML.xml")
        syn_map: Dict[str, List[str]] = {}
        if not index_xml.exists():
            return syn_map

        def parse_term(term_node, prefix=""):
            title = term_node.findtext("title", "").strip()
            code = term_node.findtext("code", "").strip()
            full_title = f"{prefix} {title}".strip() if prefix else title

            if code:
                if code not in syn_map:
                    syn_map[code] = []
                if full_title and full_title not in syn_map[code]:
                    syn_map[code].append(full_title)

            for child in term_node.findall("term"):
                parse_term(child, full_title)

        try:
            tree = ET.parse(index_xml)
            root = tree.getroot()
            for letter in root.findall("letter"):
                for main in letter.findall("mainTerm"):
                    parse_term(main)
        except Exception as err:
            mapping_logger.warning(f"Failed to load CDC index XML synonyms: {err}")

        return syn_map

    def _load_order_file_map(self) -> Dict[str, Dict[str, str]]:
        """Load short and long descriptions from CDC icd10cm-order-2026.txt if available."""
        from pathlib import Path
        order_file = Path("data/cdc_2026/icd10cm-order-2026.txt")
        desc_map = {}
        if order_file.exists():
            try:
                with open(order_file, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if len(line) >= 77:
                            raw_code = line[6:13].strip()
                            short_desc = line[16:77].strip()
                            long_desc = line[77:].strip()
                            desc_map[raw_code] = {
                                "short_desc": short_desc,
                                "long_desc": long_desc,
                            }
            except Exception as err:
                mapping_logger.warning(f"Failed to load order file descriptions: {err}")
        return desc_map

    def map_entity(self, raw_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map a single raw CDC ICD-10-CM dictionary to OAAS Ontology Schema dictionary.
        """
        uri = normalize_text(raw_json.get("uri"))
        code = normalize_text(raw_json.get("code"))
        name = extract_label_value(raw_json.get("title"))

        if not name:
            name = f"Unnamed ICD-10-CM Entity ({code})"

        chapter_name = normalize_text(raw_json.get("chapter_name"))
        if not chapter_name or chapter_name == "None":
            chapter_name = "General"

        section_name = normalize_text(raw_json.get("section_name"))

        is_header = raw_json.get("is_header", False)
        for_mapping = not is_header

        # Inclusions & Exclusions
        inclusions = normalize_list(raw_json.get("includes", []))
        exclusions = normalize_list(raw_json.get("exclusions", []))

        # Definition from inclusions if available
        definition = " | ".join(inclusions) if inclusions else ""

        # Descriptions: Short vs Long Distinction
        raw_code_key = code.replace(".", "")
        order_info = self.order_desc_map.get(raw_code_key, {})
        short_desc = order_info.get("short_desc") or name
        
        # Build expanded Long Description combining full title + section context + chapter context
        long_base = order_info.get("long_desc") or name
        context_parts = [long_base]
        if section_name and section_name != "None":
            context_parts.append(f"Section: {section_name}")
        if chapter_name and chapter_name != "General":
            context_parts.append(f"Chapter: {chapter_name}")
        if inclusions:
            context_parts.append(f"Includes: {', '.join(inclusions)}")

        long_desc = " | ".join(context_parts)

        # Parents & Children URIs
        parents = normalize_list(raw_json.get("parent", []))
        children = normalize_list(raw_json.get("child", []))

        # Term ID Construction: [code, ICD10:code]
        term_id_list = []
        if code:
            term_id_list.append(code)
            term_id_list.append(f"ICD10:{code}")

        seen = set()
        dedup_term_ids = []
        for tid in term_id_list:
            if tid and tid not in seen:
                seen.add(tid)
                dedup_term_ids.append(tid)

        # Exact 100% 200 OK BrowserUrl format matching icd10data.com
        browser_url = raw_json.get("url_path") or uri or f"https://www.icd10data.com/ICD10CM/Codes/{code}"

        # Look up synonyms from CDC Index XML map
        synonyms = self.index_synonyms_map.get(code, [])

        term_model = OAASOntologyTerm(
            Name=name,
            ID="",  # Blank for Lexicon sequence auto-generation
            Term_ID=dedup_term_ids,
            URI=uri,
            BrowserUrl=browser_url,
            Synonyms=synonyms,
            Short_Description=short_desc,
            Long_Description=long_desc,
            Condition_Group=chapter_name,
            hasDbXref=[],
            Definition=definition,
            Type_I_Exclude=exclusions,
            Type_II_Exclude=[],
            Includes=inclusions,
            Applicable_To=[],
            forMapping=for_mapping,
            mcXref=[],
            Version="ICD-10-CM 2026",
            PossiblePrefix="ICD10",
            superClassOf=children,
            subClassOf=parents,
        )

        return term_model.model_dump(by_alias=True)

    def map_batch(self, raw_documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Map a batch of raw CDC ICD-10-CM entities."""
        mapped = []
        for doc in raw_documents:
            mapped.append(self.map_entity(doc))
        return mapped
