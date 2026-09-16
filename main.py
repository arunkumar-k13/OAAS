"""
Main CLI entry point for OAAS ICD-11, ICD-10, ICD-10-CM, MeSH, LOINC, and ChEMBL Ontology ETL Pipeline.
"""

import argparse
import sys
from cli.commands import (
    handle_fetch,
    handle_transform,
    handle_validate,
    handle_export,
    handle_stats,
    handle_reset,
    handle_fetch_icd10,
    handle_transform_icd10,
    handle_export_icd10,
    handle_fetch_icd10cm,
    handle_transform_icd10cm,
    handle_export_icd10cm,
    handle_fetch_mesh,
    handle_transform_mesh,
    handle_export_mesh,
    handle_fetch_loinc,
    handle_transform_loinc,
    handle_export_loinc,
    handle_fetch_chembl,
    handle_transform_chembl,
    handle_export_chembl,
)


def main():
    parser = argparse.ArgumentParser(
        description="OAAS ICD-11, ICD-10, MeSH, LOINC & ChEMBL Ontology ETL Pipeline CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Pipeline commands")

    fetch_parser = subparsers.add_parser("fetch", help="Fetch terminology from WHO ICD-11 API")
    fetch_parser.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Optional limit on hierarchy traversal depth",
    )

    subparsers.add_parser("transform", help="Transform raw JSON into OAAS Ontology schema")
    subparsers.add_parser("validate", help="Validate ontology integrity and hierarchy")
    subparsers.add_parser("export", help="Export ontology in JSON, CSV, and OAAS formats")

    # 2026 ICD-10-CM Commands
    subparsers.add_parser("fetch-icd10cm", help="Fetch/Parse CDC FY 2026 ICD-10-CM Tabular XML release")
    subparsers.add_parser("transform-icd10cm", help="Transform raw 2026 ICD-10-CM into OAAS Schema")
    subparsers.add_parser("export-icd10cm", help="Export 2026 ICD-10-CM ontology to CSV and JSON")

    # MeSH 2026 Commands
    mesh_fetch_parser = subparsers.add_parser("fetch-mesh", help="Fetch/Parse NLM MeSH 2026 XML release data")
    mesh_fetch_parser.add_argument(
        "--filepath",
        type=str,
        default=None,
        help="Optional path to local MeSH XML file (e.g. desc2026.xml)",
    )
    subparsers.add_parser("transform-mesh", help="Transform raw MeSH into Descriptor, Concept, Qualifier schemas")
    subparsers.add_parser("export-mesh", help="Export MeSH ontology to clean deduplicated CSV")

    # LOINC 2026 Commands
    loinc_fetch_parser = subparsers.add_parser("fetch-loinc", help="Parse Regenstrief LOINC 2026 CSV release data")
    loinc_fetch_parser.add_argument(
        "--filepath",
        type=str,
        default=None,
        help="Path to LOINC CSV file or ZIP archive (e.g. Loinc_2.83.zip or Loinc.csv)",
    )
    subparsers.add_parser("transform-loinc", help="Transform raw LOINC into Lexicon-ready ontology schema")
    subparsers.add_parser("export-loinc", help="Export LOINC ontology to CSV and Multi-Sheet Excel")

    # ChEMBL 37 Commands
    chembl_fetch_parser = subparsers.add_parser("fetch-chembl", help="Fetch/Parse EMBL-EBI ChEMBL 37 bioactive compounds")
    chembl_fetch_parser.add_argument(
        "--filepath",
        type=str,
        default=None,
        help="Optional path to local ChEMBL SQLite file (e.g., chembl_37.db)",
    )
    chembl_fetch_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Sample limit for test chunks (default: None for all)",
    )
    chembl_fetch_parser.add_argument(
        "--max-phase",
        type=int,
        default=None,
        help="Minimum max_phase filter (e.g., 1 for Clinical Phase I+, 4 for Approved)",
    )
    subparsers.add_parser("transform-chembl", help="Transform raw ChEMBL into Lexicon-ready ontology schema")
    subparsers.add_parser("export-chembl", help="Export ChEMBL ontology to CSV and Multi-Sheet Excel")

    subparsers.add_parser("stats", help="Display MongoDB collection document statistics")
    subparsers.add_parser("reset", help="Clear all collections in database")

    args = parser.parse_args()

    if args.command == "fetch":
        handle_fetch(max_depth=args.max_depth)
    elif args.command == "transform":
        handle_transform()
    elif args.command == "validate":
        handle_validate()
    elif args.command == "export":
        handle_export()
    elif args.command == "fetch-icd10":
        handle_fetch_icd10()
    elif args.command == "transform-icd10":
        handle_transform_icd10()
    elif args.command == "export-icd10":
        handle_export_icd10()
    elif args.command == "fetch-icd10cm":
        handle_fetch_icd10cm()
    elif args.command == "transform-icd10cm":
        handle_transform_icd10cm()
    elif args.command == "export-icd10cm":
        handle_export_icd10cm()
    elif args.command == "fetch-mesh":
        handle_fetch_mesh(xml_filepath=args.filepath)
    elif args.command == "transform-mesh":
        handle_transform_mesh()
    elif args.command == "export-mesh":
        handle_export_mesh()
    elif args.command == "fetch-loinc":
        handle_fetch_loinc(filepath=args.filepath)
    elif args.command == "transform-loinc":
        handle_transform_loinc()
    elif args.command == "export-loinc":
        handle_export_loinc()
    elif args.command == "fetch-chembl":
        handle_fetch_chembl(filepath=args.filepath, limit=args.limit, max_phase=args.max_phase)
    elif args.command == "transform-chembl":
        handle_transform_chembl()
    elif args.command == "export-chembl":
        handle_export_chembl()
    elif args.command == "stats":
        handle_stats()
    elif args.command == "reset":
        handle_reset()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
