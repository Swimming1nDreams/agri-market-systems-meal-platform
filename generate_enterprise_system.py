import sqlite3
import random
import os
import shutil
from datetime import datetime, timedelta
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

print("Starting Enterprise MEAL & MIS Warehouse Generation (5,000+ Records)...")

project_dir = r"C:\Users\Lenovo\.gemini\antigravity\scratch\FOSTER_II_MEAL_System"
db_path = os.path.join(project_dir, "foster_enterprise_warehouse.db")

if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Create Relational Star Schema Tables
cursor.executescript("""
CREATE TABLE dim_locations (
    township_pcode TEXT PRIMARY KEY,
    township_name TEXT NOT NULL,
    district TEXT NOT NULL,
    state_region TEXT NOT NULL,
    latitude_min REAL,
    latitude_max REAL,
    longitude_min REAL,
    longitude_max REAL,
    target_beneficiaries INTEGER
);

CREATE TABLE dim_value_chains (
    value_chain_id TEXT PRIMARY KEY,
    value_chain_name TEXT NOT NULL,
    category TEXT NOT NULL,
    typical_cycle_months INTEGER,
    high_value_flag TEXT
);

CREATE TABLE dim_beneficiaries (
    beneficiary_id TEXT PRIMARY KEY,
    participant_name TEXT NOT NULL,
    category TEXT NOT NULL, -- 'Smallholder Farmer' or 'Agri-MSME'
    gender TEXT NOT NULL,
    age_years INTEGER NOT NULL,
    township_pcode TEXT NOT NULL,
    village_tract TEXT NOT NULL,
    phone_number TEXT,
    national_id_hash TEXT,
    registration_date DATE,
    FOREIGN KEY (township_pcode) REFERENCES dim_locations(township_pcode)
);

CREATE TABLE fact_monitoring_evaluations (
    monitoring_id TEXT PRIMARY KEY,
    beneficiary_id TEXT NOT NULL,
    value_chain_id TEXT NOT NULL,
    monitoring_round TEXT NOT NULL, -- 'Baseline', 'Midline', 'Endline'
    visit_date DATE NOT NULL,
    cultivated_acres REAL,
    baseline_monthly_revenue_mmk REAL,
    current_monthly_revenue_mmk REAL,
    revenue_growth_pct REAL,
    climate_resilient_adopted TEXT, -- 'Yes', 'No'
    climate_practice_type TEXT,
    financing_facilitated_mmk REAL,
    post_harvest_loss_pct REAL,
    enumerator_id TEXT,
    verification_status TEXT, -- 'Verified', 'Flagged_Anomaly', 'Spot_Check_Required'
    FOREIGN KEY (beneficiary_id) REFERENCES dim_beneficiaries(beneficiary_id),
    FOREIGN KEY (value_chain_id) REFERENCES dim_value_chains(value_chain_id)
);

CREATE TABLE fact_accountability_complaints (
    case_id TEXT PRIMARY KEY,
    beneficiary_id TEXT NOT NULL,
    incident_date DATE,
    channel TEXT, -- 'Hotline', 'Help Desk', 'Community Meeting'
    category TEXT, -- 'Targeting Criteria', 'Grant Distribution', 'Staff Conduct', 'Technical Training'
    status TEXT, -- 'Resolved', 'Under Investigation', 'Escalated'
    days_to_resolve INTEGER,
    FOREIGN KEY (beneficiary_id) REFERENCES dim_beneficiaries(beneficiary_id)
);
""")

# 2. Populate Dimensions
locations_data = [
    ("MMR011001", "Taunggyi", "Taunggyi", "Southern Shan", 20.70, 20.90, 96.95, 97.10, 1500),
    ("MMR011002", "Kalaw", "Taunggyi", "Southern Shan", 20.55, 20.75, 96.50, 96.65, 1200),
    ("MMR011003", "Hopong", "Taunggyi", "Southern Shan", 20.75, 20.95, 97.10, 97.30, 900),
    ("MMR011004", "Pindaya", "Danu SAZ", "Southern Shan", 20.85, 21.05, 96.60, 96.75, 800),
    ("MMR011005", "Nyaungshwe", "Taunggyi", "Southern Shan", 20.50, 20.70, 96.85, 97.00, 800),
    ("MMR011006", "Ywangan", "Danu SAZ", "Southern Shan", 21.10, 21.30, 96.35, 96.55, 600),
]
cursor.executemany("INSERT INTO dim_locations VALUES (?,?,?,?,?,?,?,?,?)", locations_data)

vc_data = [
    ("VC-COFFEE", "Specialty Coffee", "Perennial / Tree Crop", 12, "Yes"),
    ("VC-TEA", "Organic Tea", "Perennial / Shrub", 6, "Yes"),
    ("VC-AVOCADO", "Hass & Local Avocado", "Orchard Fruit", 12, "Yes"),
    ("VC-VEG", "High-Value Vegetables", "Horticulture", 3, "Yes"),
    ("VC-MAIZE", "Hybrid Maize", "Field Crop", 4, "No"),
]
cursor.executemany("INSERT INTO dim_value_chains VALUES (?,?,?,?,?)", vc_data)

# 3. Generate 5,200 Realistic Beneficiaries and 5,200 Fact Monitoring Records
first_names = ["Aung", "Zaw", "Kyaw", "Hla", "Mya", "Aye", "Thida", "Khin", "Nan", "Sai", "Bo", "Soe", "Win", "Tun", "Nang", "Min", "Ei", "Sandar", "Tin", "Myo"]
last_names = ["Win", "Lin", "Htet", "Latt", "Kham", "Naw", "Oo", "Swe", "Kyaw", "Myint", "Htun", "Naing", "San", "Lwin", "Sein", "Aung", "Nwe", "Yee", "Thein", "Than"]
business_suffixes = ["Coffee Roasters", "Tea Estate", "Orchard Farm", "Agri Logistics", "Seed Hub", "Cold Chain Services", "Hydroponics", "Fresh Supply", "Producers Coop", "Trading Enterprise"]
practices = ["Drip Irrigation", "Organic Bio-Composting", "Mulching & Soil Cover", "Shade-Grown Canopy", "Intercropping", "Solar Tunnel Drying"]

random.seed(42)

beneficiaries_list = []
monitoring_list = []
audit_flags = []

start_date = datetime(2024, 1, 15)

for i in range(1, 5201):
    ben_id = f"BEN-SHAN-{i:05d}"
    is_msme = (i % 5 == 0) # 20% MSMEs, 80% smallholder farmers
    category = "Agri-MSME" if is_msme else "Smallholder Farmer"
    
    gender = random.choices(["Female", "Male"], weights=[0.48, 0.52])[0]
    age = random.randint(20, 68)
    
    loc = random.choice(locations_data)
    pcode = loc[0]
    t_name = loc[1]
    village = f"{t_name} Ward-{random.randint(1, 8)}" if is_msme else f"Village-{random.randint(1, 25)}"
    
    if is_msme:
        p_name = f"{random.choice(first_names)} {random.choice(business_suffixes)}"
    else:
        prefix = "Daw" if gender == "Female" else "U"
        p_name = f"{prefix} {random.choice(first_names)} {random.choice(last_names)}"
        
    phone = f"09{random.randint(200000000, 999999999)}"
    nid_hash = f"SHA256-{random.randint(100000, 999999)}"
    reg_date = start_date + timedelta(days=random.randint(0, 365))
    
    beneficiaries_list.append((
        ben_id, p_name, category, gender, age, pcode, village, phone, nid_hash, reg_date.strftime("%Y-%m-%d")
    ))
    
    # Fact Monitoring Record
    mon_id = f"MON-{i:05d}"
    vc = random.choice(vc_data)[0]
    round_type = random.choices(["Baseline", "Midline", "Endline"], weights=[0.25, 0.50, 0.25])[0]
    visit_date = reg_date + timedelta(days=random.randint(30, 240))
    
    if is_msme:
        acres = round(random.uniform(5.0, 35.0), 1)
        base_rev = round(random.uniform(3500000, 15000000), -4)
        growth_rate = random.uniform(0.12, 0.45)
        curr_rev = round(base_rev * (1 + growth_rate), -4)
        finance_amount = random.choices([0, 5000000, 10000000, 15000000, 25000000], weights=[0.25, 0.25, 0.25, 0.15, 0.10])[0]
    else:
        acres = round(random.uniform(0.5, 6.0), 1)
        base_rev = round(random.uniform(450000, 1800000), -3)
        growth_rate = random.uniform(0.08, 0.35)
        curr_rev = round(base_rev * (1 + growth_rate), -3)
        finance_amount = random.choices([0, 1000000, 2000000, 3000000], weights=[0.60, 0.20, 0.15, 0.05])[0]
        
    calc_growth = round((curr_rev - base_rev) / base_rev, 4)
    adopted_climate = random.choices(["Yes", "No"], weights=[0.78, 0.22])[0]
    practice = random.choice(practices) if adopted_climate == "Yes" else "None"
    loss_pct = round(random.uniform(4.0, 18.0), 1)
    enumerator = f"MEAL-ENUM-{random.randint(1, 12):02d}"
    
    # Outlier / Anomaly Injection (for real QA pipeline)
    verification = "Verified"
    if i in [142, 580, 1204, 2390, 3105, 4210]: # Revenue anomaly
        curr_rev = base_rev * 15 # 1500% jump
        verification = "Flagged_Anomaly"
        audit_flags.append((mon_id, ben_id, "Outlier: Revenue Jump > 1,000%", f"Baseline: {base_rev}, Reported: {curr_rev}"))
    elif i in [210, 890, 1750, 3400]: # Loss pct anomaly
        loss_pct = 75.0
        verification = "Spot_Check_Required"
        audit_flags.append((mon_id, ben_id, "Critical Anomaly: Post-Harvest Loss > 70%", f"Loss: {loss_pct}%"))
        
    monitoring_list.append((
        mon_id, ben_id, vc, round_type, visit_date.strftime("%Y-%m-%d"),
        acres, base_rev, curr_rev, calc_growth, adopted_climate, practice,
        finance_amount, loss_pct, enumerator, verification
    ))

cursor.executemany("INSERT INTO dim_beneficiaries VALUES (?,?,?,?,?,?,?,?,?,?)", beneficiaries_list)
cursor.executemany("INSERT INTO fact_monitoring_evaluations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", monitoring_list)

# 4. Generate Accountability Complaints (AFM)
complaints_list = []
categories = ["Targeting Criteria", "Grant Distribution", "Staff Conduct", "Technical Training"]
channels = ["Hotline 24/7", "Help Desk at Field Office", "Community Feedback Meeting"]
statuses = ["Resolved", "Resolved", "Resolved", "Under Investigation"]

for c_idx in range(1, 185):
    case_id = f"AFM-{c_idx:04d}"
    b_id = f"BEN-SHAN-{random.randint(1, 5200):05d}"
    c_date = start_date + timedelta(days=random.randint(30, 400))
    cat = random.choice(categories)
    chan = random.choice(channels)
    st = random.choice(statuses)
    days = random.randint(3, 14) if st == "Resolved" else None
    complaints_list.append((case_id, b_id, c_date.strftime("%Y-%m-%d"), chan, cat, st, days))

cursor.executemany("INSERT INTO fact_accountability_complaints VALUES (?,?,?,?,?,?,?)", complaints_list)

conn.commit()
print("SQLite Relational Warehouse created successfully with 5,200 beneficiaries and 5,200 monitoring evaluations!")

# 5. Write Data Quality Audit Log (CSV)
audit_csv_path = os.path.join(project_dir, "FOSTER_II_Data_Quality_Audit_Log.csv")
with open(audit_csv_path, "w", encoding="utf-8") as f:
    f.write("Monitoring_ID,Beneficiary_ID,Anomaly_Type,Details,Timestamp\n")
    for flag in audit_flags:
        f.write(f"{flag[0]},{flag[1]},{flag[2]},{flag[3]},{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# 6. Build Master Excel Suite from the Warehouse
print("Building Master Production Excel Workbook from SQL Warehouse...")

wb = openpyxl.Workbook()

# Styling
header_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
header_font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
regular_font = Font(name="Segoe UI", size=9)
title_font = Font(name="Segoe UI", size=14, bold=True, color="1F497D")
sub_font = Font(name="Segoe UI", size=9, italic=True, color="595959")
bold_font = Font(name="Segoe UI", size=9, bold=True)
thin_border = Border(
    left=Side(style='thin', color='E0E0E0'),
    right=Side(style='thin', color='E0E0E0'),
    top=Side(style='thin', color='E0E0E0'),
    bottom=Side(style='thin', color='E0E0E0')
)

# Sheet 1: Master_Monitoring_5200
ws_master = wb.active
ws_master.title = "Master_Monitoring_Database"

sql_query = """
SELECT 
    f.monitoring_id,
    f.beneficiary_id,
    b.participant_name,
    b.category,
    b.gender,
    b.age_years,
    l.township_name,
    v.value_chain_name,
    f.monitoring_round,
    f.cultivated_acres,
    f.baseline_monthly_revenue_mmk,
    f.current_monthly_revenue_mmk,
    f.revenue_growth_pct,
    f.climate_resilient_adopted,
    f.climate_practice_type,
    f.financing_facilitated_mmk,
    f.post_harvest_loss_pct,
    f.verification_status
FROM fact_monitoring_evaluations f
JOIN dim_beneficiaries b ON f.beneficiary_id = b.beneficiary_id
JOIN dim_locations l ON b.township_pcode = l.township_pcode
JOIN dim_value_chains v ON f.value_chain_id = v.value_chain_id
"""
cursor.execute(sql_query)
records = cursor.fetchall()

headers_master = [
    "Monitoring_ID", "Beneficiary_ID", "Participant_Name", "Category", "Gender", "Age",
    "Township", "Value_Chain", "Round", "Acres", "Baseline_Revenue_MMK", "Current_Revenue_MMK",
    "Growth_Rate", "Climate_Adopted", "Climate_Practice", "Financing_MMK", "Loss_Pct", "Verification_Status"
]
ws_master.append(headers_master)

for r_idx, row in enumerate(records, start=2):
    ws_master.append(list(row))
    if r_idx % 500 == 0:
        print(f"Exported {r_idx} rows to Excel...")

for col in range(1, 19):
    cell = ws_master.cell(row=1, column=col)
    cell.fill = header_fill
    cell.font = header_font
    cell.alignment = Alignment(horizontal="center", vertical="center")

# Format columns
for r in range(2, len(records) + 2):
    ws_master.cell(row=r, column=11).number_format = "#,##0"
    ws_master.cell(row=r, column=12).number_format = "#,##0"
    ws_master.cell(row=r, column=13).number_format = "0.0%"
    ws_master.cell(row=r, column=16).number_format = "#,##0"
    ws_master.cell(row=r, column=17).number_format = "0.0%"

# Sheet 2: Indicator_Tracking_Table_ITT (Logframe)
ws_itt = wb.create_sheet(title="Indicator_Tracking_Table_ITT")

ws_itt["B2"] = "FOSTER II PROJECT - HEKS/EPER MYANMAR"
ws_itt["B2"].font = title_font
ws_itt["B3"] = "Enterprise-Scale Multi-Year Indicator Tracking Table (ITT) - 5,200 Participants"
ws_itt["B3"].font = sub_font

headers_itt = [
    "Indicator_Code", "Logframe_Indicator_Statement", "Baseline_2024", "Target_Total_2026",
    "Actual_Achievement", "Variance", "Percent_Achieved", "Performance_Status"
]
ws_itt.append([]) # row 4
ws_itt.append(headers_itt) # row 5

for col in range(1, 9):
    c = ws_itt.cell(row=5, column=col)
    c.fill = header_fill
    c.font = header_font
    c.alignment = Alignment(horizontal="center", vertical="center")

itt_rows = [
    ("IND-1.1", "Number of smallholder farmers adopting climate-resilient practices", 0, 3200,
     '=COUNTIFS(Master_Monitoring_Database!D:D, "Smallholder Farmer", Master_Monitoring_Database!N:N, "Yes")',
     '=E6-D6', '=E6/D6',
     '=IF(G6>=1.0, "Exceeded", IF(G6>=0.80, "On-Track", "Under-performing"))'),
     
    ("IND-1.2", "Number of Agri-MSMEs receiving catalytic matching grants/financing", 0, 600,
     '=COUNTIFS(Master_Monitoring_Database!D:D, "Agri-MSME", Master_Monitoring_Database!P:P, ">0")',
     '=E7-D7', '=E7/D7',
     '=IF(G7>=1.0, "Exceeded", IF(G7>=0.80, "On-Track", "Under-performing"))'),

    ("IND-2.1", "Total agricultural capital/financing unlocked (MMK Millions)", 0, 8500,
     '=SUM(Master_Monitoring_Database!P:P)/1000000',
     '=E8-D8', '=E8/D8',
     '=IF(G8>=1.0, "Exceeded", IF(G8>=0.80, "On-Track", "Under-performing"))'),

    ("IND-2.2", "Number of beneficiaries achieving >20% revenue growth", 0, 2500,
     '=COUNTIF(Master_Monitoring_Database!M:M, ">0.20")',
     '=E9-D9', '=E9/D9',
     '=IF(G9>=1.0, "Exceeded", IF(G9>=0.80, "On-Track", "Under-performing"))'),

    ("IND-3.1", "Number of female-led agribusinesses and female farmers actively supported", 0, 2200,
     '=COUNTIF(Master_Monitoring_Database!E:E, "Female")',
     '=E10-D10', '=E10/D10',
     '=IF(G10>=1.0, "Exceeded", IF(G10>=0.80, "On-Track", "Under-performing"))'),

    ("IND-3.2", "Number of field spot-checks and quality audits conducted", 0, 4800,
     '=COUNTIF(Master_Monitoring_Database!R:R, "Verified")',
     '=E11-D11', '=E11/D11',
     '=IF(G11>=1.0, "Exceeded", IF(G11>=0.80, "On-Track", "Under-performing"))'),
]

for idx, row in enumerate(itt_rows, start=6):
    ws_itt.append(list(row))
    ws_itt.cell(row=idx, column=1).alignment = Alignment(horizontal="center")
    ws_itt.cell(row=idx, column=3).alignment = Alignment(horizontal="center")
    ws_itt.cell(row=idx, column=4).alignment = Alignment(horizontal="center")
    ws_itt.cell(row=idx, column=5).alignment = Alignment(horizontal="center")
    ws_itt.cell(row=idx, column=6).alignment = Alignment(horizontal="center")
    ws_itt.cell(row=idx, column=7).alignment = Alignment(horizontal="center")
    ws_itt.cell(row=idx, column=7).number_format = "0.0%"
    ws_itt.cell(row=idx, column=8).alignment = Alignment(horizontal="center")
    for c in range(1, 9):
        ws_itt.cell(row=idx, column=c).border = thin_border
        ws_itt.cell(row=idx, column=c).font = regular_font

ws_itt.column_dimensions["A"].width = 16
ws_itt.column_dimensions["B"].width = 55
ws_itt.column_dimensions["C"].width = 16
ws_itt.column_dimensions["D"].width = 18
ws_itt.column_dimensions["E"].width = 20
ws_itt.column_dimensions["F"].width = 16
ws_itt.column_dimensions["G"].width = 18
ws_itt.column_dimensions["H"].width = 22

# Sheet 3: Executive_MIS_Dashboard
ws_dash = wb.create_sheet(title="Executive_MIS_Dashboard")
ws_dash["B2"] = "FOSTER II PROJECT - EXECUTIVE PORTFOLIO DASHBOARD"
ws_dash["B2"].font = title_font
ws_dash["B3"] = "Southern Shan State - 5,200 Beneficiaries & MSMEs"
ws_dash["B3"].font = sub_font

# Cards
cards = [
    ("B5", "B6", "Total Tracked Population", "=COUNTA(Master_Monitoring_Database!A2:A6000)", "#,##0"),
    ("D5", "D6", "Agri-MSMEs Supported", '=COUNTIF(Master_Monitoring_Database!D:D, "Agri-MSME")', "#,##0"),
    ("F5", "F6", "Female Inclusion Rate", '=COUNTIF(Master_Monitoring_Database!E:E, "Female")/COUNTA(Master_Monitoring_Database!A2:A6000)', "0.0%"),
    ("H5", "H6", "Total Financing Unlocked (MMK)", '=SUM(Master_Monitoring_Database!P:P)', "#,##0"),
]
card_fill = PatternFill(start_color="DCE6F1", end_color="DCE6F1", fill_type="solid")
val_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")

for top, bot, title, formula, num_fmt in cards:
    ws_dash[top] = title
    ws_dash[bot] = formula
    ws_dash[top].font = bold_font
    ws_dash[bot].font = Font(name="Segoe UI", size=18, bold=True, color="1F497D")
    ws_dash[top].fill = card_fill
    ws_dash[bot].fill = val_fill
    ws_dash[top].alignment = Alignment(horizontal="center")
    ws_dash[bot].alignment = Alignment(horizontal="center")
    ws_dash[bot].number_format = num_fmt

# Breakdown by Value Chain
ws_dash["B9"] = "Value Chain Portfolio Breakdown (5,200 Records)"
ws_dash["B9"].font = bold_font
ws_dash["B10"] = "Value Chain"
ws_dash["C10"] = "Total Participants"
ws_dash["D10"] = "Average Revenue Growth"
ws_dash["E10"] = "Financing Unlocked (MMK)"
for c in ["B10", "C10", "D10", "E10"]:
    ws_dash[c].font = header_font
    ws_dash[c].fill = header_fill
    ws_dash[c].alignment = Alignment(horizontal="center")

vcs = [
    ("Specialty Coffee", '=COUNTIF(Master_Monitoring_Database!H:H, "Specialty Coffee")', '=AVERAGEIF(Master_Monitoring_Database!H:H, "Specialty Coffee", Master_Monitoring_Database!M:M)', '=SUMIF(Master_Monitoring_Database!H:H, "Specialty Coffee", Master_Monitoring_Database!P:P)'),
    ("Organic Tea", '=COUNTIF(Master_Monitoring_Database!H:H, "Organic Tea")', '=AVERAGEIF(Master_Monitoring_Database!H:H, "Organic Tea", Master_Monitoring_Database!M:M)', '=SUMIF(Master_Monitoring_Database!H:H, "Organic Tea", Master_Monitoring_Database!P:P)'),
    ("Hass & Local Avocado", '=COUNTIF(Master_Monitoring_Database!H:H, "Hass & Local Avocado")', '=AVERAGEIF(Master_Monitoring_Database!H:H, "Hass & Local Avocado", Master_Monitoring_Database!M:M)', '=SUMIF(Master_Monitoring_Database!H:H, "Hass & Local Avocado", Master_Monitoring_Database!P:P)'),
    ("High-Value Vegetables", '=COUNTIF(Master_Monitoring_Database!H:H, "High-Value Vegetables")', '=AVERAGEIF(Master_Monitoring_Database!H:H, "High-Value Vegetables", Master_Monitoring_Database!M:M)', '=SUMIF(Master_Monitoring_Database!H:H, "High-Value Vegetables", Master_Monitoring_Database!P:P)'),
    ("Hybrid Maize", '=COUNTIF(Master_Monitoring_Database!H:H, "Hybrid Maize")', '=AVERAGEIF(Master_Monitoring_Database!H:H, "Hybrid Maize", Master_Monitoring_Database!M:M)', '=SUMIF(Master_Monitoring_Database!H:H, "Hybrid Maize", Master_Monitoring_Database!P:P)'),
]

for idx, (vc_name, count_f, avg_f, sum_f) in enumerate(vcs, start=11):
    ws_dash.cell(row=idx, column=2, value=vc_name)
    ws_dash.cell(row=idx, column=3, value=count_f)
    ws_dash.cell(row=idx, column=4, value=avg_f)
    ws_dash.cell(row=idx, column=5, value=sum_f)
    ws_dash.cell(row=idx, column=3).alignment = Alignment(horizontal="center")
    ws_dash.cell(row=idx, column=4).alignment = Alignment(horizontal="center")
    ws_dash.cell(row=idx, column=5).alignment = Alignment(horizontal="right")
    ws_dash.cell(row=idx, column=4).number_format = "0.0%"
    ws_dash.cell(row=idx, column=5).number_format = "#,##0"
    for col in range(2, 6):
        ws_dash.cell(row=idx, column=col).border = thin_border

ws_dash.column_dimensions["B"].width = 25
ws_dash.column_dimensions["C"].width = 20
ws_dash.column_dimensions["D"].width = 26
ws_dash.column_dimensions["E"].width = 28
ws_dash.column_dimensions["F"].width = 22
ws_dash.column_dimensions["H"].width = 28

# Adjust column widths for master sheet
for col in ws_master.columns:
    col_letter = get_column_letter(col[0].column)
    ws_master.column_dimensions[col_letter].width = 18
ws_master.column_dimensions["C"].width = 28
ws_master.column_dimensions["H"].width = 24
ws_master.column_dimensions["O"].width = 26

excel_export_path = os.path.join(project_dir, "FOSTER_II_Enterprise_MEAL_Warehouse_5200Records.xlsx")
wb.save(excel_export_path)

downloads_path = r"C:\Users\Lenovo\Downloads\FOSTER_II_Enterprise_MEAL_Warehouse_5200Records.xlsx"
shutil.copyfile(excel_export_path, downloads_path)

conn.close()

print(f"Enterprise Excel Saved: {excel_export_path}")
print(f"Copied to Downloads: {downloads_path}")
print("ALL ENTERPRISE ASSETS GENERATED SUCCESSFULLY!")
