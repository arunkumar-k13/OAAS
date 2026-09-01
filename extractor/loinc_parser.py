"""
LOINC 2026 CSV Parser and Extractor.
Parses LOINC CSV release files (Loinc.csv / LoincTableCore.csv) and persists to MongoDB.
"""

import csv
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from config.constants import COLLECTION_LOINC_RAW
from database.mongo import get_db
from utils.logger import api_logger


class LOINCParser:
    """Parser for Regenstrief LOINC 2026 CSV release files."""

    # Expected column names from Loinc.csv (full table)
    KEY_COLUMNS = [
        "LOINC_NUM", "COMPONENT", "PROPERTY", "TIME_ASPCT", "SYSTEM",
        "SCALE_TYP", "METHOD_TYP", "CLASS", "STATUS", "CLASSTYPE",
        "LONG_COMMON_NAME", "SHORTNAME", "CONSUMER_NAME", "ORDER_OBS",
        "UNITSREQUIRED", "RELATEDNAMES2", "VersionFirstReleased",
        "DefinitionDescription",
    ]

    def __init__(self, db=None):
        self.db = db if db is not None else get_db()
        self.raw_col = self.db[COLLECTION_LOINC_RAW]

    def parse_and_ingest(self, filepath: Path, hierarchy_filepath: Optional[Path] = None) -> int:
        """
        Parse LOINC CSV file(s) and persist raw records to MongoDB.

        Args:
            filepath: Path to the main LOINC CSV file (Loinc.csv) or ZIP archive.
            hierarchy_filepath: Optional path to MultiAxialHierarchy.csv.

        Returns:
            Total number of raw documents inserted.
        """
        # Handle ZIP archive
        if filepath.suffix.lower() == ".zip":
            return self._parse_from_zip(filepath)

        if not filepath.exists():
            api_logger.error(f"LOINC CSV file not found: {filepath}")
            raise FileNotFoundError(f"LOINC CSV file not found: {filepath}")

        self.raw_col.delete_many({})
        count = self._parse_csv_file(filepath)

        # Try to find and parse hierarchy file
        if hierarchy_filepath and hierarchy_filepath.exists():
            self._parse_hierarchy_file(hierarchy_filepath)
        else:
            # Try standard locations — search from the CSV's parent and from extraction root
            search_roots = [filepath.parent]
            # Also search from extraction root (e.g., loinc_extracted/)
            if "loinc_extracted" in str(filepath):
                extract_root = filepath
                while extract_root.name != "loinc_extracted" and extract_root != extract_root.parent:
                    extract_root = extract_root.parent
                if extract_root.name == "loinc_extracted":
                    search_roots.append(extract_root)

            hierarchy_candidates = [
                "MultiAxialHierarchy.csv",
                "AccessoryFiles/MultiAxialHierarchy/MultiAxialHierarchy.csv",
                "AccessoryFiles/ComponentHierarchyBySystem/ComponentHierarchyBySystem.csv",
                "ComponentHierarchyBySystem/ComponentHierarchyBySystem.csv",
            ]

            found_hier = False
            for root in search_roots:
                for candidate in hierarchy_candidates:
                    hier_path = root / candidate
                    if hier_path.exists():
                        self._parse_hierarchy_file(hier_path)
                        found_hier = True
                        break
                if found_hier:
                    break

            if not found_hier:
                api_logger.warning("No LOINC hierarchy file found. Hierarchy links will be empty.")

        total = self.raw_col.count_documents({})
        api_logger.info(f"Total LOINC raw documents in MongoDB: {total:,}")
        return total

    def _parse_from_zip(self, zip_path: Path) -> int:
        """Extract and parse LOINC files from a ZIP archive."""
        import tempfile
        import shutil

        extract_dir = zip_path.parent / "loinc_extracted"
        if extract_dir.exists():
            shutil.rmtree(extract_dir)

        api_logger.info(f"Extracting LOINC ZIP archive: {zip_path}")
        with zipfile.ZipFile(str(zip_path), 'r') as zf:
            zf.extractall(str(extract_dir))

        # Find the main LOINC CSV file and hierarchy file
        loinc_csv = None
        hierarchy_csv = None

        for f in extract_dir.rglob("*.csv"):
            fname_lower = f.name.lower()
            relative = str(f.relative_to(extract_dir)).replace("\\", "/").lower()

            # Prefer LoincTable/Loinc.csv over AccessoryFiles copy
            if fname_lower == "loinc.csv":
                if loinc_csv is None or "loinctable/" in relative:
                    loinc_csv = f
            elif fname_lower == "loinctablecore.csv" and loinc_csv is None:
                loinc_csv = f

            # Find hierarchy file
            if fname_lower in ("multiaxialhierarchy.csv", "componenthierarchybysystem.csv"):
                hierarchy_csv = f

        if loinc_csv is None:
            raise FileNotFoundError(
                f"Could not find Loinc.csv or LoincTableCore.csv inside ZIP: {zip_path}. "
                f"Found files: {[f.name for f in extract_dir.rglob('*.csv')]}"
            )

        api_logger.info(f"Found LOINC CSV: {loinc_csv}")
        if hierarchy_csv:
            api_logger.info(f"Found Hierarchy CSV: {hierarchy_csv}")

        return self.parse_and_ingest(loinc_csv, hierarchy_filepath=hierarchy_csv)

    def _parse_csv_file(self, filepath: Path) -> int:
        """Parse the main LOINC CSV file into MongoDB raw collection."""
        api_logger.info(f"Parsing LOINC CSV from: {filepath}")

        batch = []
        count = 0

        with open(filepath, "r", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)

            for row in reader:
                loinc_num = (row.get("LOINC_NUM") or "").strip()
                if not loinc_num:
                    continue

                # Skip deprecated/discouraged unless explicitly wanted
                status = (row.get("STATUS") or "").strip()

                doc = {
                    "loinc_num": loinc_num,
                    "component": (row.get("COMPONENT") or "").strip(),
                    "property": (row.get("PROPERTY") or "").strip(),
                    "time_aspct": (row.get("TIME_ASPCT") or "").strip(),
                    "system": (row.get("SYSTEM") or "").strip(),
                    "scale_typ": (row.get("SCALE_TYP") or "").strip(),
                    "method_typ": (row.get("METHOD_TYP") or "").strip(),
                    "class": (row.get("CLASS") or "").strip(),
                    "classtype": (row.get("CLASSTYPE") or "").strip(),
                    "status": status,
                    "long_common_name": (row.get("LONG_COMMON_NAME") or "").strip(),
                    "shortname": (row.get("SHORTNAME") or "").strip(),
                    "consumer_name": (row.get("CONSUMER_NAME") or "").strip(),
                    "order_obs": (row.get("ORDER_OBS") or "").strip(),
                    "units_required": (row.get("UNITSREQUIRED") or "").strip(),
                    "related_names": (row.get("RELATEDNAMES2") or "").strip(),
                    "version_first_released": (row.get("VersionFirstReleased") or "").strip(),
                    "definition": (row.get("DefinitionDescription") or "").strip(),
                }

                batch.append(doc)
                count += 1

                if len(batch) >= 5000:
                    self.raw_col.insert_many(batch)
                    api_logger.info(f"Inserted {count:,} LOINC records...")
                    batch.clear()

        if batch:
            self.raw_col.insert_many(batch)
            api_logger.info(f"Inserted final batch. Total: {count:,} LOINC records.")
            batch.clear()

        return count

    def _parse_hierarchy_file(self, filepath: Path) -> None:
        """
        Parse MultiAxialHierarchy.csv and store parent-child relationships
        in a separate collection field or in a lookup collection.
        We store as documents in a 'loinc_hierarchy' collection for use by the hierarchy builder.
        """
        api_logger.info(f"Parsing LOINC Multi-Axial Hierarchy from: {filepath}")

        hier_col = self.db["loinc_hierarchy"]
        hier_col.delete_many({})

        batch = []
        count = 0

        with open(filepath, "r", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)

            for row in reader:
                # MultiAxialHierarchy.csv columns:
                # PATH_TO_ROOT, SEQUENCE, IMMEDIATE_PARENT, CODE, CODE_TEXT
                code = (row.get("CODE") or "").strip()
                parent = (row.get("IMMEDIATE_PARENT") or "").strip()
                code_text = (row.get("CODE_TEXT") or "").strip()
                path_to_root = (row.get("PATH_TO_ROOT") or "").strip()

                if not code:
                    continue

                doc = {
                    "code": code,
                    "immediate_parent": parent,
                    "code_text": code_text,
                    "path_to_root": path_to_root,
                }

                batch.append(doc)
                count += 1

                if len(batch) >= 5000:
                    hier_col.insert_many(batch)
                    batch.clear()

        if batch:
            hier_col.insert_many(batch)
            batch.clear()

        api_logger.info(f"Stored {count:,} LOINC hierarchy records in 'loinc_hierarchy' collection.")
