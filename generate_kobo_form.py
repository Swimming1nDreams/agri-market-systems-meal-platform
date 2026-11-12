import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import os
import shutil

wb = openpyxl.Workbook()

header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
regular_font = Font(name="Segoe UI", size=10)

# -------------------------------------------------------------
# Sheet 1: survey
# -------------------------------------------------------------
ws_survey = wb.active
ws_survey.title = "survey"

survey_headers = [
    "type", "name", "label::English", "label::Myanmar", "hint::English",
    "required", "relevant", "constraint", "constraint_message::English"
]
ws_survey.append(survey_headers)

survey_rows = [
    ("start", "start", "", "", "", "", "", "", ""),
    ("end", "end", "", "", "", "", "", "", ""),
    ("today", "survey_date", "Date of Survey", "စစ်တမ်းကောက်ယူသည့်နေ့စွဲ", "", "yes", "", "", ""),
    ("text", "enumerator_id", "Enumerator / MEAL Officer Code", "စစ်တမ်းကောက်သူ အမှတ်အသား", "e.g. MEAL-01", "yes", "", "", ""),
    
    # Section 1: Location & Participant Info
    ("select_one township_list", "township", "Select Township", "မြို့နယ်ရွေးချယ်ပါ", "", "yes", "", "", ""),
    ("text", "village_ward", "Village Track / Ward Name", "ကျေးရွာအုပ်စု / ရပ်ကွက် အမည်", "", "yes", "", "", ""),
    ("geopoint", "gps_location", "Record GPS Coordinates", "GPS တည်နေရာ မှတ်တမ်းတင်ပါ", "Ensure accurate satellite lock", "no", "", "", ""),
    
    ("select_one participant_type", "participant_category", "Category of Participant", "ပါဝင်သူ အမျိုးအစား", "", "yes", "", "", ""),
    ("text", "name_entity", "Farmer Name or Agri-Enterprise Name", "တောင်သူအမည် သို့မဟုတ် စီးပွားရေးလုပ်ငန်းအမည်", "", "yes", "", "", ""),
    ("select_one gender_list", "gender", "Gender of Lead / Owner", "ဦးဆောင်သူ / ပိုင်ရှင်၏ ကျား/မ", "", "yes", "", "", ""),
    ("integer", "age_years", "Age of Lead / Owner (Years)", "ဦးဆောင်သူ / ပိုင်ရှင်၏ အသက် (နှစ်)", "", "yes", "", ". >= 18 and . <= 90", "Age must be between 18 and 90"),
    ("text", "contact_phone", "Contact Phone Number", "ဆက်သွယ်ရန် ဖုန်းနံပါတ်", "e.g. 0945001122", "yes", "", "regex(., '^09[0-9]{7,9}$')", "Invalid Myanmar phone number format"),

    # Section 2: Value Chain & Production
    ("select_one value_chain_list", "value_chain", "Primary Agrifood Value Chain", "အဓိက စိုက်ပျိုးထုတ်လုပ်သော သီးနှံ/ကဏ္ဍ", "", "yes", "", "", ""),
    ("decimal", "land_size_acres", "Cultivated Land Size (Acres)", "စိုက်ပျိုးမြေဧရိယာ (ဧက)", "", "yes", "", ". >= 0", "Area cannot be negative"),
    
    # Section 3: MSD Interventions & Adoption
    ("select_multiple intervention_list", "received_interventions", "Project Interventions Received", "စီမံကိန်းမှ ရရှိခဲ့သော ပံ့ပိုးမှုများ", "Select all that apply", "yes", "", "", ""),
    ("select_one yes_no", "adopted_climate_resilient", "Has the participant adopted climate-resilient practices?", "ရာသီဥတုဒဏ်ခံ စိုက်ပျိုးနည်းစနစ်များကို လက်တွေ့ကျင့်သုံးပါသလား?", "", "yes", "", "", ""),
    ("text", "climate_practices_detail", "Specify climate practices adopted", "ကျင့်သုံးသော နည်းစနစ်များကို ဖော်ပြပါ", "e.g. drip irrigation, organic composting", "yes", "${adopted_climate_resilient} = 'yes'", "", ""),

    # Section 4: Financial Access & Revenue
    ("select_one yes_no", "accessed_finance", "Did the MSME/Farmer access formal financial services or grants?", "ဘဏ္ဍာရေးဝန်ဆောင်မှု သို့မဟုတ် ထောက်ပံ့ငွေ ရရှိခဲ့ပါသလား?", "", "yes", "", "", ""),
    ("decimal", "loan_grant_amount_mmk", "Total Financial Amount Facilitated (MMK)", "ရရှိခဲ့သော ငွေပမာဏ (ကျပ်)", "", "yes", "${accessed_finance} = 'yes'", ". > 0", "Amount must be greater than zero"),
    ("decimal", "baseline_monthly_revenue", "Baseline Monthly Revenue / Income (MMK)", "ယခင် လစဉ် ပျမ်းမျှ ဝင်ငွေ (ကျပ်)", "", "yes", "", ". >= 0", "Revenue cannot be negative"),
    ("decimal", "current_monthly_revenue", "Current Monthly Revenue / Income (MMK)", "လက်ရှိ လစဉ် ပျမ်းမျှ ဝင်ငွေ (ကျပ်)", "", "yes", "", ". >= 0", "Revenue cannot be negative"),

    # Section 5: Verification & Quality Check
    ("select_one verification_list", "meal_verification", "MEAL Spot-Check / Verification Status", "MEAL ကွင်းဆင်း စစ်ဆေးအတည်ပြုမှု အခြေအနေ", "", "yes", "", "", ""),
    ("note", "thank_you_note", "Thank you for completing the FOSTER II assessment.", "စစ်တမ်းတွင် ပါဝင်ဖြေဆိုပေးသည့်အတွက် ကျေးဇူးတင်ရှိပါသည်။", "", "", "", "", ""),
]

for row in survey_rows:
    ws_survey.append(row)

# -------------------------------------------------------------
# Sheet 2: choices
# -------------------------------------------------------------
ws_choices = wb.create_sheet(title="choices")
choices_headers = ["list_name", "name", "label::English", "label::Myanmar"]
ws_choices.append(choices_headers)

choices_data = [
    # township_list
    ("township_list", "taunggyi", "Taunggyi", "တောင်ကြီး"),
    ("township_list", "kalaw", "Kalaw", "ကလော"),
    ("township_list", "hopong", "Hopong", "ဟိုပုံး"),
    ("township_list", "pindaya", "Pindaya", "ပင်းတယ"),
    ("township_list", "nyaungshwe", "Nyaungshwe", "ညောင်ရွှေ"),
    ("township_list", "ywangan", "Ywangan", "ရွာငံ"),

    # participant_type
    ("participant_type", "smallholder_farmer", "Smallholder Farmer", "အသေးစားတောင်သူ"),
    ("participant_type", "agri_msme", "Agri-MSME (Enterprise)", "စိုက်ပျိုးမွေးမြူရေး အသေးစား/အလတ်စား စီးပွားရေးလုပ်ငန်း"),

    # gender_list
    ("gender_list", "male", "Male", "ကျား"),
    ("gender_list", "female", "Female", "မ"),
    ("gender_list", "other", "Other", "အခြား"),

    # value_chain_list
    ("value_chain_list", "specialty_coffee", "Specialty Coffee", "ကော်ဖီ"),
    ("value_chain_list", "organic_tea", "Organic Tea", "လက်ဖက်"),
    ("value_chain_list", "avocado", "Avocado", "ထောပတ်"),
    ("value_chain_list", "vegetables", "High-Value Vegetables", "တန်ဖိုးမြင့် ဟင်းသီးဟင်းရွက်"),
    ("value_chain_list", "maize", "Maize", "ပြောင်းဖူး"),

    # intervention_list
    ("intervention_list", "climate_training", "Climate-Resilient Training", "ရာသီဥတုဒဏ်ခံ စိုက်ပျိုးနည်း သင်တန်း"),
    ("intervention_list", "matching_grant", "MSME Matching Grant", "မတည်ထောက်ပံ့ငွေ"),
    ("intervention_list", "finance_linkage", "Financial Access Linkage", "ဘဏ်/ချေးငွေ ချိတ်ဆက်မှု"),
    ("intervention_list", "market_linkage", "Private Sector Market Linkage", "ဈေးကွက်ချိတ်ဆက်မှု"),
    ("intervention_list", "equipment_support", "Post-Harvest Equipment", "ရိတ်သိမ်းချိန်လွန် စက်ကိရိယာ အထောက်အပံ့"),

    # yes_no
    ("yes_no", "yes", "Yes", "ဟုတ်ပါသည်"),
    ("yes_no", "no", "No", "မဟုတ်ပါ"),

    # verification_list
    ("verification_list", "verified", "Fully Verified", "အတည်ပြုပြီး"),
    ("verification_list", "spot_check_required", "Spot-Check Required", "ကွင်းဆင်းပြန်လည်စစ်ဆေးရန်လိုအပ်"),
]

for row in choices_data:
    ws_choices.append(row)

# -------------------------------------------------------------
# Sheet 3: settings
# -------------------------------------------------------------
ws_settings = wb.create_sheet(title="settings")
ws_settings.append(["form_title", "form_id", "version", "default_language"])
ws_settings.append(["FOSTER II Agrifood & MSME Monitoring Survey", "foster_ii_msme_survey", "v1.0", "English"])

# Format headers
for ws in [ws_survey, ws_choices, ws_settings]:
    for col in range(1, ws.max_column + 1):
        cell = ws.cell(row=1, column=col)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
    for r in range(2, ws.max_row + 1):
        for c in range(1, ws.max_column + 1):
            ws.cell(row=r, column=c).font = regular_font

output_dir = r"C:\Users\Lenovo\.gemini\antigravity\scratch\FOSTER_II_MEAL_System"
kobo_path = os.path.join(output_dir, "Kobo_FOSTER_II_Field_Survey_XLSForm.xlsx")
wb.save(kobo_path)

downloads_path = r"C:\Users\Lenovo\Downloads\Kobo_FOSTER_II_Field_Survey_XLSForm.xlsx"
shutil.copyfile(kobo_path, downloads_path)

print(f"Successfully generated Kobo XLSForm: {kobo_path} and copied to {downloads_path}")
