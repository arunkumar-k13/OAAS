"""
Generate SNOMED CT Sample with Live Clickable Web Links & Official URIs.
Links include:
- SNOMED International Browser URLs (concept_id & parent_concept_ids)
- Official W3C / SNOMED Info URIs (http://snomed.info/id/...)
- WHO ICD-10 Browser URLs for mapped codes
Generates:
- output/SNOMED_CT_Sample_With_Links.xlsx (with clickable blue hyperlinks in Excel)
- output/SNOMED_CT_Sample_With_Links.csv
Copied to C:\\Users\\arun.kumar\\Downloads.
"""

import csv
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

OUTPUT_DIR = Path(r"c:\Users\arun.kumar\Desktop\MC\OAS\output")
DOWNLOADS_DIR = Path.home() / "Downloads"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_BROWSER_URL = "https://browser.ihtsdotools.org/?perspective=full&conceptId1="
BASE_URI = "http://snomed.info/id/"
BASE_ICD10_URL = "https://icd.who.int/browse10/2019/en#/"

SAMPLE_DATA = [
    {
        "concept_id": "22298006",
        "fully_specified_name": "Myocardial infarction (disorder)",
        "preferred_term": "Myocardial infarction",
        "semantic_tag": "disorder",
        "snomed_browser_url": f"{BASE_BROWSER_URL}22298006",
        "concept_uri": f"{BASE_URI}22298006",
        "synonyms": "Heart attack|Cardiac infarction|Infarction of heart|MI - Myocardial infarction",
        "parent_concept_ids": "401303003|401314000",
        "parent_terms": "Ischaemic heart disease|Necrosis of anatomical site",
        "parent_browser_urls": f"{BASE_BROWSER_URL}401303003|{BASE_BROWSER_URL}401314000",
        "clinical_attributes": "Finding site: Structure of myocardium (body structure)|Associated morphology: Infarct (morphologic abnormality)",
        "icd10_code": "I21.9",
        "icd10_browser_url": f"{BASE_ICD10_URL}I21.9",
        "effective_time": "20260901",
        "active": "1",
        "definition_status": "Sufficiently defined"
    },
    {
        "concept_id": "73211009",
        "fully_specified_name": "Diabetes mellitus (disorder)",
        "preferred_term": "Diabetes mellitus",
        "semantic_tag": "disorder",
        "snomed_browser_url": f"{BASE_BROWSER_URL}73211009",
        "concept_uri": f"{BASE_URI}73211009",
        "synonyms": "Diabetes|DM - Diabetes mellitus|Diabetic",
        "parent_concept_ids": "362969004|118940003",
        "parent_terms": "Disorder of endocrine system|Disorder of glucose metabolism",
        "parent_browser_urls": f"{BASE_BROWSER_URL}362969004|{BASE_BROWSER_URL}118940003",
        "clinical_attributes": "Finding site: Endocrine system structure (body structure)|Pathological process: Abnormal glucose metabolism",
        "icd10_code": "E14.9",
        "icd10_browser_url": f"{BASE_ICD10_URL}E14.9",
        "effective_time": "20260901",
        "active": "1",
        "definition_status": "Sufficiently defined"
    },
    {
        "concept_id": "38341003",
        "fully_specified_name": "Hypertensive disorder, systemic arterial (disorder)",
        "preferred_term": "Hypertensive disorder, systemic arterial",
        "semantic_tag": "disorder",
        "snomed_browser_url": f"{BASE_BROWSER_URL}38341003",
        "concept_uri": f"{BASE_URI}38341003",
        "synonyms": "Hypertension|High blood pressure|Arterial hypertension|Systemic hypertension",
        "parent_concept_ids": "49601007",
        "parent_terms": "Disorder of cardiovascular system",
        "parent_browser_urls": f"{BASE_BROWSER_URL}49601007",
        "clinical_attributes": "Finding site: Systemic arterial structure (body structure)",
        "icd10_code": "I10",
        "icd10_browser_url": f"{BASE_ICD10_URL}I10",
        "effective_time": "20260901",
        "active": "1",
        "definition_status": "Primitive"
    },
    {
        "concept_id": "80146002",
        "fully_specified_name": "Appendectomy (procedure)",
        "preferred_term": "Appendectomy",
        "semantic_tag": "procedure",
        "snomed_browser_url": f"{BASE_BROWSER_URL}80146002",
        "concept_uri": f"{BASE_URI}80146002",
        "synonyms": "Excision of appendix|Appendicectomy|Removal of appendix",
        "parent_concept_ids": "65801008|128927007",
        "parent_terms": "Excision of abdominal organ|Procedure on appendix",
        "parent_browser_urls": f"{BASE_BROWSER_URL}65801008|{BASE_BROWSER_URL}128927007",
        "clinical_attributes": "Method: Excision - action (qualifier value)|Procedure site - Direct: Vermiform appendix structure (body structure)",
        "icd10_code": "0DTJ0ZZ",
        "icd10_browser_url": "",
        "effective_time": "20260901",
        "active": "1",
        "definition_status": "Sufficiently defined"
    },
    {
        "concept_id": "195967001",
        "fully_specified_name": "Asthma (disorder)",
        "preferred_term": "Asthma",
        "semantic_tag": "disorder",
        "snomed_browser_url": f"{BASE_BROWSER_URL}195967001",
        "concept_uri": f"{BASE_URI}195967001",
        "synonyms": "Bronchial asthma|Hyperreactive airway disease",
        "parent_concept_ids": "195951007|87433001",
        "parent_terms": "Acute lower respiratory infection|Pulmonary disease",
        "parent_browser_urls": f"{BASE_BROWSER_URL}195951007|{BASE_BROWSER_URL}87433001",
        "clinical_attributes": "Finding site: Lower respiratory tract structure (body structure)|Pathological process: Airway hyperreactivity",
        "icd10_code": "J45.9",
        "icd10_browser_url": f"{BASE_ICD10_URL}J45.9",
        "effective_time": "20260901",
        "active": "1",
        "definition_status": "Sufficiently defined"
    },
    {
        "concept_id": "24030006",
        "fully_specified_name": "Pneumonia (disorder)",
        "preferred_term": "Pneumonia",
        "semantic_tag": "disorder",
        "snomed_browser_url": f"{BASE_BROWSER_URL}24030006",
        "concept_uri": f"{BASE_URI}24030006",
        "synonyms": "Infection of lung|Pneumonitis|Pulmonary infection",
        "parent_concept_ids": "128601007|50417007",
        "parent_terms": "Lower respiratory tract infection|Inflammatory disorder of lung",
        "parent_browser_urls": f"{BASE_BROWSER_URL}128601007|{BASE_BROWSER_URL}50417007",
        "clinical_attributes": "Finding site: Lung structure (body structure)|Associated morphology: Inflammation (morphologic abnormality)",
        "icd10_code": "J18.9",
        "icd10_browser_url": f"{BASE_ICD10_URL}J18.9",
        "effective_time": "20260901",
        "active": "1",
        "definition_status": "Sufficiently defined"
    },
    {
        "concept_id": "70070008",
        "fully_specified_name": "Structure of myocardium (body structure)",
        "preferred_term": "Structure of myocardium",
        "semantic_tag": "body structure",
        "snomed_browser_url": f"{BASE_BROWSER_URL}70070008",
        "concept_uri": f"{BASE_URI}70070008",
        "synonyms": "Myocardium|Cardiac muscle structure|Heart muscle",
        "parent_concept_ids": "80891009",
        "parent_terms": "Heart structure",
        "parent_browser_urls": f"{BASE_BROWSER_URL}80891009",
        "clinical_attributes": "Laterality: Not applicable",
        "icd10_code": "",
        "icd10_browser_url": "",
        "effective_time": "20260901",
        "active": "1",
        "definition_status": "Primitive"
    },
    {
        "concept_id": "111164008",
        "fully_specified_name": "Coronary artery structure (body structure)",
        "preferred_term": "Coronary artery structure",
        "semantic_tag": "body structure",
        "snomed_browser_url": f"{BASE_BROWSER_URL}111164008",
        "concept_uri": f"{BASE_URI}111164008",
        "synonyms": "Coronary artery|Arteria coronaria",
        "parent_concept_ids": "51299004",
        "parent_terms": "Structure of artery",
        "parent_browser_urls": f"{BASE_BROWSER_URL}51299004",
        "clinical_attributes": "Laterality: Bilateral",
        "icd10_code": "",
        "icd10_browser_url": "",
        "effective_time": "20260901",
        "active": "1",
        "definition_status": "Primitive"
    },
    {
        "concept_id": "387207008",
        "fully_specified_name": "Aspirin (substance)",
        "preferred_term": "Aspirin",
        "semantic_tag": "substance",
        "snomed_browser_url": f"{BASE_BROWSER_URL}387207008",
        "concept_uri": f"{BASE_URI}387207008",
        "synonyms": "Acetylsalicylic acid|ASA - Acetylsalicylic acid|2-Acetoxybenzoic acid",
        "parent_concept_ids": "79440003",
        "parent_terms": "Salicylate derivative",
        "parent_browser_urls": f"{BASE_BROWSER_URL}79440003",
        "clinical_attributes": "Has active ingredient: Acetylsalicylic acid",
        "icd10_code": "",
        "icd10_browser_url": "",
        "effective_time": "20260901",
        "active": "1",
        "definition_status": "Sufficiently defined"
    },
    {
        "concept_id": "180256009",
        "fully_specified_name": "Subcutaneous injection (procedure)",
        "preferred_term": "Subcutaneous injection",
        "semantic_tag": "procedure",
        "snomed_browser_url": f"{BASE_BROWSER_URL}180256009",
        "concept_uri": f"{BASE_URI}180256009",
        "synonyms": "SC injection|Subcut injection|Subcutaneous administration",
        "parent_concept_ids": "38216008",
        "parent_terms": "Injection of medicament",
        "parent_browser_urls": f"{BASE_BROWSER_URL}38216008",
        "clinical_attributes": "Method: Injection - action (qualifier value)|Procedure site - Direct: Subcutaneous tissue structure (body structure)",
        "icd10_code": "3E013GC",
        "icd10_browser_url": "",
        "effective_time": "20260901",
        "active": "1",
        "definition_status": "Sufficiently defined"
    },
    {
        "concept_id": "302509004",
        "fully_specified_name": "Cardiac finding (finding)",
        "preferred_term": "Cardiac finding",
        "semantic_tag": "finding",
        "snomed_browser_url": f"{BASE_BROWSER_URL}302509004",
        "concept_uri": f"{BASE_URI}302509004",
        "synonyms": "Heart finding|Heart sign/symptom",
        "parent_concept_ids": "106063007",
        "parent_terms": "Cardiovascular finding",
        "parent_browser_urls": f"{BASE_BROWSER_URL}106063007",
        "clinical_attributes": "Finding site: Heart structure (body structure)",
        "icd10_code": "R00.9",
        "icd10_browser_url": f"{BASE_ICD10_URL}R00.9",
        "effective_time": "20260901",
        "active": "1",
        "definition_status": "Primitive"
    },
    {
        "concept_id": "115329001",
        "fully_specified_name": "Methicillin resistant Staphylococcus aureus (organism)",
        "preferred_term": "Methicillin resistant Staphylococcus aureus",
        "semantic_tag": "organism",
        "snomed_browser_url": f"{BASE_BROWSER_URL}115329001",
        "concept_uri": f"{BASE_URI}115329001",
        "synonyms": "MRSA - Methicillin resistant Staphylococcus aureus|Methicillin-resistant S. aureus",
        "parent_concept_ids": "3092008",
        "parent_terms": "Staphylococcus aureus",
        "parent_browser_urls": f"{BASE_BROWSER_URL}3092008",
        "clinical_attributes": "Has disposition: Antimicrobial resistance",
        "icd10_code": "B95.62",
        "icd10_browser_url": "",
        "effective_time": "20260901",
        "active": "1",
        "definition_status": "Primitive"
    }
]

headers = list(SAMPLE_DATA[0].keys())

# Write CSV
csv_out = OUTPUT_DIR / "SNOMED_CT_Sample_With_Links.csv"
downloads_csv = DOWNLOADS_DIR / "SNOMED_CT_Sample_With_Links.csv"

with open(csv_out, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    writer.writerows(SAMPLE_DATA)

with open(downloads_csv, "w", newline="", encoding="utf-8") as f_dl:
    with open(csv_out, "r", encoding="utf-8") as f_in:
        f_dl.write(f_in.read())

# Write Styled Excel with Live Hyperlinks
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "SNOMED_CT_Links_Sample"

# Styling definitions
header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
link_font = Font(name="Calibri", size=10, color="0000FF", underline="single")
regular_font = Font(name="Calibri", size=10)
thin_border = Border(
    left=Side(style='thin', color='D9D9D9'),
    right=Side(style='thin', color='D9D9D9'),
    top=Side(style='thin', color='D9D9D9'),
    bottom=Side(style='thin', color='D9D9D9')
)

ws.append(headers)

# Style Header Row
for col_num in range(1, len(headers) + 1):
    cell = ws.cell(row=1, column=col_num)
    cell.fill = header_fill
    cell.font = header_font
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

# Add Data with Clickable Hyperlinks
for row_idx, row in enumerate(SAMPLE_DATA, start=2):
    for col_idx, h in enumerate(headers, start=1):
        val = row[h]
        cell = ws.cell(row=row_idx, column=col_idx)
        cell.value = val
        cell.font = regular_font
        cell.border = thin_border
        cell.alignment = Alignment(vertical="center")

        # Convert URL columns to actual clickable Excel hyperlinks
        if h in ("snomed_browser_url", "concept_uri", "icd10_browser_url") and val:
            cell.hyperlink = val
            cell.font = link_font

ws.row_dimensions[1].height = 28

# Auto-adjust column widths
for col in ws.columns:
    max_len = max(len(str(cell.value or '')) for cell in col)
    col_letter = openpyxl.utils.get_column_letter(col[0].column)
    ws.column_dimensions[col_letter].width = min(max(max_len + 3, 14), 45)

excel_out = OUTPUT_DIR / "SNOMED_CT_Sample_With_Links.xlsx"
downloads_excel = DOWNLOADS_DIR / "SNOMED_CT_Sample_With_Links.xlsx"
wb.save(str(excel_out))
wb.save(str(downloads_excel))

print(f"[SUCCESS] Excel with Clickable Links: {excel_out}")
print(f"[SUCCESS] Copied to Downloads:         {downloads_excel}")
print(f"[SUCCESS] CSV with Links:              {csv_out}")
print(f"[SUCCESS] Copied to Downloads:         {downloads_csv}")
