"""
Generate SNOMED CT Mapped Sample with Live Browser & URI Links and Hierarchical Relations.
Generates:
1. output/SNOMED_CT_Mapped_Ontology_With_Links_Sample.xlsx (Multi-Sheet Workbook)
2. output/SNOMED_CT_Mapped_Ontology_With_Links_Sample.csv
Copied to C:\\Users\\arun.kumar\\Downloads.
"""

import csv
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUTPUT_DIR = Path(r"c:\Users\arun.kumar\Desktop\MC\OAS\output")
DOWNLOADS_DIR = Path.home() / "Downloads"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 15 highly representative concepts with bidirectional hierarchy and cross-reference links
CONCEPTS = [
    {
        "Name": "Myocardial infarction",
        "ID": "",
        "Term ID": "22298006|SNOMEDCT:22298006",
        "URI": "http://snomed.info/id/22298006",
        "Browser Link": "https://browser.ihtsdotools.org/?perspective=full&conceptId1=22298006",
        "Concept ID": "22298006",
        "Fully Specified Name": "Myocardial infarction (disorder)",
        "Preferred Term": "Myocardial infarction",
        "Semantic Tag": "disorder",
        "Definition Status": "Sufficiently defined",
        "Effective Time": "20260901",
        "Synonyms": "Heart attack|Cardiac infarction|Infarction of heart|MI - Myocardial infarction",
        "subClassOf": "Ischaemic heart disease|Necrosis of anatomical site",
        "superClassOf": "Acute myocardial infarction",
        "hasDbXref": "ICD10:I21.9|ICD11:BA41|UMLS:C0027051",
        "Clinical Attributes": "Finding site: Structure of myocardium (body structure)|Associated morphology: Infarct (morphologic abnormality)",
        "Version": "SNOMED CT International Edition 2026-09-01",
        "mcXref": "",
        "forMapping": "True",
        "PossiblePrefix": "SNOMEDCT"
    },
    {
        "Name": "Acute myocardial infarction",
        "ID": "",
        "Term ID": "57054005|SNOMEDCT:57054005",
        "URI": "http://snomed.info/id/57054005",
        "Browser Link": "https://browser.ihtsdotools.org/?perspective=full&conceptId1=57054005",
        "Concept ID": "57054005",
        "Fully Specified Name": "Acute myocardial infarction (disorder)",
        "Preferred Term": "Acute myocardial infarction",
        "Semantic Tag": "disorder",
        "Synonyms": "AMI - Acute myocardial infarction|Acute heart attack|Acute cardiac infarction",
        "subClassOf": "Myocardial infarction|Acute ischaemic heart disease",
        "superClassOf": "ST elevation myocardial infarction",
        "hasDbXref": "ICD10:I21.0|ICD11:BA41.0|UMLS:C0155626",
        "Clinical Attributes": "Finding site: Structure of myocardium (body structure)|Associated morphology: Acute infarct (morphologic abnormality)",
        "Version": "SNOMED CT International Edition 2026-09-01",
        "mcXref": "",
        "forMapping": "True",
        "PossiblePrefix": "SNOMEDCT"
    },
    {
        "Name": "Diabetes mellitus",
        "ID": "",
        "Term ID": "73211009|SNOMEDCT:73211009",
        "URI": "http://snomed.info/id/73211009",
        "Browser Link": "https://browser.ihtsdotools.org/?perspective=full&conceptId1=73211009",
        "Concept ID": "73211009",
        "Fully Specified Name": "Diabetes mellitus (disorder)",
        "Preferred Term": "Diabetes mellitus",
        "Semantic Tag": "disorder",
        "Synonyms": "Diabetes|DM - Diabetes mellitus|Diabetic disorder",
        "subClassOf": "Disorder of endocrine system|Disorder of glucose metabolism",
        "superClassOf": "Type 2 diabetes mellitus",
        "hasDbXref": "ICD10:E14.9|ICD11:5A14|UMLS:C0011849",
        "Clinical Attributes": "Finding site: Endocrine system structure (body structure)|Pathological process: Abnormal glucose metabolism",
        "Version": "SNOMED CT International Edition 2026-09-01",
        "mcXref": "",
        "forMapping": "True",
        "PossiblePrefix": "SNOMEDCT"
    },
    {
        "Name": "Type 2 diabetes mellitus",
        "ID": "",
        "Term ID": "44054006|SNOMEDCT:44054006",
        "URI": "http://snomed.info/id/44054006",
        "Browser Link": "https://browser.ihtsdotools.org/?perspective=full&conceptId1=44054006",
        "Concept ID": "44054006",
        "Fully Specified Name": "Type 2 diabetes mellitus (disorder)",
        "Preferred Term": "Type 2 diabetes mellitus",
        "Semantic Tag": "disorder",
        "Synonyms": "T2D|Type 2 diabetes|Non-insulin-dependent diabetes mellitus|NIDDM",
        "subClassOf": "Diabetes mellitus",
        "superClassOf": "",
        "hasDbXref": "ICD10:E11.9|ICD11:5A11|UMLS:C0011860",
        "Clinical Attributes": "Finding site: Endocrine system structure (body structure)|Pathological process: Insulin resistance",
        "Version": "SNOMED CT International Edition 2026-09-01",
        "mcXref": "",
        "forMapping": "True",
        "PossiblePrefix": "SNOMEDCT"
    },
    {
        "Name": "Hypertensive disorder, systemic arterial",
        "ID": "",
        "Term ID": "38341003|SNOMEDCT:38341003",
        "URI": "http://snomed.info/id/38341003",
        "Browser Link": "https://browser.ihtsdotools.org/?perspective=full&conceptId1=38341003",
        "Concept ID": "38341003",
        "Fully Specified Name": "Hypertensive disorder, systemic arterial (disorder)",
        "Preferred Term": "Hypertensive disorder, systemic arterial",
        "Semantic Tag": "disorder",
        "Synonyms": "Hypertension|High blood pressure|Arterial hypertension|Systemic hypertension",
        "subClassOf": "Disorder of cardiovascular system",
        "superClassOf": "Essential hypertension",
        "hasDbXref": "ICD10:I10|ICD11:BA00|UMLS:C0020538",
        "Clinical Attributes": "Finding site: Systemic arterial structure (body structure)",
        "Version": "SNOMED CT International Edition 2026-09-01",
        "mcXref": "",
        "forMapping": "True",
        "PossiblePrefix": "SNOMEDCT"
    },
    {
        "Name": "Appendectomy",
        "ID": "",
        "Term ID": "80146002|SNOMEDCT:80146002",
        "URI": "http://snomed.info/id/80146002",
        "Browser Link": "https://browser.ihtsdotools.org/?perspective=full&conceptId1=80146002",
        "Concept ID": "80146002",
        "Fully Specified Name": "Appendectomy (procedure)",
        "Preferred Term": "Appendectomy",
        "Semantic Tag": "procedure",
        "Synonyms": "Excision of appendix|Appendicectomy|Removal of appendix",
        "subClassOf": "Excision of abdominal organ|Procedure on appendix",
        "superClassOf": "Laparoscopic appendectomy",
        "hasDbXref": "ICD10PCS:0DTJ0ZZ|CPT:44950|UMLS:C0003611",
        "Clinical Attributes": "Method: Excision - action (qualifier value)|Procedure site - Direct: Vermiform appendix structure (body structure)",
        "Version": "SNOMED CT International Edition 2026-09-01",
        "mcXref": "",
        "forMapping": "True",
        "PossiblePrefix": "SNOMEDCT"
    },
    {
        "Name": "Asthma",
        "ID": "",
        "Term ID": "195967001|SNOMEDCT:195967001",
        "URI": "http://snomed.info/id/195967001",
        "Browser Link": "https://browser.ihtsdotools.org/?perspective=full&conceptId1=195967001",
        "Concept ID": "195967001",
        "Fully Specified Name": "Asthma (disorder)",
        "Preferred Term": "Asthma",
        "Semantic Tag": "disorder",
        "Synonyms": "Bronchial asthma|Hyperreactive airway disease",
        "subClassOf": "Pulmonary disease|Chronic obstructive airway disease",
        "superClassOf": "Allergic asthma",
        "hasDbXref": "ICD10:J45.9|ICD11:CA23|UMLS:C0004096",
        "Clinical Attributes": "Finding site: Lower respiratory tract structure (body structure)|Pathological process: Airway hyperreactivity",
        "Version": "SNOMED CT International Edition 2026-09-01",
        "mcXref": "",
        "forMapping": "True",
        "PossiblePrefix": "SNOMEDCT"
    },
    {
        "Name": "Pneumonia",
        "ID": "",
        "Term ID": "24030006|SNOMEDCT:24030006",
        "URI": "http://snomed.info/id/24030006",
        "Browser Link": "https://browser.ihtsdotools.org/?perspective=full&conceptId1=24030006",
        "Concept ID": "24030006",
        "Fully Specified Name": "Pneumonia (disorder)",
        "Preferred Term": "Pneumonia",
        "Semantic Tag": "disorder",
        "Synonyms": "Infection of lung|Pneumonitis|Pulmonary infection",
        "subClassOf": "Lower respiratory tract infection|Inflammatory disorder of lung",
        "superClassOf": "Bacterial pneumonia",
        "hasDbXref": "ICD10:J18.9|ICD11:CA40|UMLS:C0032285",
        "Clinical Attributes": "Finding site: Lung structure (body structure)|Associated morphology: Inflammation (morphologic abnormality)",
        "Version": "SNOMED CT International Edition 2026-09-01",
        "mcXref": "",
        "forMapping": "True",
        "PossiblePrefix": "SNOMEDCT"
    },
    {
        "Name": "Structure of myocardium",
        "ID": "",
        "Term ID": "70070008|SNOMEDCT:70070008",
        "URI": "http://snomed.info/id/70070008",
        "Browser Link": "https://browser.ihtsdotools.org/?perspective=full&conceptId1=70070008",
        "Concept ID": "70070008",
        "Fully Specified Name": "Structure of myocardium (body structure)",
        "Preferred Term": "Structure of myocardium",
        "Semantic Tag": "body structure",
        "Synonyms": "Myocardium|Cardiac muscle structure|Heart muscle",
        "subClassOf": "Heart structure|Muscle structure",
        "superClassOf": "",
        "hasDbXref": "FMA:9564|UMLS:C0027061",
        "Clinical Attributes": "Laterality: Not applicable",
        "Version": "SNOMED CT International Edition 2026-09-01",
        "mcXref": "",
        "forMapping": "True",
        "PossiblePrefix": "SNOMEDCT"
    },
    {
        "Name": "Coronary artery structure",
        "ID": "",
        "Term ID": "111164008|SNOMEDCT:111164008",
        "URI": "http://snomed.info/id/111164008",
        "Browser Link": "https://browser.ihtsdotools.org/?perspective=full&conceptId1=111164008",
        "Concept ID": "111164008",
        "Fully Specified Name": "Coronary artery structure (body structure)",
        "Preferred Term": "Coronary artery structure",
        "Semantic Tag": "body structure",
        "Synonyms": "Coronary artery|Arteria coronaria",
        "subClassOf": "Structure of artery",
        "superClassOf": "Left coronary artery structure",
        "hasDbXref": "FMA:3954|UMLS:C0225950",
        "Clinical Attributes": "Laterality: Bilateral",
        "Version": "SNOMED CT International Edition 2026-09-01",
        "mcXref": "",
        "forMapping": "True",
        "PossiblePrefix": "SNOMEDCT"
    },
    {
        "Name": "Aspirin",
        "ID": "",
        "Term ID": "387207008|SNOMEDCT:387207008",
        "URI": "http://snomed.info/id/387207008",
        "Browser Link": "https://browser.ihtsdotools.org/?perspective=full&conceptId1=387207008",
        "Concept ID": "387207008",
        "Fully Specified Name": "Aspirin (substance)",
        "Preferred Term": "Aspirin",
        "Semantic Tag": "substance",
        "Synonyms": "Acetylsalicylic acid|ASA - Acetylsalicylic acid|2-Acetoxybenzoic acid",
        "subClassOf": "Salicylate derivative|Non-steroidal anti-inflammatory agent",
        "superClassOf": "",
        "hasDbXref": "ChEMBL:CHEMBL25|DrugBank:DB00945|RxNorm:1191|UMLS:C0004057",
        "Clinical Attributes": "Has active ingredient: Acetylsalicylic acid",
        "Version": "SNOMED CT International Edition 2026-09-01",
        "mcXref": "",
        "forMapping": "True",
        "PossiblePrefix": "SNOMEDCT"
    },
    {
        "Name": "Subcutaneous injection",
        "ID": "",
        "Term ID": "180256009|SNOMEDCT:180256009",
        "URI": "http://snomed.info/id/180256009",
        "Browser Link": "https://browser.ihtsdotools.org/?perspective=full&conceptId1=180256009",
        "Concept ID": "180256009",
        "Fully Specified Name": "Subcutaneous injection (procedure)",
        "Preferred Term": "Subcutaneous injection",
        "Semantic Tag": "procedure",
        "Synonyms": "SC injection|Subcut injection|Subcutaneous administration",
        "subClassOf": "Injection of medicament",
        "superClassOf": "",
        "hasDbXref": "ICD10PCS:3E013GC|CPT:96372|UMLS:C0021487",
        "Clinical Attributes": "Method: Injection - action (qualifier value)|Procedure site - Direct: Subcutaneous tissue structure (body structure)",
        "Version": "SNOMED CT International Edition 2026-09-01",
        "mcXref": "",
        "forMapping": "True",
        "PossiblePrefix": "SNOMEDCT"
    },
    {
        "Name": "Cardiac finding",
        "ID": "",
        "Term ID": "302509004|SNOMEDCT:302509004",
        "URI": "http://snomed.info/id/302509004",
        "Browser Link": "https://browser.ihtsdotools.org/?perspective=full&conceptId1=302509004",
        "Concept ID": "302509004",
        "Fully Specified Name": "Cardiac finding (finding)",
        "Preferred Term": "Cardiac finding",
        "Semantic Tag": "finding",
        "Synonyms": "Heart finding|Heart sign/symptom",
        "subClassOf": "Cardiovascular finding",
        "superClassOf": "Heart murmur",
        "hasDbXref": "ICD10:R00.9|UMLS:C0018808",
        "Clinical Attributes": "Finding site: Heart structure (body structure)",
        "Version": "SNOMED CT International Edition 2026-09-01",
        "mcXref": "",
        "forMapping": "True",
        "PossiblePrefix": "SNOMEDCT"
    },
    {
        "Name": "Methicillin resistant Staphylococcus aureus",
        "ID": "",
        "Term ID": "115329001|SNOMEDCT:115329001",
        "URI": "http://snomed.info/id/115329001",
        "Browser Link": "https://browser.ihtsdotools.org/?perspective=full&conceptId1=115329001",
        "Concept ID": "115329001",
        "Fully Specified Name": "Methicillin resistant Staphylococcus aureus (organism)",
        "Preferred Term": "Methicillin resistant Staphylococcus aureus",
        "Semantic Tag": "organism",
        "Synonyms": "MRSA - Methicillin resistant Staphylococcus aureus|Methicillin-resistant S. aureus",
        "subClassOf": "Staphylococcus aureus",
        "superClassOf": "",
        "hasDbXref": "NCBI:1280|UMLS:C0600494",
        "Clinical Attributes": "Has disposition: Antimicrobial resistance",
        "Version": "SNOMED CT International Edition 2026-09-01",
        "mcXref": "",
        "forMapping": "True",
        "PossiblePrefix": "SNOMEDCT"
    },
    {
        "Name": "Infarct",
        "ID": "",
        "Term ID": "5221008|SNOMEDCT:5221008",
        "URI": "http://snomed.info/id/5221008",
        "Browser Link": "https://browser.ihtsdotools.org/?perspective=full&conceptId1=5221008",
        "Concept ID": "5221008",
        "Fully Specified Name": "Infarct (morphologic abnormality)",
        "Preferred Term": "Infarct",
        "Semantic Tag": "morphologic abnormality",
        "Synonyms": "Infarction|Infarcted tissue",
        "subClassOf": "Necrosis",
        "superClassOf": "Acute infarct",
        "hasDbXref": "UMLS:C0021308",
        "Clinical Attributes": "Pathological process: Ischaemia and necrosis",
        "Definition Status": "Primitive",
        "Effective Time": "20260901",
        "Version": "SNOMED CT International Edition 2026-09-01",
        "mcXref": "",
        "forMapping": "True",
        "PossiblePrefix": "SNOMEDCT"
    }
]

# Build Multi-Sheet Excel Workbook
wb = openpyxl.Workbook()

# Sheet 1: Mapped Clinical Concepts
ws1 = wb.active
ws1.title = "Clinical Concepts"
headers = list(CONCEPTS[0].keys())

header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
link_font = Font(name="Calibri", size=10, color="0563C1", underline="single")
border_thin = Border(
    left=Side(style='thin', color='D9D9D9'),
    right=Side(style='thin', color='D9D9D9'),
    top=Side(style='thin', color='D9D9D9'),
    bottom=Side(style='thin', color='D9D9D9')
)

ws1.append(headers)
for col_num in range(1, len(headers) + 1):
    cell = ws1.cell(row=1, column=col_num)
    cell.fill = header_fill
    cell.font = header_font
    cell.alignment = Alignment(horizontal="center", vertical="center")

row_idx = 2
for c in CONCEPTS:
    row_data = [c.get(h, "") for h in headers]
    ws1.append(row_data)
    
    for col_num in range(1, len(headers) + 1):
        ws1.cell(row=row_idx, column=col_num).border = border_thin

    row_idx += 1

# Auto-adjust column widths
for col in ws1.columns:
    max_len = max(len(str(cell.value or '')) for cell in col)
    col_letter = get_column_letter(col[0].column)
    ws1.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 45)

# Sheet 2: Hierarchical Relations
ws2 = wb.create_sheet(title="Hierarchy Relations")
h_headers = ["Source SCTID", "Source Concept Name", "Relation", "Target SCTID", "Target Concept Name", "Direct Browser Link"]
ws2.append(h_headers)
for col_num in range(1, len(h_headers) + 1):
    cell = ws2.cell(row=1, column=col_num)
    cell.fill = header_fill
    cell.font = header_font
    cell.alignment = Alignment(horizontal="center", vertical="center")

RELATIONS = [
    ("57054005", "Acute myocardial infarction", "subClassOf", "22298006", "Myocardial infarction", "https://browser.ihtsdotools.org/?perspective=full&conceptId1=57054005"),
    ("22298006", "Myocardial infarction", "superClassOf", "57054005", "Acute myocardial infarction", "https://browser.ihtsdotools.org/?perspective=full&conceptId1=22298006"),
    ("44054006", "Type 2 diabetes mellitus", "subClassOf", "73211009", "Diabetes mellitus", "https://browser.ihtsdotools.org/?perspective=full&conceptId1=44054006"),
    ("73211009", "Diabetes mellitus", "superClassOf", "44054006", "Type 2 diabetes mellitus", "https://browser.ihtsdotools.org/?perspective=full&conceptId1=73211009"),
    ("22298006", "Myocardial infarction", "subClassOf", "401303003", "Ischaemic heart disease", "https://browser.ihtsdotools.org/?perspective=full&conceptId1=401303003"),
    ("80146002", "Appendectomy", "subClassOf", "65801008", "Excision of abdominal organ", "https://browser.ihtsdotools.org/?perspective=full&conceptId1=80146002"),
    ("195967001", "Asthma", "subClassOf", "195951007", "Acute lower respiratory infection", "https://browser.ihtsdotools.org/?perspective=full&conceptId1=195967001"),
    ("24030006", "Pneumonia", "subClassOf", "128601007", "Lower respiratory tract infection", "https://browser.ihtsdotools.org/?perspective=full&conceptId1=24030006")
]

r_idx = 2
for rel in RELATIONS:
    ws2.append(list(rel))
    for col_num in range(1, len(h_headers) + 1):
        ws2.cell(row=r_idx, column=col_num).border = border_thin
    r_idx += 1

for col in ws2.columns:
    max_len = max(len(str(cell.value or '')) for cell in col)
    col_letter = get_column_letter(col[0].column)
    ws2.column_dimensions[col_letter].width = min(max(max_len + 3, 15), 45)

# Sheet 3: Cross-References & External Mappings
ws3 = wb.create_sheet(title="Cross References (DbXref)")
xr_headers = ["SCTID", "SNOMED Concept Name", "Target System", "Target Code", "Reference Link"]
ws3.append(xr_headers)
for col_num in range(1, len(xr_headers) + 1):
    cell = ws3.cell(row=1, column=col_num)
    cell.fill = header_fill
    cell.font = header_font
    cell.alignment = Alignment(horizontal="center", vertical="center")

XREFS = [
    ("22298006", "Myocardial infarction", "ICD-10", "I21.9", "https://icd.who.int/browse10/2019/en#/I21.9"),
    ("22298006", "Myocardial infarction", "ICD-11", "BA41", "https://icd.who.int/browse/2026-01/mms/en#BA41"),
    ("57054005", "Acute myocardial infarction", "ICD-10", "I21.0", "https://icd.who.int/browse10/2019/en#/I21.0"),
    ("73211009", "Diabetes mellitus", "ICD-10", "E14.9", "https://icd.who.int/browse10/2019/en#/E14.9"),
    ("44054006", "Type 2 diabetes mellitus", "ICD-10", "E11.9", "https://icd.who.int/browse10/2019/en#/E11.9"),
    ("38341003", "Hypertensive disorder, systemic arterial", "ICD-10", "I10", "https://icd.who.int/browse10/2019/en#/I10"),
    ("195967001", "Asthma", "ICD-10", "J45.9", "https://icd.who.int/browse10/2019/en#/J45.9"),
    ("24030006", "Pneumonia", "ICD-10", "J18.9", "https://icd.who.int/browse10/2019/en#/J18.9"),
    ("387207008", "Aspirin", "ChEMBL", "CHEMBL25", "https://www.ebi.ac.uk/chembl/compound_report_card/CHEMBL25/"),
    ("387207008", "Aspirin", "DrugBank", "DB00945", "https://go.drugbank.com/drugs/DB00945"),
    ("80146002", "Appendectomy", "CPT", "44950", "")
]

x_idx = 2
for xr in XREFS:
    ws3.append(list(xr))
    for col_num in range(1, len(xr_headers) + 1):
        ws3.cell(row=x_idx, column=col_num).border = border_thin
    x_idx += 1

for col in ws3.columns:
    max_len = max(len(str(cell.value or '')) for cell in col)
    col_letter = get_column_letter(col[0].column)
    ws3.column_dimensions[col_letter].width = min(max(max_len + 3, 15), 45)

# Sheet 4: Statistics Summary
ws4 = wb.create_sheet(title="Summary Statistics")
ws4.append(["Metric", "Value"])
ws4.cell(row=1, column=1).fill = header_fill
ws4.cell(row=1, column=1).font = header_font
ws4.cell(row=1, column=2).fill = header_fill
ws4.cell(row=1, column=2).font = header_font

STATS = [
    ("Release Edition", "SNOMED CT International Edition (September 2026 Release)"),
    ("Total Sample Concepts", len(CONCEPTS)),
    ("Clinical Findings / Disorders", 7),
    ("Procedures / Interventions", 2),
    ("Body Structures (Anatomy)", 2),
    ("Substances / Pharmaceutical Agents", 1),
    ("Organisms", 1),
    ("Morphologic Abnormalities", 1),
    ("Findings", 1),
    ("Total Hierarchical Relations Illustrated", len(RELATIONS)),
    ("Total Cross-References (ICD-10, ICD-11, ChEMBL, DrugBank, CPT)", len(XREFS)),
    ("All Multi-Values Delimiter", "Strict Compact Pipe ('|') without spaces")
]

for k, v in STATS:
    ws4.append([k, v])
for row in ws4.iter_rows(min_row=2, max_col=2):
    for cell in row:
        cell.border = border_thin
ws4.column_dimensions['A'].width = 35
ws4.column_dimensions['B'].width = 45

# Save Excel
excel_out = OUTPUT_DIR / "SNOMED_CT_Mapped_Ontology_With_Links_Sample.xlsx"
downloads_excel = DOWNLOADS_DIR / "SNOMED_CT_Mapped_Ontology_With_Links_Sample.xlsx"
wb.save(str(excel_out))
wb.save(str(downloads_excel))

# Save CSV version of main Sheet 1
csv_out = OUTPUT_DIR / "SNOMED_CT_Mapped_Ontology_With_Links_Sample.csv"
downloads_csv = DOWNLOADS_DIR / "SNOMED_CT_Mapped_Ontology_With_Links_Sample.csv"
with open(csv_out, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    writer.writerows(CONCEPTS)

with open(downloads_csv, "w", newline="", encoding="utf-8") as f_dl:
    with open(csv_out, "r", encoding="utf-8") as f_in:
        f_dl.write(f_in.read())

print("=" * 70)
print("SNOMED CT MAPPED SAMPLE WITH LINKS GENERATED!")
print(f"Excel File: {downloads_excel}")
print(f"CSV File:   {downloads_csv}")
print("=" * 70)
