"""
MeSH 2026 Downloader and Extractor.
Parses NLM MeSH XML release files (Descriptors, Qualifiers, Supplementary Concepts).
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional
from config.constants import COLLECTION_MESH_RAW
from database.mongo import get_db
from utils.logger import api_logger


class MeSHDownloader:
    """Downloader and parser for NLM MeSH 2026 Ontology dataset."""

    def __init__(self, db=None):
        self.db = db if db is not None else get_db()
        self.raw_col = self.db[COLLECTION_MESH_RAW]

    def download_or_parse_mesh_xml(self, xml_filepath: Optional[Path] = None) -> int:
        """
        Parse NLM MeSH XML files (desc2026.xml, qual2026.xml, supp2026.xml) and persist to MongoDB.
        """
        data_dir = Path(r"c:\Users\arun.kumar\Desktop\MC\OAS\data\mesh")
        desc_path = xml_filepath or (data_dir / "desc2026.xml")
        qual_path = data_dir / "qual2026.xml"
        supp_path = data_dir / "supp2026.xml"

        if not desc_path.exists():
            api_logger.warning("No MeSH XML filepath provided or file not found. Seeding sample data...")
            return self._seed_mesh_sample_data()

        self.raw_col.delete_many({})
        raw_docs = []

        # 1. Parse Descriptors (D...)
        api_logger.info(f"Parsing NLM MeSH Descriptors XML from: {desc_path}")
        context_d = ET.iterparse(str(desc_path), events=("end",))
        for event, elem in context_d:
            if elem.tag == "DescriptorRecord":
                doc = self._parse_descriptor_record(elem)
                if doc:
                    raw_docs.append(doc)
                elem.clear()

            if len(raw_docs) >= 5000:
                self.raw_col.insert_many(raw_docs)
                api_logger.info(f"Inserted {len(raw_docs)} MeSH Descriptors into `{COLLECTION_MESH_RAW}`...")
                raw_docs.clear()

        if raw_docs:
            self.raw_col.insert_many(raw_docs)
            api_logger.info(f"Inserted final {len(raw_docs)} MeSH Descriptors.")
            raw_docs.clear()

        # 2. Parse Qualifiers (Q...)
        if qual_path.exists():
            api_logger.info(f"Parsing NLM MeSH Qualifiers XML from: {qual_path}")
            context_q = ET.iterparse(str(qual_path), events=("end",))
            for event, elem in context_q:
                if elem.tag == "QualifierRecord":
                    doc = self._parse_qualifier_record(elem)
                    if doc:
                        raw_docs.append(doc)
                    elem.clear()

            if raw_docs:
                self.raw_col.insert_many(raw_docs)
                api_logger.info(f"Inserted {len(raw_docs)} MeSH Qualifiers into `{COLLECTION_MESH_RAW}`.")
                raw_docs.clear()

        # 3. Parse Supplementary Concepts (C...)
        if supp_path.exists():
            api_logger.info(f"Parsing NLM MeSH Supplementary Concepts (C...) XML from: {supp_path}")
            context_s = ET.iterparse(str(supp_path), events=("end",))
            for event, elem in context_s:
                if elem.tag == "SupplementalRecord":
                    doc = self._parse_supplemental_record(elem)
                    if doc:
                        raw_docs.append(doc)
                    elem.clear()

                if len(raw_docs) >= 5000:
                    self.raw_col.insert_many(raw_docs)
                    api_logger.info(f"Inserted {len(raw_docs)} Supplementary Concepts (C...) into `{COLLECTION_MESH_RAW}`...")
                    raw_docs.clear()

            if raw_docs:
                self.raw_col.insert_many(raw_docs)
                api_logger.info(f"Inserted final {len(raw_docs)} Supplementary Concepts (C...).")
                raw_docs.clear()

        total_inserted = self.raw_col.count_documents({})
        api_logger.info(f"Total MeSH raw documents in MongoDB: {total_inserted:,}")
        return total_inserted

    def _parse_descriptor_record(self, elem: ET.Element) -> Dict[str, Any]:
        """Parse DescriptorRecord (D...) XML element."""
        descriptor_ui = elem.findtext("DescriptorUI", default="")
        descriptor_name = elem.findtext("DescriptorName/String", default="")

        tree_numbers = [tn.text.strip() for tn in elem.findall("TreeNumberList/TreeNumber") if tn.text]
        synonyms = [term.findtext("String") for term in elem.findall(".//ConceptList//TermList//Term") if term.findtext("String")]

        return {
            "ui": descriptor_ui,
            "name": descriptor_name,
            "term_type": "Descriptor",
            "tree_numbers": tree_numbers,
            "synonyms": list(set(synonyms)),
            "version": "MeSH 2026"
        }

    def _parse_qualifier_record(self, elem: ET.Element) -> Dict[str, Any]:
        """Parse QualifierRecord (Q...) XML element."""
        qualifier_ui = elem.findtext("QualifierUI", default="")
        qualifier_name = elem.findtext("QualifierName/String", default="")
        tree_numbers = [tn.text.strip() for tn in elem.findall("TreeNumberList/TreeNumber") if tn.text]

        return {
            "ui": qualifier_ui,
            "name": qualifier_name,
            "term_type": "Qualifier",
            "tree_numbers": tree_numbers,
            "synonyms": [],
            "version": "MeSH 2026"
        }

    def _parse_supplemental_record(self, elem: ET.Element) -> Dict[str, Any]:
        """Parse SupplementalRecord (C...) XML element into Concept record."""
        supp_ui = elem.findtext("SupplementalRecordUI", default="")
        supp_name = elem.findtext("SupplementalRecordName/String", default="")

        mapped_descs = []
        for h in elem.findall(".//HeadingMappedToList/HeadingMappedTo/DescriptorReferredTo"):
            d_name = h.findtext("DescriptorName/String", default="")
            if d_name and d_name not in mapped_descs:
                mapped_descs.append(d_name)

        synonyms = [term.findtext("String") for term in elem.findall(".//ConceptList//TermList//Term") if term.findtext("String")]

        return {
            "ui": supp_ui,
            "name": supp_name,
            "term_type": "Concept",
            "mapped_to_descriptor": mapped_descs,
            "tree_numbers": [],
            "synonyms": list(set(synonyms)),
            "version": "MeSH 2026"
        }

    def _seed_mesh_sample_data(self) -> int:
        """Seed sample MeSH 2026 data into MongoDB if no raw file is present."""
        sample_data = [
            {
                "ui": "D000001",
                "name": "Calcimycin",
                "term_type": "Descriptor",
                "tree_numbers": ["D03.637.100.080"],
                "synonyms": ["A23187", "Antibiotic A23187"],
                "version": "MeSH 2026"
            },
            {
                "ui": "C000002",
                "name": "bevonium",
                "term_type": "Concept",
                "mapped_to_descriptor": ["Benzilates"],
                "tree_numbers": [],
                "synonyms": ["bevonium", "Acabel"],
                "version": "MeSH 2026"
            },
            {
                "ui": "Q000008",
                "name": "administration & dosage",
                "term_type": "Qualifier",
                "tree_numbers": ["Y01"],
                "synonyms": ["administration and dosage"],
                "version": "MeSH 2026"
            }
        ]

        self.raw_col.delete_many({})
        self.raw_col.insert_many(sample_data)
        api_logger.info(f"Seeded {len(sample_data)} sample MeSH 2026 records into `{COLLECTION_MESH_RAW}`.")
        return len(sample_data)
