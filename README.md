# OAAS ICD-11 Ontology ETL Pipeline

Production-ready, scalable, and modular Python ETL pipeline designed to extract ICD-11 terminology from the official WHO ICD-11 API, transform raw payloads into the **OAAS Ontology Schema**, validate hierarchy and metadata integrity, persist everything in **MongoDB** (`oaas` database), and export clean datasets for **OAAS Lexicon Import**.

---

## Table of Contents

- [Project Architecture & Data Flow](#project-architecture--data-flow)
- [Folder Structure](#folder-structure)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Environment Variables Configuration](#environment-variables-configuration)
- [MongoDB Setup](#mongodb-setup)
- [WHO API Authentication](#who-api-authentication)
- [CLI Usage & Commands](#cli-usage--commands)
- [OAAS Ontology Schema Specification](#oaas-ontology-schema-specification)
- [Testing & Verification](#testing--verification)
- [Troubleshooting & FAQ](#troubleshooting--faq)

---

## Project Architecture & Data Flow

The ETL pipeline operates sequentially across 6 core collections in the `oaas` MongoDB database:

```
                  ┌───────────────────────────────┐
                  │       WHO ICD-11 API          │
                  └──────────────┬────────────────┘
                                 │ OAuth2 Auth
                                 ▼
                  ┌───────────────────────────────┐
                  │    ICD11Downloader (BFS)      │
                  └──────────────┬────────────────┘
                                 │ Raw JSON
                                 ▼
                  ┌───────────────────────────────┐
                  │    MongoDB Collection:        │
                  │         icd11_raw             │
                  └──────────────┬────────────────┘
                                 │ Normalization & Mapping
                                 ▼
                  ┌───────────────────────────────┐
                  │    ICD11Mapper & Hierarchy    │
                  └──────────────┬────────────────┘
                                 │ Mapped Terms
                                 ▼
                  ┌───────────────────────────────┐
                  │    MongoDB Collections:       │
                  │       icd11_processed         │
                  │     ICD11_2026_ONTOLOGY       │
                  └──────────────┬────────────────┘
                                 │ Validation Engine
                                 ▼
                  ┌───────────────────────────────┐
                  │       OntologyValidator       │
                  └──────────────┬────────────────┘
                                 │ Multi-Format Export
                                 ▼
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  icd11_ontology  │    │  icd11_ontology  │    │   oaas_lexicon   │
│      .json       │    │       .csv       │    │   _import.json   │
└──────────────────┘    └──────────────────┘    └──────────────────┘
```

---

## Folder Structure

```
OAS/
├── config/
│   ├── settings.py         # Pydantic settings loading from .env
│   ├── mapping.yaml        # YAML mapping rules for WHO -> OAAS fields
│   └── constants.py        # Collections names, schema fields, paths
│
├── extractor/
│   ├── auth.py             # Thread-safe WHO OAuth2 token manager with caching
│   ├── icd11_client.py     # HTTP Client with 429 rate limiting & retries
│   ├── downloader.py       # BFS hierarchy downloader with resume checkpoints
│   └── endpoints.py        # WHO API endpoint URL resolution
│
├── transformer/
│   ├── mapper.py           # Configurable WHO JSON -> OAAS schema mapper
│   ├── hierarchy.py        # Bidirectional superClassOf / subClassOf generator
│   ├── validator.py        # Data integrity & anomaly detection engine
│   └── normalizer.py       # HTML unescaping, string sanitization, list parser
│
├── database/
│   ├── mongo.py            # PyMongo client manager & healthcheck provider
│   ├── repositories.py     # Repositories for raw, processed, final & log collections
│   └── indexes.py          # MongoDB unique, text, and compound indexes
│
├── exporter/
│   ├── json_export.py      # Formatted JSON exporter
│   ├── csv_export.py       # Pipe-delimited CSV exporter
│   └── oaas_export.py      # OAAS Lexicon Import JSON container exporter
│
├── models/
│   ├── icd11.py            # Raw WHO API Pydantic models
│   ├── ontology.py         # OAASOntologyTerm Pydantic schema model
│   └── responses.py        # TokenResponse and ValidationReport models
│
├── utils/
│   ├── logger.py           # Multi-file Loguru logging infrastructure
│   ├── helpers.py          # String sanitization & list wrapping helpers
│   └── retry.py            # Tenacity exponential backoff decorators
│
├── cli/
│   └── commands.py         # Rich CLI command handlers
│
├── output/                 # Exported output directory
├── logs/                   # Categorized log files (api.log, mongo.log, etc.)
├── tests/                  # Pytest test suite (27 unit tests)
│
├── .env                    # Environment configuration (ignored in vcs)
├── .env.example            # Environment configuration template
├── requirements.txt        # Production dependencies
├── README.md               # Pipeline documentation
└── main.py                 # CLI entry point
```

---

## Technology Stack

- **Language**: Python 3.11+
- **Database**: MongoDB (PyMongo 4.5+)
- **Data Validation & Schemas**: Pydantic v2 & `pydantic-settings`
- **HTTP Client**: `httpx` & `requests`
- **Resilience**: `tenacity` (retries, rate limiting, 429 handling)
- **CLI & UX**: `rich` (Tables, Panels, Status spinners, Progress bars)
- **Logging**: `loguru` (Structured multi-file logging)
- **Configuration**: `pyyaml`, `python-dotenv`
- **Testing**: `pytest`

---

## Installation

1. **Clone the Repository & Navigate to Workspace**:
   ```bash
   cd OAS
   ```

2. **Set Up Python Virtual Environment** (Recommended):
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

## Environment Variables Configuration

Copy `.env.example` to create your local `.env` file:

```bash
cp .env.example .env
```

Set the variables in `.env`:

```ini
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=oaas

# WHO ICD-11 API Credentials
WHO_CLIENT_ID=your_who_client_id_here
WHO_CLIENT_SECRET=your_who_client_secret_here
WHO_AUTH_URL=https://icdaccessmanagement.who.int/connect/token
WHO_API_BASE_URL=https://id.who.int/icd

# ICD-11 Parameters
ICD11_LINEARIZATION=mms
ICD11_RELEASE_ID=2024-01
ICD11_LANGUAGE=en

# Performance & Rate Limits
MAX_RETRIES=5
REQUEST_TIMEOUT_SECONDS=30
RATE_LIMIT_DELAY=0.2

# Logging
LOG_LEVEL=INFO
```

---

## MongoDB Setup

Ensure MongoDB is running locally on port `27017` or update `MONGO_URI` in `.env`.

The pipeline targets database **`oaas`** and manages the following 6 collections:
- `icd11_raw`: Staging collection storing un-flattened raw WHO API JSON payloads.
- `icd11_processed`: Intermediate collection storing mapped OAAS schema terms.
- `ICD11_2026_ONTOLOGY`: Master collection storing the final validated ontology.
- `mapping_logs`: Audit trail for transformation & mapping runs.
- `validation_logs`: Detailed execution reports generated by the validation engine.
- `import_logs`: Export and lexicon import activity logs.

> [!NOTE]
> The database name is set strictly to `oaas`. The pipeline never touches external or preprint databases.

---

## WHO API Authentication

To fetch data from WHO ICD-11 API:

1. Register an account on the [WHO ICD API Portal](https://icd.who.int/icdapi).
2. Create an Application to obtain your `Client ID` and `Client Secret`.
3. Fill `WHO_CLIENT_ID` and `WHO_CLIENT_SECRET` in `.env`.

The `WHOAuth` service (`extractor/auth.py`) automatically:
- Obtains Bearer access tokens via Client Credentials grant.
- Caches access tokens in memory.
- Checks expiration timestamps (with a 60-second safety buffer).
- Auto-refreshes tokens upon expiry or 401 Unauthorized responses.

---

## CLI Usage & Commands

Run all pipeline commands using `main.py`:

### 1. View Database Collection Statistics
```bash
python main.py stats
```

### 2. Fetch ICD-11 Terminology from WHO API
Recursively downloads top-level MMS chapters down through child concepts into `icd11_raw`. Supports checkpoint resume.
```bash
python main.py fetch
```

### 3. Transform Raw JSON into OAAS Schema & Hierarchy
Maps raw fields, generates bidirectional `superClassOf` and `subClassOf` links, and syncs concepts to `ICD11_2026_ONTOLOGY`.
```bash
python main.py transform
```

### 4. Validate Ontology Integrity & Metadata
Executes validation metrics (missing names, missing codes, circular links, broken references) and logs reports to `validation_logs`.
```bash
python main.py validate
```

### 5. Export Datasets for OAAS Lexicon Import
Generates JSON, CSV, and OAAS Lexicon Import JSON files inside the `output/` directory.
```bash
python main.py export
```

### 6. Reset Database Collections
Drops all pipeline collections in `oaas` database and recreates clean indexes.
```bash
python main.py reset
```

---

## OAAS Ontology Schema Specification

Every term exported or stored in `ICD11_2026_ONTOLOGY` follows the exact schema:

| Field Name | Type | Description |
| :--- | :--- | :--- |
| **Name** | `string` | Primary concept title/label |
| **ID** | `string` | Unique concept entity identifier |
| **Term ID** | `string` | Short alphanumeric code (e.g. `1A00`) |
| **URI** | `string` | Canonical WHO ICD-11 URI |
| **Synonyms** | `list[string]` | Alternative terms or synonyms |
| **Short Description** | `string` | Coding note or brief summary |
| **Long Description** | `string` | Extended textual description |
| **Condition Group** | `string` | Domain category (default: `General`) |
| **hasDbXref** | `list[string]` | External cross-references (browser URLs) |
| **Definition** | `string` | Formal WHO textual definition |
| **Type I Exclude** | `list[string]` | Type I exclusion terms |
| **Type II Exclude** | `list[string]` | Type II exclusion terms |
| **Includes** | `list[string]` | Inclusion terms / criteria |
| **Applicable To** | `list[string]` | Applicability constraints |
| **forMapping** | `boolean` | Flag indicating eligibility for mapping |
| **mcXref** | `list[string]` | Clinical cross-references |
| **Version** | `string` | Linearization release version |
| **PossiblePrefix** | `string` | OAAS ontology prefix code (`ICD11`) |
| **superClassOf** | `list[string]` | Child concept URIs / IDs |
| **subClassOf** | `list[string]` | Parent concept URIs / IDs |

---

## Testing & Verification

Run the comprehensive pytest suite covering all 10 pipeline modules:

```bash
python -m pytest tests/ -v
```

Output:
```text
tests/test_auth.py PASSED
tests/test_cli.py PASSED
tests/test_client.py PASSED
tests/test_downloader.py PASSED
tests/test_exporters.py PASSED
tests/test_hierarchy.py PASSED
tests/test_init.py PASSED
tests/test_mapper.py PASSED
tests/test_repositories.py PASSED
tests/test_utils.py PASSED
tests/test_validator.py PASSED
============================= 27 passed in 1.09s =============================
```

---

## Troubleshooting & FAQ

#### 1. `MongoDB is unreachable!`
- Verify MongoDB service is running (`mongod` or Docker container).
- Check `MONGO_URI` in `.env` (default: `mongodb://localhost:27017`).

#### 2. `WHO API Client ID or Client Secret is missing`
- Ensure `.env` exists and contains valid `WHO_CLIENT_ID` and `WHO_CLIENT_SECRET`.

#### 3. Rate Limit Exceeded (HTTP 429)
- `ICD11Client` automatically inspects `Retry-After` headers and sleeps before retrying. You can also adjust `RATE_LIMIT_DELAY` in `.env`.

#### 4. Resuming Interrupted Downloads
- The downloader automatically queries `icd11_raw` for already fetched URIs before fetching. You can interrupt (`Ctrl+C`) and re-run `python main.py fetch` anytime without duplicating requests.
