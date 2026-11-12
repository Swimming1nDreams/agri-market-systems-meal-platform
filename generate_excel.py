import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import os
import shutil

wb = openpyxl.Workbook()

# Style helpers
header_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid") # Dark Blue
header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
accent_fill = PatternFill(start_color="DCE6F1", end_color="DCE6F1", fill_type="solid") # Light Blue
soft_green = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
soft_yellow = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
soft_red = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
bold_font = Font(name="Segoe UI", size=10, bold=True)
regular_font = Font(name="Segoe UI", size=10)
title_font = Font(name="Segoe UI", size=14, bold=True, color="1F497D")
sub_font = Font(name="Segoe UI", size=10, italic=True, color="595959")
thin_border = Border(
    left=Side(style='thin', color='D9D9D9'),
    right=Side(style='thin', color='D9D9D9'),
    top=Side(style='thin', color='D9D9D9'),
    bottom=Side(style='thin', color='D9D9D9')
)
double_bottom_border = Border(
    top=Side(style='thin', color='1F497D'),
    bottom=Side(style='double', color='1F497D')
)

# -------------------------------------------------------------
# Sheet 1: Township_Master
# -------------------------------------------------------------
ws_township = wb.active
ws_township.title = "Township_Master"

ws_township.append(["Township_Code", "Township_Name", "State_Region", "Target_Farmers", "Target_MSMEs", "Focal_Officer"])
townships = [
    ("T-SHAN-01", "Taunggyi", "Southern Shan", 350, 35, "Ko Zaw Lin"),
    ("T-SHAN-02", "Kalaw", "Southern Shan", 300, 25, "Ma Hnin Ei"),
    ("T-SHAN-03", "Hopong", "Southern Shan", 250, 20, "Ko Sai Naw"),
    ("T-SHAN-04", "Pindaya", "Southern Shan", 220, 18, "Ma May Thu"),
    ("T-SHAN-05", "Nyaungshwe", "Southern Shan", 200, 15, "Ko Kyaw Min"),
    ("T-SHAN-06", "Ywangan", "Southern Shan", 180, 12, "Ma Sandar"),
]
for row in townships:
    ws_township.append(row)

for col in range(1, 7):
    cell = ws_township.cell(row=1, column=col)
    cell.fill = header_fill
    cell.font = header_font
    cell.alignment = Alignment(horizontal="center", vertical="center")

# -------------------------------------------------------------
# Sheet 2: MSME_Farmer_Database (Operational Field Data)
# -------------------------------------------------------------
ws_data = wb.create_sheet(title="MSME_Farmer_Database")

headers_data = [
    "Record_ID", "Beneficiary_ID", "Enterprise_or_Farmer_Name", "Category", "Gender",
    "Township_Code", "Township_Name", "Value_Chain", "Intervention_Type",
    "Baseline_Revenue_MMK", "Current_Revenue_MMK", "Revenue_Growth_Rate",
    "Adopted_Climate_Practice", "Access_to_Finance_MMK", "Surveyor_Code", "Verification_Status"
]
ws_data.append(headers_data)

raw_records = [
    ("REC-001", "BEN-SHAN-001", "Shan Highland Coffee Co.", "Agri-MSME", "Female", "T-SHAN-06", "Specialty Coffee", "Matching Grant", 4500000, 6200000, "Yes", 5000000, "MEAL-01", "Verified"),
    ("REC-002", "BEN-SHAN-002", "U Than Win", "Smallholder Farmer", "Male", "T-SHAN-01", "Avocado", "Climate-Resilient Training", 650000, 850000, "Yes", 0, "MEAL-02", "Verified"),
    ("REC-003", "BEN-SHAN-003", "Pindaya Organic Tea House", "Agri-MSME", "Female", "T-SHAN-04", "Organic Tea", "Post-Harvest Equipment", 3200000, 4100000, "Yes", 3500000, "MEAL-01", "Verified"),
    ("REC-004", "BEN-SHAN-004", "Daw Nan Kham", "Smallholder Farmer", "Female", "T-SHAN-03", "Specialty Coffee", "Climate-Resilient Training", 800000, 950000, "Yes", 0, "MEAL-03", "Verified"),
    ("REC-005", "BEN-SHAN-005", "Kalaw Fresh Agri Supply", "Agri-MSME", "Male", "T-SHAN-02", "High-Value Vegetables", "Financial Access Linkage", 5800000, 7500000, "No", 8000000, "MEAL-02", "Verified"),
    ("REC-006", "BEN-SHAN-006", "U Kyaw Swar", "Smallholder Farmer", "Male", "T-SHAN-06", "Specialty Coffee", "Climate-Resilient Training", 900000, 1300000, "Yes", 0, "MEAL-01", "Verified"),
    ("REC-007", "BEN-SHAN-007", "Inle Lake Veggie Logistics", "Agri-MSME", "Male", "T-SHAN-05", "High-Value Vegetables", "Market Linkage", 4200000, 5000000, "No", 2000000, "MEAL-03", "Verified"),
    ("REC-008", "BEN-SHAN-008", "Daw Mu Mu Win", "Smallholder Farmer", "Female", "T-SHAN-04", "Organic Tea", "Climate-Resilient Training", 550000, 720000, "Yes", 0, "MEAL-04", "Verified"),
    ("REC-009", "BEN-SHAN-009", "Ywangan Blue Orchard", "Agri-MSME", "Female", "T-SHAN-06", "Avocado", "Matching Grant", 6000000, 8400000, "Yes", 6000000, "MEAL-01", "Verified"),
    ("REC-010", "BEN-SHAN-010", "Ko Sai Htun", "Smallholder Farmer", "Male", "T-SHAN-03", "Maize", "Climate-Resilient Training", 700000, 780000, "No", 0, "MEAL-02", "Spot-check Required"),
    ("REC-011", "BEN-SHAN-011", "Taunggyi Seed & Input Hub", "Agri-MSME", "Male", "T-SHAN-01", "High-Value Vegetables", "Market Linkage", 8500000, 11000000, "Yes", 10000000, "MEAL-04", "Verified"),
    ("REC-012", "BEN-SHAN-012", "Daw Aye Mya", "Smallholder Farmer", "Female", "T-SHAN-02", "Avocado", "Climate-Resilient Training", 750000, 980000, "Yes", 0, "MEAL-03", "Verified"),
    ("REC-013", "BEN-SHAN-013", "Hopong Green Community", "Agri-MSME", "Female", "T-SHAN-03", "Organic Tea", "Financial Access Linkage", 2900000, 3600000, "Yes", 3000000, "MEAL-02", "Verified"),
    ("REC-014", "BEN-SHAN-014", "U Aung Myint", "Smallholder Farmer", "Male", "T-SHAN-05", "High-Value Vegetables", "Climate-Resilient Training", 850000, 1150000, "Yes", 0, "MEAL-01", "Verified"),
    ("REC-015", "BEN-SHAN-015", "Pindaya Golden Bean Roasters", "Agri-MSME", "Male", "T-SHAN-04", "Specialty Coffee", "Post-Harvest Equipment", 5100000, 6800000, "Yes", 5000000, "MEAL-04", "Verified"),
    ("REC-016", "BEN-SHAN-016", "Daw Khin Mar", "Smallholder Farmer", "Female", "T-SHAN-01", "Maize", "Climate-Resilient Training", 600000, 700000, "No", 0, "MEAL-03", "Verified"),
    ("REC-017", "BEN-SHAN-017", "Golden Avocado Producers Coop", "Agri-MSME", "Female", "T-SHAN-02", "Avocado", "Matching Grant", 7200000, 9800000, "Yes", 7500000, "MEAL-02", "Verified"),
    ("REC-018", "BEN-SHAN-018", "U Bo Bo", "Smallholder Farmer", "Male", "T-SHAN-06", "Organic Tea", "Climate-Resilient Training", 500000, 680000, "Yes", 0, "MEAL-01", "Verified"),
    ("REC-019", "BEN-SHAN-019", "Nyaungshwe Hydroponic Farm", "Agri-MSME", "Female", "T-SHAN-05", "High-Value Vegetables", "Financial Access Linkage", 6500000, 8900000, "Yes", 7000000, "MEAL-04", "Verified"),
    ("REC-020", "BEN-SHAN-020", "Ko Myo Zaw", "Smallholder Farmer", "Male", "T-SHAN-03", "Maize", "Climate-Resilient Training", 620000, 650000, "No", 0, "MEAL-03", "Spot-check Required"),
    ("REC-021", "BEN-SHAN-021", "Southern Shan Micro Finance Group", "Agri-MSME", "Female", "T-SHAN-01", "Specialty Coffee", "Financial Access Linkage", 9000000, 12500000, "Yes", 12000000, "MEAL-01", "Verified"),
    ("REC-022", "BEN-SHAN-022", "Daw Tin Tin", "Smallholder Farmer", "Female", "T-SHAN-04", "High-Value Vegetables", "Climate-Resilient Training", 780000, 1020000, "Yes", 0, "MEAL-02", "Verified"),
    ("REC-023", "BEN-SHAN-023", "Ywangan Specialty Export Ltd.", "Agri-MSME", "Male", "T-SHAN-06", "Specialty Coffee", "Market Linkage", 12000000, 16800000, "Yes", 15000000, "MEAL-01", "Verified"),
    ("REC-024", "BEN-SHAN-024", "U Hlaing Win", "Smallholder Farmer", "Male", "T-SHAN-02", "Organic Tea", "Climate-Resilient Training", 670000, 890000, "Yes", 0, "MEAL-04", "Verified"),
    ("REC-025", "BEN-SHAN-025", "Taunggyi Cold Chain Depot", "Agri-MSME", "Female", "T-SHAN-01", "High-Value Vegetables", "Post-Harvest Equipment", 8000000, 10500000, "Yes", 8000000, "MEAL-02", "Verified"),
]

for idx, rec in enumerate(raw_records, start=2):
    row_data = [
        rec[0], # Record_ID
        rec[1], # Beneficiary_ID
        rec[2], # Enterprise_or_Farmer_Name
        rec[3], # Category
        rec[4], # Gender
        rec[5], # Township_Code
        f"=XLOOKUP(F{idx}, Township_Master!A:A, Township_Master!B:B)", # Township_Name (Formula)
        rec[6], # Value_Chain
        rec[7], # Intervention_Type
        rec[8], # Baseline_Revenue_MMK
        rec[9], # Current_Revenue_MMK
        f"=(K{idx}-J{idx})/J{idx}", # Revenue_Growth_Rate (Formula)
        rec[10], # Adopted_Climate_Practice
        rec[11], # Access_to_Finance_MMK
        rec[12], # Surveyor_Code
        rec[13], # Verification_Status
    ]
    ws_data.append(row_data)

# Format Data Sheet
for col in range(1, 17):
    cell = ws_data.cell(row=1, column=col)
    cell.fill = header_fill
    cell.font = header_font
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

for r in range(2, len(raw_records) + 2):
    ws_data.cell(row=r, column=10).number_format = "#,##0"
    ws_data.cell(row=r, column=11).number_format = "#,##0"
    ws_data.cell(row=r, column=12).number_format = "0.0%"
    ws_data.cell(row=r, column=14).number_format = "#,##0"
    for c in range(1, 17):
        cell = ws_data.cell(row=r, column=c)
        cell.font = regular_font
        cell.border = thin_border
        if c in [1, 2, 4, 5, 6, 13, 15, 16]:
            cell.alignment = Alignment(horizontal="center")

# -------------------------------------------------------------
# Sheet 3: Indicator_Tracking_Table_ITT (Logframe Reporting)
# -------------------------------------------------------------
ws_itt = wb.create_sheet(title="Indicator_Tracking_Table_ITT")

ws_itt["A1"] = "FOSTER II PROJECT - HEKS/EPER MYANMAR"
ws_itt["A1"].font = title_font
ws_itt["A2"] = "Market Systems Development (MSD) - Indicator Tracking Table (ITT)"
ws_itt["A2"].font = sub_font

headers_itt = [
    "Indicator_ID", "Logframe_Indicator_Description", "Baseline", "Target_Total",
    "Current_Actual_Achievement", "Variance", "Percent_Achieved", "Performance_Status"
]
ws_itt.append([]) # empty row 3
ws_itt.append(headers_itt) # row 4

for col in range(1, 9):
    cell = ws_itt.cell(row=4, column=col)
    cell.fill = header_fill
    cell.font = header_font
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

indicators = [
    ("IND-1.1", "Number of smallholder farmers adopting climate-resilient practices", 0, 15,
     '=COUNTIFS(MSME_Farmer_Database!D:D, "Smallholder Farmer", MSME_Farmer_Database!M:M, "Yes")',
     '=E5-D5', '=E5/D5',
     '=IF(G5>=1.0, "Exceeded", IF(G5>=0.75, "On-Track", "Under-performing"))'),
    
    ("IND-1.2", "Number of agri-MSMEs receiving financial linkages / matching grants", 0, 10,
     '=COUNTIFS(MSME_Farmer_Database!D:D, "Agri-MSME", MSME_Farmer_Database!N:N, ">0")',
     '=E6-D6', '=E6/D6',
     '=IF(G6>=1.0, "Exceeded", IF(G6>=0.75, "On-Track", "Under-performing"))'),
     
    ("IND-2.1", "Total agricultural financing facilitated / unlocked (MMK Millions)", 0, 80,
     '=SUM(MSME_Farmer_Database!N:N)/1000000',
     '=E7-D7', '=E7/D7',
     '=IF(G7>=1.0, "Exceeded", IF(G7>=0.75, "On-Track", "Under-performing"))'),

    ("IND-2.2", "Number of supported enterprises and farmers reporting >20% revenue growth", 0, 18,
     '=COUNTIF(MSME_Farmer_Database!L:L, ">0.20")',
     '=E8-D8', '=E8/D8',
     '=IF(G8>=1.0, "Exceeded", IF(G8>=0.75, "On-Track", "Under-performing"))'),

    ("IND-3.1", "Number of female-led agribusinesses / farmers actively participating", 0, 12,
     '=COUNTIF(MSME_Farmer_Database!E:E, "Female")',
     '=E9-D9', '=E9/D9',
     '=IF(G9>=1.0, "Exceeded", IF(G9>=0.75, "On-Track", "Under-performing"))'),

    ("IND-3.2", "Number of field spot-checks and quality verifications completed", 0, 25,
     '=COUNTIF(MSME_Farmer_Database!P:P, "Verified")',
     '=E10-D10', '=E10/D10',
     '=IF(G10>=1.0, "Exceeded", IF(G10>=0.75, "On-Track", "Under-performing"))'),
]

for idx, ind in enumerate(indicators, start=5):
    ws_itt.append([ind[0], ind[1], ind[2], ind[3], ind[4], ind[5], ind[6], ind[7]])
    ws_itt.cell(row=idx, column=1).alignment = Alignment(horizontal="center")
    ws_itt.cell(row=idx, column=3).alignment = Alignment(horizontal="center")
    ws_itt.cell(row=idx, column=4).alignment = Alignment(horizontal="center")
    ws_itt.cell(row=idx, column=5).alignment = Alignment(horizontal="center")
    ws_itt.cell(row=idx, column=6).alignment = Alignment(horizontal="center")
    ws_itt.cell(row=idx, column=7).alignment = Alignment(horizontal="center")
    ws_itt.cell(row=idx, column=8).alignment = Alignment(horizontal="center")
    
    ws_itt.cell(row=idx, column=7).number_format = "0.0%"
    for c in range(1, 9):
        ws_itt.cell(row=idx, column=c).border = thin_border
        ws_itt.cell(row=idx, column=c).font = regular_font

# -------------------------------------------------------------
# Sheet 4: Executive_Summary_Dashboard
# -------------------------------------------------------------
ws_dash = wb.create_sheet(title="Executive_Summary_Dashboard")

ws_dash["B2"] = "FOSTER II PROJECT - EXECUTIVE MEAL SUMMARY"
ws_dash["B2"].font = title_font
ws_dash["B3"] = "Southern Shan State Agrifood & MSME Market Systems Portfolio"
ws_dash["B3"].font = sub_font

# KPI Card 1: Total Beneficiaries Tracked
ws_dash["B5"] = "Total Participants Tracked"
ws_dash["B6"] = '=COUNTA(MSME_Farmer_Database!A2:A100)'
ws_dash["B5"].font = bold_font
ws_dash["B6"].font = Font(name="Segoe UI", size=20, bold=True, color="1F497D")
ws_dash["B5"].fill = accent_fill
ws_dash["B6"].fill = soft_green
ws_dash["B5"].alignment = Alignment(horizontal="center")
ws_dash["B6"].alignment = Alignment(horizontal="center")

# KPI Card 2: Total Agri-MSMEs
ws_dash["D5"] = "Supported Agri-MSMEs"
ws_dash["D6"] = '=COUNTIF(MSME_Farmer_Database!D:D, "Agri-MSME")'
ws_dash["D5"].font = bold_font
ws_dash["D6"].font = Font(name="Segoe UI", size=20, bold=True, color="1F497D")
ws_dash["D5"].fill = accent_fill
ws_dash["D6"].fill = soft_green
ws_dash["D5"].alignment = Alignment(horizontal="center")
ws_dash["D6"].alignment = Alignment(horizontal="center")

# KPI Card 3: Female Participation Rate
ws_dash["F5"] = "Female Inclusion Rate"
ws_dash["F6"] = '=COUNTIF(MSME_Farmer_Database!E:E, "Female")/COUNTA(MSME_Farmer_Database!A2:A100)'
ws_dash["F5"].font = bold_font
ws_dash["F6"].font = Font(name="Segoe UI", size=20, bold=True, color="1F497D")
ws_dash["F5"].fill = accent_fill
ws_dash["F6"].fill = soft_green
ws_dash["F6"].number_format = "0.0%"
ws_dash["F5"].alignment = Alignment(horizontal="center")
ws_dash["F6"].alignment = Alignment(horizontal="center")

# KPI Card 4: Total Finance Unlocked
ws_dash["H5"] = "Financing Unlocked (MMK)"
ws_dash["H6"] = '=SUM(MSME_Farmer_Database!N:N)'
ws_dash["H5"].font = bold_font
ws_dash["H6"].font = Font(name="Segoe UI", size=18, bold=True, color="1F497D")
ws_dash["H5"].fill = accent_fill
ws_dash["H6"].fill = soft_green
ws_dash["H6"].number_format = "#,##0"
ws_dash["H5"].alignment = Alignment(horizontal="center")
ws_dash["H6"].alignment = Alignment(horizontal="center")

# Value Chain Summary Table
ws_dash["B9"] = "Value Chain Portfolio Breakdown"
ws_dash["B9"].font = bold_font
ws_dash["B10"] = "Value Chain"
ws_dash["C10"] = "Total Participants"
ws_dash["D10"] = "Average Revenue Growth"
for c in ["B10", "C10", "D10"]:
    ws_dash[c].font = header_font
    ws_dash[c].fill = header_fill
    ws_dash[c].alignment = Alignment(horizontal="center")

vcs = [
    ("Specialty Coffee", '=COUNTIF(MSME_Farmer_Database!H:H, "Specialty Coffee")', '=AVERAGEIF(MSME_Farmer_Database!H:H, "Specialty Coffee", MSME_Farmer_Database!L:L)'),
    ("Organic Tea", '=COUNTIF(MSME_Farmer_Database!H:H, "Organic Tea")', '=AVERAGEIF(MSME_Farmer_Database!H:H, "Organic Tea", MSME_Farmer_Database!L:L)'),
    ("Avocado", '=COUNTIF(MSME_Farmer_Database!H:H, "Avocado")', '=AVERAGEIF(MSME_Farmer_Database!H:H, "Avocado", MSME_Farmer_Database!L:L)'),
    ("High-Value Vegetables", '=COUNTIF(MSME_Farmer_Database!H:H, "High-Value Vegetables")', '=AVERAGEIF(MSME_Farmer_Database!H:H, "High-Value Vegetables", MSME_Farmer_Database!L:L)'),
    ("Maize", '=COUNTIF(MSME_Farmer_Database!H:H, "Maize")', '=AVERAGEIF(MSME_Farmer_Database!H:H, "Maize", MSME_Farmer_Database!L:L)'),
]

for idx, (vc_name, count_f, avg_f) in enumerate(vcs, start=11):
    ws_dash.cell(row=idx, column=2, value=vc_name)
    ws_dash.cell(row=idx, column=3, value=count_f)
    ws_dash.cell(row=idx, column=4, value=avg_f)
    ws_dash.cell(row=idx, column=3).alignment = Alignment(horizontal="center")
    ws_dash.cell(row=idx, column=4).alignment = Alignment(horizontal="center")
    ws_dash.cell(row=idx, column=4).number_format = "0.0%"
    for col in range(2, 5):
        ws_dash.cell(row=idx, column=col).border = thin_border

# Auto adjust column widths for all sheets
for sheet in wb.worksheets:
    for col in sheet.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or '')
            if not str(cell.value or '').startswith('='):
                max_len = max(max_len, len(val_str))
        sheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

# Specific manual tweaks
ws_itt.column_dimensions["B"].width = 45
ws_data.column_dimensions["C"].width = 28
ws_data.column_dimensions["I"].width = 26
ws_dash.column_dimensions["B"].width = 24
ws_dash.column_dimensions["C"].width = 20
ws_dash.column_dimensions["D"].width = 26
ws_dash.column_dimensions["F"].width = 22
ws_dash.column_dimensions["H"].width = 26

output_dir = r"C:\Users\Lenovo\.gemini\antigravity\scratch\FOSTER_II_MEAL_System"
excel_path = os.path.join(output_dir, "FOSTER_II_MEAL_Agrifood_System.xlsx")
wb.save(excel_path)

# Also copy to Downloads for user instant access
downloads_path = r"C:\Users\Lenovo\Downloads\FOSTER_II_MEAL_Agrifood_System.xlsx"
shutil.copyfile(excel_path, downloads_path)

print(f"Successfully generated: {excel_path} and copied to {downloads_path}")
