"""
Production CLI command handlers powered by Rich terminal formatting.
"""

import sys
import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.status import Status

from config.constants import ALL_COLLECTIONS, COLLECTION_PROCESSED, COLLECTION_VALIDATION_LOGS
from database.indexes import create_all_indexes
from database.mongo import db_healthcheck, get_db
from database.repositories import (
    BaseRepository,
    FinalOntologyRepository,
    LoggingRepository,
    ProcessedOntologyRepository,
    RawDataRepository,
)
from extractor.downloader import ICD11Downloader
from transformer.hierarchy import HierarchyGenerator
from transformer.mapper import ICD11Mapper
from transformer.validator import OntologyValidator

console = Console()


def handle_fetch(max_depth: Optional[int] = None):
    """Fetch ICD-11 terminology from WHO API."""
    console.print(Panel("[bold blue]WHO ICD-11 Terminology Fetcher[/bold blue]", expand=False))
    if not db_healthcheck():
        console.print("[bold red]Error: MongoDB is unreachable! Please ensure MongoDB is running on the configured URI.[/bold red]")
        sys.exit(1)

    start_time = time.time()
    downloader = ICD11Downloader()
    count = downloader.download_hierarchy(max_depth=max_depth)
    elapsed = time.time() - start_time

    console.print(f"[bold green]Fetch completed successfully! {count} entities downloaded in {elapsed:.2f}s.[/bold green]")


def handle_transform():
    """Transform raw ICD-11 JSON to OAAS ontology schema with bidirectional hierarchy."""
    console.print(Panel("[bold magenta]OAAS Schema Transformer & Hierarchy Generator[/bold magenta]", expand=False))
    if not db_healthcheck():
        console.print("[bold red]Error: MongoDB is unreachable![/bold red]")
        sys.exit(1)

    start_time = time.time()
    raw_repo = RawDataRepository()
    processed_repo = ProcessedOntologyRepository()
    final_repo = FinalOntologyRepository()
    mapper = ICD11Mapper()
    hierarchy_gen = HierarchyGenerator()

    with Status("[bold cyan]Fetching raw documents from icd11_raw...", console=console):
        raw_entities = raw_repo.fetch_all_raw_documents()

    if not raw_entities:
        console.print("[yellow]No raw entity documents found in `icd11_raw`. Please run `python main.py fetch` first.[/yellow]")
        return

    with Status(f"[bold cyan]Mapping {len(raw_entities)} raw documents to OAAS schema...", console=console):
        mapped_terms = mapper.map_batch(raw_entities)

    with Status("[bold cyan]Generating bidirectional superClassOf / subClassOf hierarchy...", console=console):
        linked_terms = hierarchy_gen.build_bidirectional_links(mapped_terms)

    with Status("[bold cyan]Persisting terms to MongoDB collections...", console=console):
        from database.indexes import create_all_indexes
        db = get_db()
        processed_repo.drop()
        create_all_indexes(db)
        saved_count = processed_repo.bulk_upsert(linked_terms)
        synced_count = final_repo.sync_from_processed()

    # Record mapping log
    logger_repo = LoggingRepository()
    logger_repo.log_mapping_run(total_raw=len(raw_entities), total_mapped=saved_count)

    elapsed = time.time() - start_time
    console.print(f"[bold green]Transformation complete! {saved_count} terms mapped and synced in {elapsed:.2f}s.[/bold green]")


def handle_validate():
    """Validate ontology hierarchy and required metadata."""
    console.print(Panel("[bold yellow]OAAS Ontology Validation Engine[/bold yellow]", expand=False))
    if not db_healthcheck():
        console.print("[bold red]Error: MongoDB is unreachable![/bold red]")
        sys.exit(1)

    db = get_db()
    processed_col = db[COLLECTION_PROCESSED]

    with Status("[bold cyan]Loading processed terms for validation...", console=console):
        terms = list(processed_col.find({}, {"_id": 0}))

    if not terms:
        console.print("[yellow]No terms found in `icd11_processed`. Please run `python main.py transform` first.[/yellow]")
        return

    with Status(f"[bold cyan]Validating {len(terms)} terms...", console=console):
        validator = OntologyValidator()
        report = validator.validate(terms)

    # Render Validation Report Table
    table = Table(title=f"Ontology Validation Summary (Total Entities: {report.total_entities_validated})")
    table.add_column("Validation Metric", style="cyan")
    table.add_column("Count / Status", style="magenta", justify="right")

    table.add_row("Missing Names", str(report.missing_names))
    table.add_row("Missing Codes", str(report.missing_codes))
    table.add_row("Duplicate IDs", str(report.duplicate_ids))
    table.add_row("Broken Hierarchy Links", str(report.broken_hierarchy))
    table.add_row("Circular References", str(report.circular_references))
    table.add_row("Root Entities (No Parents)", str(report.missing_parents))
    table.add_row("Leaf Entities (No Children)", str(report.missing_children))
    table.add_row("Duplicate Synonyms", str(report.duplicate_synonyms))

    status_str = "[bold green]PASSED[/bold green]" if report.is_valid else "[bold red]FAILED[/bold red]"
    table.add_row("Overall Status", status_str)

    console.print(table)

    # Store validation log in validation_logs collection
    from datetime import datetime, timezone

    log_doc = report.model_dump()
    log_doc["timestamp"] = datetime.now(timezone.utc).isoformat()
    db[COLLECTION_VALIDATION_LOGS].insert_one(log_doc)
    console.print("[dim]Validation report logged to `validation_logs` collection.[/dim]")


def handle_export():
    """Export ontology data to JSON, CSV, and OAAS Lexicon formats."""
    console.print(Panel("[bold green]OAAS Multi-Format Exporter[/bold green]", expand=False))
    if not db_healthcheck():
        console.print("[bold red]Error: MongoDB is unreachable![/bold red]")
        sys.exit(1)

    final_repo = FinalOntologyRepository()
    with Status("[bold cyan]Querying final ICD11_2026_ONTOLOGY collection...", console=console):
        terms = list(final_repo.collection.find({}, {"_id": 0}))

    if not terms:
        console.print("[yellow]No terms found in `ICD11_2026_ONTOLOGY`. Please run `python main.py transform` first.[/yellow]")
        return

    from exporter.csv_export import export_csv
    from exporter.json_export import export_json
    from exporter.oaas_export import export_oaas_format

    with Status("[bold cyan]Exporting files...", console=console):
        json_path = export_json(terms)
        csv_path = export_csv(terms)
        oaas_path = export_oaas_format(terms)

    # Log export runs
    logger_repo = LoggingRepository()
    logger_repo.log_import_run("JSON", len(terms), str(json_path))
    logger_repo.log_import_run("CSV", len(terms), str(csv_path))
    logger_repo.log_import_run("OAAS_IMPORT_JSON", len(terms), str(oaas_path))

    # Display Rich summary table
    table = Table(title=f"Export Summary ({len(terms)} Terms Exported)")
    table.add_column("Export Format", style="cyan")
    table.add_column("File Path", style="green")

    table.add_row("Standard JSON", str(json_path))
    table.add_row("Flat CSV", str(csv_path))
    table.add_row("OAAS Lexicon Import JSON", str(oaas_path))

    console.print(table)
    console.print("[dim]Export runs logged to `import_logs` collection.[/dim]")


def handle_stats():
    """Display database stats and collection counts."""
    console.print(Panel("[bold cyan]OAAS Database Statistics[/bold cyan]", expand=False))

    if not db_healthcheck():
        console.print("[bold red]Error: MongoDB is unreachable![/bold red]")
        sys.exit(1)

    db = get_db()
    table = Table(title="MongoDB Collections (Database: oaas)")
    table.add_column("Collection Name", style="cyan")
    table.add_column("Document Count", style="green", justify="right")

    for col in ALL_COLLECTIONS:
        count = db[col].count_documents({})
        table.add_row(col, str(count))

    console.print(table)


def handle_reset():
    """Clear all pipeline collections in the oaas database."""
    console.print(Panel("[bold red]Resetting OAAS Database Collections[/bold red]", expand=False))
    if not db_healthcheck():
        console.print("[bold red]Error: MongoDB is unreachable![/bold red]")
        sys.exit(1)

    db = get_db()
    with Status("[bold red]Dropping collections and recreating indexes...", console=console):
        for col in ALL_COLLECTIONS:
            db[col].drop()
            console.print(f"Dropped collection: [dim]{col}[/dim]")

        create_all_indexes(db)
    console.print("[bold green]Reset completed successfully. All collections dropped and re-indexed.[/bold green]")


def handle_fetch_icd10():
    """Fetch ICD-10 terminology from WHO API."""
    console.print(Panel("[bold blue]WHO ICD-10 Terminology Fetcher (2019 Release)[/bold blue]", expand=False))
    if not db_healthcheck():
        console.print("[bold red]Error: MongoDB is unreachable![/bold red]")
        sys.exit(1)

    start_time = time.time()
    from extractor.icd10_downloader import ICD10Downloader
    downloader = ICD10Downloader()
    count = downloader.download_hierarchy()
    elapsed = time.time() - start_time
    console.print(f"[bold green]ICD-10 Download complete! {count} new entities downloaded in {elapsed:.2f}s.[/bold green]")


def handle_transform_icd10():
    """Transform raw ICD-10 JSON entities to OAAS Schema and build hierarchy."""
    console.print(Panel("[bold magenta]OAAS ICD-10 Schema Transformer & Hierarchy Generator[/bold magenta]", expand=False))
    if not db_healthcheck():
        console.print("[bold red]Error: MongoDB is unreachable![/bold red]")
        sys.exit(1)

    start_time = time.time()
    from database.repositories import ICD10RawRepository, ICD10ProcessedRepository, ICD10FinalRepository
    from transformer.icd10_mapper import ICD10Mapper
    from transformer.icd10_hierarchy import ICD10HierarchyGenerator

    raw_repo = ICD10RawRepository()
    processed_repo = ICD10ProcessedRepository()
    final_repo = ICD10FinalRepository()
    mapper = ICD10Mapper()
    hierarchy_gen = ICD10HierarchyGenerator()

    with Status("[bold cyan]Fetching raw ICD-10 documents...", console=console):
        raw_entities = raw_repo.fetch_all_raw_documents()

    if not raw_entities:
        console.print("[yellow]No raw ICD-10 documents found in `icd10_raw`. Please run `python main.py fetch-icd10` first.[/yellow]")
        return

    with Status(f"[bold cyan]Mapping {len(raw_entities)} raw ICD-10 documents...", console=console):
        mapped_terms = mapper.map_batch(raw_entities)

    with Status("[bold cyan]Generating ICD-10 hierarchy links...", console=console):
        linked_terms = hierarchy_gen.build_bidirectional_links(mapped_terms)

    with Status("[bold cyan]Persisting ICD-10 terms to MongoDB...", console=console):
        db = get_db()
        processed_repo.drop()
        create_all_indexes(db)
        saved_count = processed_repo.bulk_upsert(linked_terms)
        synced_count = final_repo.sync_from_processed()

    elapsed = time.time() - start_time
    console.print(f"[bold green]ICD-10 Transformation complete! {saved_count} terms mapped and synced in {elapsed:.2f}s.[/bold green]")


def handle_export_icd10():
    """Export transformed ICD-10 ontology terms to CSV and JSON."""
    console.print(Panel("[bold yellow]OAAS ICD-10 Multi-Format Exporter[/bold yellow]", expand=False))
    if not db_healthcheck():
        console.print("[bold red]Error: MongoDB is unreachable![/bold red]")
        sys.exit(1)

    from database.repositories import ICD10FinalRepository
    from exporter.csv_export import export_csv
    from exporter.json_export import export_json
    from config.constants import OUTPUT_DIR

    final_repo = ICD10FinalRepository()
    terms = final_repo.get_all_terms()

    if not terms:
        console.print("[yellow]No terms found in `ICD10_2019_ONTOLOGY`. Please run `python main.py transform-icd10` first.[/yellow]")
        return

    json_path = OUTPUT_DIR / "icd10_ontology.json"
    csv_path = OUTPUT_DIR / "icd10_ontology.csv"

    export_json(terms, filepath=json_path)
    csv_out = export_csv(terms, filepath=csv_path)

    table = Table(title=f"ICD-10 Export Summary ({len(terms)} Terms Exported)")
    table.add_column("Export Format", style="cyan")
    table.add_column("File Path", style="green")
    table.add_row("Standard JSON", str(json_path))
    table.add_row("Flat CSV", str(csv_out))

    console.print(table)


def handle_fetch_icd10cm():
    """Fetch/Parse CDC FY 2026 ICD-10-CM Tabular XML release."""
    console.print(Panel("[bold blue]CDC FY 2026 ICD-10-CM Parser & Extractor[/bold blue]", expand=False))
    if not db_healthcheck():
        console.print("[bold red]Error: MongoDB is unreachable![/bold red]")
        sys.exit(1)

    start_time = time.time()
    from extractor.icd10cm_xml_parser import ICD10CMXMLParser
    from database.repositories import ICD10CMRawRepository

    parser = ICD10CMXMLParser()
    raw_repo = ICD10CMRawRepository()

    with Status("[bold cyan]Parsing CDC ICD-10-CM Tabular XML file...", console=console):
        entities = parser.parse()

    with Status("[bold cyan]Storing raw ICD-10-CM entities in MongoDB...", console=console):
        raw_repo.drop()
        for ent in entities:
            raw_repo.collection.insert_one(ent)

    elapsed = time.time() - start_time
    console.print(f"[bold green]ICD-10-CM Ingestion complete! {len(entities)} entities extracted and saved in {elapsed:.2f}s.[/bold green]")


def handle_transform_icd10cm():
    """Transform raw 2026 ICD-10-CM XML entities to OAAS Schema and build hierarchy."""
    console.print(Panel("[bold magenta]OAAS 2026 ICD-10-CM Schema Transformer & Hierarchy Generator[/bold magenta]", expand=False))
    if not db_healthcheck():
        console.print("[bold red]Error: MongoDB is unreachable![/bold red]")
        sys.exit(1)

    start_time = time.time()
    from database.repositories import ICD10CMRawRepository, ICD10CMProcessedRepository, ICD10CMFinalRepository
    from transformer.icd10cm_mapper import ICD10CMMapper
    from transformer.icd10_hierarchy import ICD10HierarchyGenerator

    raw_repo = ICD10CMRawRepository()
    processed_repo = ICD10CMProcessedRepository()
    final_repo = ICD10CMFinalRepository()
    mapper = ICD10CMMapper()
    hierarchy_gen = ICD10HierarchyGenerator()

    with Status("[bold cyan]Fetching raw ICD-10-CM documents...", console=console):
        raw_entities = list(raw_repo.collection.find({}, {"_id": 0}))

    if not raw_entities:
        console.print("[yellow]No raw ICD-10-CM entities found. Please run `python main.py fetch-icd10cm` first.[/yellow]")
        return

    with Status(f"[bold cyan]Mapping {len(raw_entities)} raw ICD-10-CM entities...", console=console):
        mapped_terms = mapper.map_batch(raw_entities)

    with Status("[bold cyan]Generating 2026 ICD-10-CM hierarchy links...", console=console):
        linked_terms = hierarchy_gen.build_bidirectional_links(mapped_terms)

    with Status("[bold cyan]Persisting 2026 ICD-10-CM terms to MongoDB...", console=console):
        db = get_db()
        processed_repo.drop()
        create_all_indexes(db)
        saved_count = processed_repo.bulk_upsert(linked_terms)
        synced_count = final_repo.sync_from_processed()

    elapsed = time.time() - start_time
    console.print(f"[bold green]2026 ICD-10-CM Transformation complete! {saved_count} terms mapped and synced in {elapsed:.2f}s.[/bold green]")


def handle_export_icd10cm():
    """Export transformed 2026 ICD-10-CM ontology terms to CSV and JSON."""
    console.print(Panel("[bold yellow]OAAS 2026 ICD-10-CM Multi-Format Exporter[/bold yellow]", expand=False))
    if not db_healthcheck():
        console.print("[bold red]Error: MongoDB is unreachable![/bold red]")
        sys.exit(1)

    from database.repositories import ICD10CMFinalRepository
    from exporter.csv_export import export_csv
    from exporter.json_export import export_json
    from config.constants import OUTPUT_DIR

    final_repo = ICD10CMFinalRepository()
    terms = final_repo.get_all_terms()

    if not terms:
        console.print("[yellow]No terms found in `ICD10CM_2026_ONTOLOGY`. Please run `python main.py transform-icd10cm` first.[/yellow]")
        return

    json_path = OUTPUT_DIR / "icd10_cm_2026_ontology.json"
    csv_path = OUTPUT_DIR / "icd10_cm_2026_ontology.csv"

    export_json(terms, filepath=json_path)
    csv_out = export_csv(terms, filepath=csv_path)

    table = Table(title=f"2026 ICD-10-CM Export Summary ({len(terms)} Terms Exported)")
    table.add_column("Export Format", style="cyan")
    table.add_column("File Path", style="green")
    table.add_row("Standard JSON", str(json_path))
    table.add_row("Flat CSV", str(csv_out))

    console.print(table)


# =====================================================================
# MeSH 2026 CLI Command Handlers
# =====================================================================

def handle_fetch_mesh(xml_filepath: Optional[str] = None):
    """Fetch/Parse MeSH 2026 Ontology raw data."""
    console.print(Panel("[bold cyan]NLM MeSH 2026 Ontology Fetcher/Parser[/bold cyan]", expand=False))
    if not db_healthcheck():
        console.print("[bold red]Error: MongoDB is unreachable![/bold red]")
        sys.exit(1)

    from extractor.mesh_downloader import MeSHDownloader
    from pathlib import Path

    start_time = time.time()
    downloader = MeSHDownloader()
    path_obj = Path(xml_filepath) if xml_filepath else None
    count = downloader.download_or_parse_mesh_xml(xml_filepath=path_obj)
    elapsed = time.time() - start_time

    console.print(f"[bold green]MeSH fetch/seed completed successfully! {count} entities stored in {elapsed:.2f}s.[/bold green]")


def handle_transform_mesh():
    """Transform raw MeSH data into Descriptor, Concept, and Qualifier schemas with hierarchy."""
    console.print(Panel("[bold magenta]MeSH 2026 Schema Transformer & Hierarchy Generator[/bold magenta]", expand=False))
    if not db_healthcheck():
        console.print("[bold red]Error: MongoDB is unreachable![/bold red]")
        sys.exit(1)

    from config.constants import COLLECTION_MESH_RAW, COLLECTION_MESH_PROCESSED, COLLECTION_MESH_ONTOLOGY
    from transformer.mesh_mapper import MeSHMapper
    from transformer.mesh_hierarchy import MeSHHierarchyGenerator
    from database.indexes import create_all_indexes

    db = get_db()
    raw_col = db[COLLECTION_MESH_RAW]
    processed_col = db[COLLECTION_MESH_PROCESSED]
    final_col = db[COLLECTION_MESH_ONTOLOGY]

    raw_docs = list(raw_col.find({}, {"_id": 0}))
    if not raw_docs:
        console.print("[yellow]No raw MeSH documents found. Running initial fetch/seed...[/yellow]")
        from extractor.mesh_downloader import MeSHDownloader
        downloader = MeSHDownloader(db=db)
        downloader.download_or_parse_mesh_xml()
        raw_docs = list(raw_col.find({}, {"_id": 0}))

    mapper = MeSHMapper()
    hierarchy_gen = MeSHHierarchyGenerator()

    mapped_terms = mapper.transform_batch(raw_docs)
    linked_terms = hierarchy_gen.build_bidirectional_links(mapped_terms)

    processed_col.delete_many({})
    final_col.delete_many({})

    if linked_terms:
        processed_col.insert_many(linked_terms)
        final_col.insert_many([dict(t) for t in linked_terms])

    console.print(f"[bold green]MeSH Transformation complete! {len(linked_terms)} unique terms mapped and synced.[/bold green]")


def handle_export_mesh():
    """Export transformed MeSH 2026 ontology to clean deduplicated CSV."""
    console.print(Panel("[bold green]MeSH 2026 Ontology Exporter[/bold green]", expand=False))
    if not db_healthcheck():
        console.print("[bold red]Error: MongoDB is unreachable![/bold red]")
        sys.exit(1)

    from config.constants import COLLECTION_MESH_ONTOLOGY, OUTPUT_DIR
    from exporter.mesh_export import export_mesh_csv

    db = get_db()
    final_col = db[COLLECTION_MESH_ONTOLOGY]
    terms = list(final_col.find({}, {"_id": 0}))

    if not terms:
        console.print("[yellow]No terms found in `MESH_2026_ONTOLOGY`. Running transform-mesh first...[/yellow]")
        handle_transform_mesh()
        terms = list(final_col.find({}, {"_id": 0}))

    out_csv = export_mesh_csv(terms)

    table = Table(title=f"MeSH 2026 Export Summary ({len(terms)} Terms Exported)")
    table.add_column("Export Format", style="cyan")
    table.add_column("File Path", style="green")
    table.add_row("Deduplicated CSV", str(out_csv))

    console.print(table)


# =====================================================================
# LOINC 2026 CLI Command Handlers
# =====================================================================

def handle_fetch_loinc(filepath: Optional[str] = None):
    """Fetch/Parse LOINC 2026 CSV release data into MongoDB."""
    console.print(Panel("[bold cyan]Regenstrief LOINC 2026 Parser & Extractor[/bold cyan]", expand=False))
    if not db_healthcheck():
        console.print("[bold red]Error: MongoDB is unreachable![/bold red]")
        sys.exit(1)

    from extractor.loinc_parser import LOINCParser
    from pathlib import Path

    start_time = time.time()
    parser = LOINCParser()

    if filepath:
        path_obj = Path(filepath)
    else:
        # Default data directory
        data_dir = Path(r"c:\Users\arun.kumar\Desktop\MC\OAS\data\loinc")
        # Try to find CSV or ZIP file
        candidates = list(data_dir.glob("*.zip")) + list(data_dir.glob("Loinc.csv")) + list(data_dir.glob("LoincTableCore.csv"))
        if not candidates:
            console.print(f"[bold red]No LOINC files found in {data_dir}![/bold red]")
            console.print("[yellow]Please download the LOINC release from https://loinc.org/downloads/ and place it in the data/loinc/ directory.[/yellow]")
            sys.exit(1)
        path_obj = candidates[0]
        console.print(f"[dim]Found LOINC file: {path_obj}[/dim]")

    count = parser.parse_and_ingest(path_obj)
    elapsed = time.time() - start_time

    console.print(f"[bold green]LOINC fetch/parse completed! {count:,} records stored in {elapsed:.2f}s.[/bold green]")


def handle_transform_loinc():
    """Transform raw LOINC data into Lexicon-ready ontology schema with hierarchy."""
    console.print(Panel("[bold magenta]LOINC 2026 Schema Transformer & Hierarchy Generator[/bold magenta]", expand=False))
    if not db_healthcheck():
        console.print("[bold red]Error: MongoDB is unreachable![/bold red]")
        sys.exit(1)

    from config.constants import COLLECTION_LOINC_RAW, COLLECTION_LOINC_PROCESSED, COLLECTION_LOINC_ONTOLOGY
    from transformer.loinc_mapper import LOINCMapper
    from transformer.loinc_hierarchy import LOINCHierarchyGenerator
    from database.indexes import create_all_indexes

    start_time = time.time()
    db = get_db()
    raw_col = db[COLLECTION_LOINC_RAW]
    processed_col = db[COLLECTION_LOINC_PROCESSED]
    final_col = db[COLLECTION_LOINC_ONTOLOGY]

    with Status("[bold cyan]Fetching raw LOINC documents...", console=console):
        raw_docs = list(raw_col.find({}, {"_id": 0}))

    if not raw_docs:
        console.print("[yellow]No raw LOINC documents found. Please run `python main.py fetch-loinc` first.[/yellow]")
        return

    console.print(f"[dim]Found {len(raw_docs):,} raw LOINC documents.[/dim]")

    with Status(f"[bold cyan]Mapping {len(raw_docs):,} raw LOINC documents to Lexicon schema...", console=console):
        mapper = LOINCMapper()
        mapped_terms = mapper.transform_batch(raw_docs)

    with Status("[bold cyan]Generating LOINC hierarchy links...", console=console):
        hierarchy_gen = LOINCHierarchyGenerator(db=db)
        linked_terms = hierarchy_gen.build_bidirectional_links(mapped_terms)

    with Status("[bold cyan]Persisting LOINC terms to MongoDB...", console=console):
        processed_col.delete_many({})
        final_col.delete_many({})

        if linked_terms:
            # Batch insert in chunks of 10,000
            batch_size = 10000
            for i in range(0, len(linked_terms), batch_size):
                batch = linked_terms[i:i + batch_size]
                processed_col.insert_many(batch)
                final_col.insert_many([dict(t) for t in batch])

    elapsed = time.time() - start_time
    console.print(f"[bold green]LOINC Transformation complete! {len(linked_terms):,} unique terms mapped and synced in {elapsed:.2f}s.[/bold green]")


def handle_export_loinc():
    """Export transformed LOINC 2026 ontology to CSV and Multi-Sheet Excel."""
    console.print(Panel("[bold green]LOINC 2026 Ontology Exporter[/bold green]", expand=False))
    if not db_healthcheck():
        console.print("[bold red]Error: MongoDB is unreachable![/bold red]")
        sys.exit(1)

    from config.constants import COLLECTION_LOINC_ONTOLOGY, OUTPUT_DIR
    from exporter.loinc_export import export_loinc_csv, export_loinc_excel

    db = get_db()
    final_col = db[COLLECTION_LOINC_ONTOLOGY]

    with Status("[bold cyan]Querying LOINC_2026_ONTOLOGY collection...", console=console):
        terms = list(final_col.find({}, {"_id": 0}))

    if not terms:
        console.print("[yellow]No terms found in `LOINC_2026_ONTOLOGY`. Please run `python main.py transform-loinc` first.[/yellow]")
        return

    console.print(f"[dim]Exporting {len(terms):,} LOINC terms...[/dim]")

    with Status("[bold cyan]Exporting LOINC CSV...", console=console):
        csv_path = export_loinc_csv(terms)

    with Status("[bold cyan]Exporting LOINC Multi-Sheet Excel...", console=console):
        excel_path = export_loinc_excel(terms)

    table = Table(title=f"LOINC 2026 Export Summary ({len(terms):,} Terms Exported)")
    table.add_column("Export Format", style="cyan")
    table.add_column("File Path", style="green")
    table.add_row("Deduplicated CSV", str(csv_path))
    table.add_row("Multi-Sheet Excel", str(excel_path))

    console.print(table)

