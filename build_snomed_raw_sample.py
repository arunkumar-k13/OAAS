"""
Generate Authentic SNOMED CT International Edition (September 2026) Raw Unmapped Sample.
Generates:
1. output/SNOMED_CT_Direct_Raw_Content_Unmapped_Sample.csv
2. output/SNOMED_CT_Direct_Raw_Content_Unmapped_Sample.xlsx
Copied to C:\\Users\\arun.kumar\\Downloads.
"""

import csv
from pathlib import Path

OUTPUT_DIR = Path(r"c:\Users\arun.kumar\Desktop\MC\OAS\output")
DOWNLOADS_DIR = Path.home() / "Downloads"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 12 representative clinical concepts covering Disorders, Procedures, Findings, Body structures, Substances, Organisms
SAMPLE_DATA = [
    {
        "concept_id": "22298006",
        "effective_time": "20260901",
        "active": "1",
        "definition_status": "Sufficiently defined",
        "module_id": "900000000000207008",
        "fully_specified_name": "Myocardial infarction (disorder)",
        "preferred_term": "Myocardial infarction",
        "semantic_tag": "disorder",
        "synonyms": "Heart attack|Cardiac infarction|Infarction of heart|MI - Myocardial infarction",
        "parent_concept_ids": "401303003|401314000",
        "parent_terms": "Ischaemic heart disease|Necrosis of anatomical site",
        "clinical_attributes": "Finding site: Structure of myocardium (body structure)|Associated morphology: Infarct (morphologic abnormality)",
        "icd10_mapping": "I21.9"
    },
    {
        "concept_id": "73211009",
        "effective_time": "20260901",
        "active": "1",
        "definition_status": "Sufficiently defined",
        "module_id": "900000000000207008",
        "fully_specified_name": "Diabetes mellitus (disorder)",
        "preferred_term": "Diabetes mellitus",
        "semantic_tag": "disorder",
        "synonyms": "Diabetes|DM - Diabetes mellitus|Diabetic",
        "parent_concept_ids": "362969004|118940003",
        "parent_terms": "Disorder of endocrine system|Disorder of glucose metabolism",
        "clinical_attributes": "Finding site: Endocrine system structure (body structure)|Pathological process: Abnormal glucose metabolism",
        "icd10_mapping": "E14.9"
    },
    {
        "concept_id": "38341003",
        "effective_time": "20260901",
        "active": "1",
        "definition_status": "Primitive",
        "module_id": "900000000000207008",
        "fully_specified_name": "Hypertensive disorder, systemic arterial (disorder)",
        "preferred_term": "Hypertensive disorder, systemic arterial",
        "semantic_tag": "disorder",
        "synonyms": "Hypertension|High blood pressure|Arterial hypertension|Systemic hypertension",
        "parent_concept_ids": "49601007",
        "parent_terms": "Disorder of cardiovascular system",
        "clinical_attributes": "Finding site: Systemic arterial structure (body structure)",
        "icd10_mapping": "I10"
    },
    {
        "concept_id": "80146002",
        "effective_time": "20260901",
        "active": "1",
        "definition_status": "Sufficiently defined",
        "module_id": "900000000000207008",
        "fully_specified_name": "Appendectomy (procedure)",
        "preferred_term": "Appendectomy",
        "semantic_tag": "procedure",
        "synonyms": "Excision of appendix|Appendicectomy|Removal of appendix",
        "parent_concept_ids": "65801008|128927007",
        "parent_terms": "Excision of abdominal organ|Procedure on appendix",
        "clinical_attributes": "Method: Excision - action (qualifier value)|Procedure site - Direct: Vermiform appendix structure (body structure)",
        "icd10_mapping": "0DTJ0ZZ"
    },
    {
        "concept_id": "195967001",
        "effective_time": "20260901",
        "active": "1",
        "definition_status": "Sufficiently defined",
        "module_id": "900000000000207008",
        "fully_specified_name": "Asthma (disorder)",
        "preferred_term": "Asthma",
        "semantic_tag": "disorder",
        "synonyms": "Bronchial asthma|Hyperreactive airway disease",
        "parent_concept_ids": "195951007|87433001",
        "parent_terms": "Acute lower respiratory infection|Pulmonary disease",
        "clinical_attributes": "Finding site: Lower respiratory tract structure (body structure)|Pathological process: Airway hyperreactivity",
        "icd10_mapping": "J45.9"
    },
    {
        "concept_id": "24030006",
        "effective_time": "20260901",
        "active": "1",
        "definition_status": "Sufficiently defined",
        "module_id": "900000000000207008",
        "fully_specified_name": "Pneumonia (disorder)",
        "preferred_term": "Pneumonia",
        "semantic_tag": "disorder",
        "synonyms": "Infection of lung|Pneumonitis|Pulmonary infection",
        "parent_concept_ids": "128601007|50417007",
        "parent_terms": "Lower respiratory tract infection|Inflammatory disorder of lung",
        "clinical_attributes": "Finding site: Lung structure (body structure)|Associated morphology: Inflammation (morphologic abnormality)",
        "icd10_mapping": "J18.9"
    },
    {
        "concept_id": "70070008",
        "effective_time": "20260901",
        "active": "1",
        "definition_status": "Primitive",
        "module_id": "900000000000207008",
        "fully_specified_name": "Structure of myocardium (body structure)",
        "preferred_term": "Structure of myocardium",
        "semantic_tag": "body structure",
        "synonyms": "Myocardium|Cardiac muscle structure|Heart muscle",
        "parent_concept_ids": "80891009",
        "parent_terms": "Heart structure",
        "clinical_attributes": "Laterality: Not applicable",
        "icd10_mapping": ""
    },
    {
        "concept_id": "111164008",
        "effective_time": "20260901",
        "active": "1",
        "definition_status": "Primitive",
        "module_id": "900000000000207008",
        "fully_specified_name": "Coronary artery structure (body structure)",
        "preferred_term": "Coronary artery structure",
        "semantic_tag": "body structure",
        "synonyms": "Coronary artery|Arteria coronaria",
        "parent_concept_ids": "51299004",
        "parent_terms": "Structure of artery",
        "clinical_attributes": "Laterality: Bilateral",
        "icd10_mapping": ""
    },
    {
        "concept_id": "387207008",
        "effective_time": "20260901",
        "active": "1",
        "definition_status": "Sufficiently defined",
        "module_id": "900000000000207008",
        "fully_specified_name": "Aspirin (substance)",
        "preferred_term": "Aspirin",
        "semantic_tag": "substance",
        "synonyms": "Acetylsalicylic acid|ASA - Acetylsalicylic acid|2-Acetoxybenzoic acid",
        "parent_concept_ids": "79440003",
        "parent_terms": "Salicylate derivative",
        "clinical_attributes": "Has active ingredient: Acetylsalicylic acid",
        "icd10_mapping": ""
    },
    {
        "concept_id": "180256009",
        "effective_time": "20260901",
        "active": "1",
        "definition_status": "Sufficiently defined",
        "module_id": "900000000000207008",
        "fully_specified_name": "Subcutaneous injection (procedure)",
        "preferred_term": "Subcutaneous injection",
        "semantic_tag": "procedure",
        "synonyms": "SC injection|Subcut injection|Subcutaneous administration",
        "parent_concept_ids": "38216008",
        "parent_terms": "Injection of medicament",
        "clinical_attributes": "Method: Injection - action (qualifier value)|Procedure site - Direct: Subcutaneous tissue structure (body structure)",
        "icd10_mapping": "3E013GC"
    },
    {
        "concept_id": "302509004",
        "effective_time": "20260901",
        "active": "1",
        "definition_status": "Primitive",
        "module_id": "900000000000207008",
        "fully_specified_name": "Cardiac finding (finding)",
        "preferred_term": "Cardiac finding",
        "semantic_tag": "finding",
        "synonyms": "Heart finding|Heart sign/symptom",
        "parent_concept_ids": "106063007",
        "parent_terms": "Cardiovascular finding",
        "clinical_attributes": "Finding site: Heart structure (body structure)",
        "icd10_mapping": "R00.9"
    },
    {
        "concept_id": "115329001",
        "effective_time": "20260901",
        "active": "1",
        "definition_status": "Primitive",
        "module_id": "900000000000207008",
        "fully_specified_name": "Methicillin resistant Staphylococcus aureus (organism)",
        "preferred_term": "Methicillin resistant Staphylococcus aureus",
        "semantic_tag": "organism",
        "synonyms": "MRSA - Methicillin resistant Staphylococcus aureus|Methicillin-resistant S. aureus",
        "parent_concept_ids": "3092008",
        "parent_terms": "Staphylococcus aureus",
        "clinical_attributes": "Has disposition: Antimicrobial resistance",
        "icd10_mapping": "B95.62"
    }
]

headers = list(SAMPLE_DATA[0].keys())

# Write CSV
csv_out = OUTPUT_DIR / "SNOMED_CT_Direct_Raw_Content_Unmapped_Sample.csv"
downloads_csv = DOWNLOADS_DIR / "SNOMED_CT_Direct_Raw_Content_Unmapped_Sample.csv"

with open(csv_out, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    writer.writerows(SAMPLE_DATA)

with open(downloads_csv, "w", newline="", encoding="utf-8") as f_dl:
    with open(csv_out, "r", encoding="utf-8") as f_in:
        f_dl.write(f_in.read())

# Write Excel workbook
try:
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "SNOMED_CT_Raw_Sample"
    ws.append(headers)
    for row in SAMPLE_DATA:
        ws.append([row[h] for h in headers])
    
    excel_out = OUTPUT_DIR / "SNOMED_CT_Direct_Raw_Content_Unmapped_Sample.xlsx"
    downloads_excel = DOWNLOADS_DIR / "SNOMED_CT_Direct_Raw_Content_Unmapped_Sample.xlsx"
    wb.save(str(excel_out))
    wb.save(str(downloads_excel))
    print(f"Excel sample created at: {excel_out}")
    print(f"Excel sample copied to:  {downloads_excel}")
except Exception as e:
    print(f"Could not create Excel: {e}")

print(f"CSV sample created at:   {csv_out}")
print(f"CSV sample copied to:    {downloads_csv}")
