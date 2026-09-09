# OAAS Ontology ETL Pipeline (ICD-11, ICD-10, ICD-10-CM, MeSH & LOINC)

Production-ready, scalable, and modular Python ETL pipeline designed to extract, transform, and export medical ontology datasets into the **OAAS Lexicon Schema**. Supports **WHO ICD-11**, **WHO ICD-10**, **CDC FY 2026 ICD-10-CM**, **NLM MeSH 2026**, and **Regenstrief LOINC v2.83**.

Persists all transformed data in **MongoDB** (`oaas` database) and exports clean, deduplicated datasets for **OAAS Lexicon Import**.

---

## 📌 Supported Ontologies & Capabilities

| Ontology | Source | Version / Release | Primary Entity Types | Pipeline Commands |
| :--- | :--- | :--- | :--- | :--- |
| **ICD-11** | WHO API | 2026 Release (MMS) | Diseases, Causes of Death | `fetch`, `transform`, `export` |
| **ICD-10** | WHO API | 2019 Release | Chapters, Block Headers, Sub-codes | `fetch-icd10`, `transform-icd10`, `export-icd10` |
| **ICD-10-CM** | CDC | FY 2026 Tabular Release | Category Headers, Sub-codes | `fetch-icd10cm`, `transform-icd10cm`, `export-icd10cm` |
| **MeSH** | NLM FTP | 2026 XML Release | Descriptors (T0), Concepts (T1), Qualifiers (T2) | `fetch-mesh`, `transform-mesh`, `export-mesh` |
| **LOINC** | Regenstrief | v2.83 (August 2026) | Observation Codes, 6-Axis Parts | `fetch-loinc`, `transform-loinc`, `export-loinc` |

---

## Table of Contents

- [Project Architecture & Data Flow](#project-architecture--data-flow)
- [Folder Structure](#folder-structure)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Environment Configuration](#environment-configuration)
- [MongoDB Setup](#mongodb-setup)
- [CLI Usage & Commands](#cli-usage--commands)
- [Deduplication & Quality Rules](#deduplication--quality-rules)
- [Testing & Verification](#testing--verification)

---

## Project Architecture & Data Flow

```
                   ┌─────────────────────────────────────────┐
                   │    Data Sources (WHO / CDC / NLM / LOINC)│
                   └────────────────────┬────────────────────┘
                                        │ Extraction & Ingestion
                                        ▼
                   ┌─────────────────────────────────────────┐
                   │       MongoDB Raw Collections           │
                   │ (icd11_raw, mesh_2026_raw, loinc_raw)   │
                   └────────────────────┬────────────────────┘
                                        │ Transformation & Deduplication
                                        ▼
                   ┌─────────────────────────────────────────┐
                   │     Schema Mapping & Hierarchy Builder  │
                   │  (Pipe-merge attributes, subClassOf)    │
                   └────────────────────┬────────────────────┘
                                        │ Production Persistence
                                        ▼
                   ┌─────────────────────────────────────────┐
                   │      MongoDB Final Collections          │
                   │  (ICD11, ICD10CM, MESH, LOINC ONTOLOGY) │
                   └────────────────────┬────────────────────┘
                                        │ Multi-Format Exporter
                                        ▼
          ┌─────────────────────────────┼─────────────────────────────┐
          │                             │                             │
          ▼                             ▼                             ▼
 ┌─────────────────┐           ┌─────────────────┐           ┌──────────────────┐
 │  Lexicon CSVs   │           │ Multi-Sheet     │           │  JSON Artifacts  │
 │ (0 Dupe Errors) │           │ Excel Workbooks │           │  & Reports       │
 └─────────────────┘           └─────────────────┘           └──────────────────┘
```

---

## Folder Structure

```
OAS/
├── config/
│   ├── settings.py         # Pydantic settings loading from .env
│   ├── mapping.yaml        # YAML mapping rules for WHO -> OAAS fields
│   └── constants.py        # Collection names, schema fields, paths
│
├── extractor/
│   ├── auth.py             # Thread-safe WHO OAuth2 token manager
│   ├── icd11_client.py     # HTTP Client with rate limiting & retries
│   ├── downloader.py       # BFS hierarchy downloader
│   ├── icd10cm_xml_parser.py # CDC Tabular XML parser
│   ├── mesh_downloader.py  # NLM MeSH XML parser (Descriptors, Concepts, Qualifiers)
│   └── loinc_parser.py     # Regenstrief LOINC CSV/ZIP parser
│
├── transformer/
│   ├── mapper.py           # WHO JSON -> OAAS schema mapper
│   ├── hierarchy.py        # Bidirectional superClassOf / subClassOf generator
│   ├── mesh_mapper.py      # MeSH term mapper & pipe-merge deduplicator
│   ├── mesh_hierarchy.py   # MeSH Tree Number hierarchy builder
│   ├── loinc_mapper.py     # LOINC 6-axis mapper & name deduplicator
│   └── loinc_hierarchy.py  # LOINC component hierarchy walker
│
├── database/
│   ├── mongo.py            # PyMongo client manager & healthcheck provider
│   ├── repositories.py     # Repositories for raw, processed, final & log collections
│   └── indexes.py          # MongoDB unique, text, and compound indexes
│
├── exporter/
│   ├── json_export.py      # Formatted JSON exporter
│   ├── csv_export.py       # Pipe-delimited CSV exporter
│   ├── mesh_export.py      # MeSH multi-sheet Excel & CSV exporter
│   └── loinc_export.py     # LOINC multi-sheet Excel & CSV exporter
│
├── models/
│   ├── icd11.py            # Raw API Pydantic models
│   ├── ontology.py         # OAASOntologyTerm Pydantic schema model
│   └── responses.py        # TokenResponse and ValidationReport models
│
├── utils/
│   ├── logger.py           # Structured multi-file Loguru logging infrastructure
│   ├── helpers.py          # String sanitization & list wrapping helpers
│   └── retry.py            # Tenacity exponential backoff decorators
│
├── cli/
│   └── commands.py         # Rich CLI command handlers for all 5 ontologies
│
├── output/                 # Exported CSV, Excel, and JSON deliverables
├── logs/                   # Categorized log files (api.log, mongo.log, etc.)
├── tests/                  # Pytest test suite
│
├── .env.example            # Environment configuration template
├── .gitignore              # Git ignore configuration
├── requirements.txt        # Production dependencies
├── README.md               # Pipeline documentation
└── main.py                 # CLI entry point
```

---

## Installation

1. **Clone & Navigate to Workspace**:
   ```bash
   git clone https://github.com/arunkumar-k13/OAAS.git
   cd OAAS
   ```

2. **Set Up Virtual Environment**:
   ```bash
   python -m venv venv
   # Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # Linux/macOS:
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## CLI Usage & Commands

Run all pipeline commands using `main.py`:

### LOINC 2026 Commands
```bash
# Parse LOINC CSV or ZIP archive
python main.py fetch-loinc

# Transform to Lexicon schema with component hierarchy
python main.py transform-loinc

# Export clean CSV and Multi-Sheet Excel
python main.py export-loinc
```

### MeSH 2026 Commands
```bash
# Parse NLM MeSH XML files (desc2026.xml, qual2026.xml, supp2026.xml)
python main.py fetch-mesh

# Transform to Descriptors, Concepts, and Qualifiers
python main.py transform-mesh

# Export MeSH clean CSV and Excel workbooks
python main.py export-mesh
```

### ICD-10-CM 2026 Commands
```bash
python main.py fetch-icd10cm
python main.py transform-icd10cm
python main.py export-icd10cm
```

### ICD-11 & General Commands
```bash
python main.py fetch
python main.py transform
python main.py validate
python main.py export
python main.py stats
python main.py reset
```

---

## Deduplication & Quality Rules

To guarantee **0 Duplicate Import Errors** when loading data into Lexicon systems:

1. **Name Grouping**: Data is grouped strictly by `Name` (`molcon:Name`).
2. **Pipe-Delimited Value Merging**: Multiple values for attributes (such as IDs, Synonyms, Example Units, UCUM Units, Tree Numbers) are combined into a single string using pipe (`|`) delimiting.
3. **Empty Auto-Generated Fields**: `ID` and `hasDbXref` are kept blank (`""`) to allow target Lexicon systems to assign internal primary keys cleanly.

---

## Testing & Verification

Run the pytest suite to verify all core components:

```bash
python -m pytest tests/ -v
```
