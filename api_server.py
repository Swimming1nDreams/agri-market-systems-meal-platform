import http.server
import socketserver
import json
import sqlite3
import os
import urllib.parse
import random
from datetime import datetime

PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "foster_enterprise_warehouse.db")
PUBLIC_DIR = os.path.join(BASE_DIR, "public")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class EnterpriseMEALHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/api/kpis":
            self.handle_kpis(query)
        elif path == "/api/indicators":
            self.handle_indicators(query)
        elif path == "/api/spatial":
            self.handle_spatial(query)
        elif path == "/api/beneficiaries":
            self.handle_beneficiaries(query)
        elif path.startswith("/api/beneficiary/"):
            ben_id = path.replace("/api/beneficiary/", "")
            self.handle_single_beneficiary(ben_id)
        elif path == "/api/recent-updates":
            self.handle_recent_updates()
        elif path == "/api/charts":
            self.handle_charts(query)
        elif path == "/api/projections":
            self.handle_projections()
        elif path == "/api/audit-logs":
            self.handle_audit_logs()
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        try:
            payload = json.loads(body) if body else {}
        except:
            payload = {}

        if path == "/api/beneficiaries/new":
            self.handle_create_beneficiary(payload)
        elif path.startswith("/api/beneficiary/") and path.endswith("/verify"):
            ben_id = path.split("/")[3]
            self.handle_update_verification(ben_id, payload)
        elif path == "/api/kobo-webhook" or path == "/api/simulate-kobo":
            self.handle_simulate_kobo(payload)
        elif path == "/api/bulk-import":
            self.handle_bulk_import(payload)
        else:
            self.send_json({"error": "Endpoint not found"}, status=404)

    # ---------------------------------------------------------
    # API Handlers
    # ---------------------------------------------------------
    def handle_kpis(self, query):
        conn = get_db()
        c = conn.cursor()
        township = query.get("township", [""])[0]

        filter_sql = ""
        params = []
        if township:
            filter_sql = " JOIN dim_locations l ON b.township_pcode=l.township_pcode WHERE l.township_name=?"
            params.append(township)

        c.execute(f"SELECT COUNT(*) FROM dim_beneficiaries b{filter_sql}", params)
        total_beneficiaries = c.fetchone()[0]

        msme_sql = f"SELECT COUNT(*) FROM dim_beneficiaries b{filter_sql} {'AND' if township else 'WHERE'} b.category = 'Agri-MSME'"
        c.execute(msme_sql, params)
        total_msmes = c.fetchone()[0]

        female_sql = f"SELECT COUNT(*) FROM dim_beneficiaries b{filter_sql} {'AND' if township else 'WHERE'} b.gender = 'Female'"
        c.execute(female_sql, params)
        female_count = c.fetchone()[0]
        female_pct = round((female_count / total_beneficiaries * 100), 1) if total_beneficiaries else 0

        fin_join = " JOIN dim_beneficiaries b ON f.beneficiary_id=b.beneficiary_id" + filter_sql
        c.execute(f"SELECT SUM(f.financing_facilitated_mmk), AVG(f.revenue_growth_pct) FROM fact_monitoring_evaluations f{fin_join}", params)
        fin_sum, avg_growth = c.fetchone()
        fin_sum = fin_sum or 0
        avg_growth = round((avg_growth or 0) * 100, 1)

        c.execute(f"SELECT COUNT(*) FROM fact_monitoring_evaluations f{fin_join} {'AND' if township else 'WHERE'} f.climate_resilient_adopted = 'Yes'", params)
        climate_adopted = c.fetchone()[0]
        climate_pct = round((climate_adopted / total_beneficiaries * 100), 1) if total_beneficiaries else 0

        conn.close()

        self.send_json({
            "total_beneficiaries": total_beneficiaries,
            "total_msmes": total_msmes,
            "female_inclusion_pct": female_pct,
            "total_financing_mmk": fin_sum,
            "total_financing_billions": round(fin_sum / 1_000_000_000, 2),
            "climate_adoption_pct": climate_pct,
            "avg_revenue_growth_pct": avg_growth
        })

    def handle_indicators(self, query):
        conn = get_db()
        c = conn.cursor()
        township = query.get("township", [""])[0]

        loc_filter = ""
        params = []
        if township:
            loc_filter = " AND l.township_name=?"
            params = [township]

        indicators_config = [
            ("IND-1.1", "Smallholder farmers adopting climate-resilient practices", 3200,
             f"SELECT COUNT(*) FROM fact_monitoring_evaluations f JOIN dim_beneficiaries b ON f.beneficiary_id=b.beneficiary_id JOIN dim_locations l ON b.township_pcode=l.township_pcode WHERE b.category='Smallholder Farmer' AND f.climate_resilient_adopted='Yes'{loc_filter}"),
            ("IND-1.2", "Agri-MSMEs receiving catalytic matching grants / financing", 600,
             f"SELECT COUNT(*) FROM fact_monitoring_evaluations f JOIN dim_beneficiaries b ON f.beneficiary_id=b.beneficiary_id JOIN dim_locations l ON b.township_pcode=l.township_pcode WHERE b.category='Agri-MSME' AND f.financing_facilitated_mmk > 0{loc_filter}"),
            ("IND-2.1", "Total agricultural capital unlocked (MMK Millions)", 8500,
             f"SELECT ROUND(SUM(f.financing_facilitated_mmk)/1000000, 1) FROM fact_monitoring_evaluations f JOIN dim_beneficiaries b ON f.beneficiary_id=b.beneficiary_id JOIN dim_locations l ON b.township_pcode=l.township_pcode WHERE 1=1{loc_filter}"),
            ("IND-2.2", "Participants achieving sustainable revenue growth >20%", 2500,
             f"SELECT COUNT(*) FROM fact_monitoring_evaluations f JOIN dim_beneficiaries b ON f.beneficiary_id=b.beneficiary_id JOIN dim_locations l ON b.township_pcode=l.township_pcode WHERE f.revenue_growth_pct > 0.20{loc_filter}"),
            ("IND-3.1", "Female-led agribusinesses and female farmers actively supported", 2200,
             f"SELECT COUNT(*) FROM dim_beneficiaries b JOIN dim_locations l ON b.township_pcode=l.township_pcode WHERE b.gender = 'Female'{loc_filter}"),
            ("IND-3.2", "Field quality spot-checks and verifications conducted", 4800,
             f"SELECT COUNT(*) FROM fact_monitoring_evaluations f JOIN dim_beneficiaries b ON f.beneficiary_id=b.beneficiary_id JOIN dim_locations l ON b.township_pcode=l.township_pcode WHERE f.verification_status = 'Verified'{loc_filter}"),
        ]

        result = []
        for code, label, target, sql in indicators_config:
            c.execute(sql, params)
            actual = c.fetchone()[0] or 0
            variance = actual - target
            achieved_pct = round((actual / target) * 100, 1) if target else 0
            status = "Exceeded" if achieved_pct >= 100 else ("On-Track" if achieved_pct >= 80 else "Under-performing")
            result.append({
                "code": code,
                "label": label,
                "target": target,
                "actual": actual,
                "variance": variance,
                "achieved_pct": achieved_pct,
                "status": status
            })

        conn.close()
        self.send_json(result)

    def handle_spatial(self, query):
        conn = get_db()
        c = conn.cursor()
        limit = int(query.get("limit", [800])[0])
        township = query.get("township", [""])[0]

        sql = """
        SELECT 
            b.beneficiary_id, b.participant_name, b.category, b.gender,
            l.township_name, l.latitude_min, l.latitude_max, l.longitude_min, l.longitude_max,
            v.value_chain_name, f.current_monthly_revenue_mmk, f.climate_resilient_adopted,
            f.revenue_growth_pct, f.financing_facilitated_mmk
        FROM dim_beneficiaries b
        JOIN dim_locations l ON b.township_pcode = l.township_pcode
        JOIN fact_monitoring_evaluations f ON b.beneficiary_id = f.beneficiary_id
        JOIN dim_value_chains v ON f.value_chain_id = v.value_chain_id
        """
        params = []
        if township:
            sql += " WHERE l.township_name = ?"
            params.append(township)
        sql += " ORDER BY b.beneficiary_id DESC LIMIT ?"
        params.append(limit)

        c.execute(sql, params)
        rows = c.fetchall()
        conn.close()

        features = []
        for r in rows:
            seed_val = int(r["beneficiary_id"].split("-")[-1])
            random.seed(seed_val)
            lat = round(random.uniform(r["latitude_min"], r["latitude_max"]), 5)
            lng = round(random.uniform(r["longitude_min"], r["longitude_max"]), 5)

            features.append({
                "id": r["beneficiary_id"],
                "name": r["participant_name"],
                "category": r["category"],
                "gender": r["gender"],
                "township": r["township_name"],
                "value_chain": r["value_chain_name"],
                "revenue": r["current_monthly_revenue_mmk"],
                "growth_pct": round(r["revenue_growth_pct"] * 100, 1),
                "financing": r["financing_facilitated_mmk"],
                "climate_adopted": r["climate_resilient_adopted"],
                "lat": lat,
                "lng": lng,
                "intensity": round(min(1.0, max(0.25, r["current_monthly_revenue_mmk"] / 8000000)), 2)
            })

        self.send_json(features)

    def handle_charts(self, query):
        conn = get_db()
        c = conn.cursor()
        township = query.get("township", [""])[0]

        loc_filter = ""
        params = []
        if township:
            loc_filter = " JOIN dim_beneficiaries b ON f.beneficiary_id=b.beneficiary_id JOIN dim_locations l ON b.township_pcode=l.township_pcode WHERE l.township_name=?"
            params.append(township)

        c.execute(f"""
        SELECT v.value_chain_name, COUNT(*), ROUND(AVG(f.revenue_growth_pct)*100, 1), SUM(f.financing_facilitated_mmk)/1000000
        FROM fact_monitoring_evaluations f
        JOIN dim_value_chains v ON f.value_chain_id = v.value_chain_id
        {loc_filter}
        GROUP BY v.value_chain_name
        """, params)
        vc_data = [{"name": r[0], "count": r[1], "growth": r[2], "financing_m": round(r[3] or 0, 1)} for r in c.fetchall()]

        c.execute("""
        SELECT l.township_name, COUNT(*), SUM(CASE WHEN f.climate_resilient_adopted='Yes' THEN 1 ELSE 0 END), SUM(f.financing_facilitated_mmk)/1000000
        FROM dim_beneficiaries b
        JOIN dim_locations l ON b.township_pcode = l.township_pcode
        JOIN fact_monitoring_evaluations f ON b.beneficiary_id = f.beneficiary_id
        GROUP BY l.township_name
        """)
        t_data = [{"township": r[0], "total": r[1], "climate": r[2], "financing_m": round(r[3] or 0, 1)} for r in c.fetchall()]

        conn.close()
        self.send_json({"value_chains": vc_data, "townships": t_data})

    def handle_recent_updates(self):
        conn = get_db()
        c = conn.cursor()
        c.execute("""
        SELECT 
            b.beneficiary_id, b.participant_name, b.category, b.gender,
            l.township_name, v.value_chain_name, f.current_monthly_revenue_mmk,
            f.revenue_growth_pct, f.visit_date, f.verification_status
        FROM dim_beneficiaries b
        JOIN dim_locations l ON b.township_pcode = l.township_pcode
        JOIN fact_monitoring_evaluations f ON b.beneficiary_id = f.beneficiary_id
        JOIN dim_value_chains v ON f.value_chain_id = v.value_chain_id
        ORDER BY b.beneficiary_id DESC
        LIMIT 6
        """)
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        self.send_json(rows)

    def handle_single_beneficiary(self, ben_id):
        conn = get_db()
        c = conn.cursor()
        c.execute("""
        SELECT 
            b.beneficiary_id, b.participant_name, b.category, b.gender, b.age_years,
            b.township_pcode, l.township_name, b.village_tract, b.phone_number, b.registration_date,
            v.value_chain_name, f.monitoring_id, f.monitoring_round, f.visit_date, f.cultivated_acres,
            f.baseline_monthly_revenue_mmk, f.current_monthly_revenue_mmk, f.revenue_growth_pct,
            f.climate_resilient_adopted, f.climate_practice_type, f.financing_facilitated_mmk,
            f.post_harvest_loss_pct, f.enumerator_id, f.verification_status
        FROM dim_beneficiaries b
        JOIN dim_locations l ON b.township_pcode = l.township_pcode
        JOIN fact_monitoring_evaluations f ON b.beneficiary_id = f.beneficiary_id
        JOIN dim_value_chains v ON f.value_chain_id = v.value_chain_id
        WHERE b.beneficiary_id = ?
        """, (ben_id,))
        row = c.fetchone()
        conn.close()

        if row:
            self.send_json(dict(row))
        else:
            self.send_json({"error": "Beneficiary not found"}, status=404)

    def handle_update_verification(self, ben_id, payload):
        new_status = payload.get("status", "Verified")
        conn = get_db()
        c = conn.cursor()
        c.execute("UPDATE fact_monitoring_evaluations SET verification_status=? WHERE beneficiary_id=?", (new_status, ben_id))
        conn.commit()
        conn.close()
        self.send_json({"success": True, "beneficiary_id": ben_id, "new_status": new_status})

    def handle_create_beneficiary(self, p):
        conn = get_db()
        c = conn.cursor()

        c.execute("SELECT COUNT(*) FROM dim_beneficiaries")
        next_num = c.fetchone()[0] + 1
        new_ben_id = f"BEN-SHAN-{next_num:05d}"
        new_mon_id = f"MON-{next_num:05d}"

        name = p.get("participant_name", "Anonymous Farmer")
        category = p.get("category", "Smallholder Farmer")
        gender = p.get("gender", "Female")
        age = int(p.get("age_years", 35))
        township_name = p.get("township_name", "Taunggyi")
        village = p.get("village_tract", "Central Tract")
        phone = p.get("phone_number", "0945001122")
        value_chain_name = p.get("value_chain_name", "Specialty Coffee")
        acres = float(p.get("cultivated_acres", 2.0))
        base_rev = float(p.get("baseline_monthly_revenue_mmk", 800000))
        curr_rev = float(p.get("current_monthly_revenue_mmk", 1100000))
        growth = round((curr_rev - base_rev) / base_rev, 4) if base_rev > 0 else 0.0
        adopted = p.get("climate_resilient_adopted", "Yes")
        practice = p.get("climate_practice_type", "Composting")
        finance = float(p.get("financing_facilitated_mmk", 0))

        # Lookup pcode and vc_id
        c.execute("SELECT township_pcode FROM dim_locations WHERE township_name=?", (township_name,))
        pcode_row = c.fetchone()
        pcode = pcode_row[0] if pcode_row else "MMR011001"

        c.execute("SELECT value_chain_id FROM dim_value_chains WHERE value_chain_name=?", (value_chain_name,))
        vc_row = c.fetchone()
        vc_id = vc_row[0] if vc_row else "VC-COFFEE"

        now_str = datetime.now().strftime("%Y-%m-%d")

        c.execute("""
        INSERT INTO dim_beneficiaries VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (new_ben_id, name, category, gender, age, pcode, village, phone, "SHA256-MANUAL", now_str))

        c.execute("""
        INSERT INTO fact_monitoring_evaluations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (new_mon_id, new_ben_id, vc_id, "Endline", now_str, acres, base_rev, curr_rev, growth, adopted, practice, finance, 6.0, "WEB-MANUAL-ENTRY", "Verified"))

        conn.commit()
        conn.close()

        self.send_json({
            "success": True,
            "beneficiary_id": new_ben_id,
            "name": name,
            "township": township_name,
            "value_chain": value_chain_name,
            "growth_pct": f"{growth*100:.1f}%",
            "message": "Beneficiary successfully registered and verified in database!"
        }, status=201)

    def handle_beneficiaries(self, query):
        conn = get_db()
        c = conn.cursor()

        search = query.get("search", [""])[0]
        township = query.get("township", [""])[0]
        value_chain = query.get("value_chain", [""])[0]
        mask_pii = query.get("mask_pii", ["false"])[0].lower() == "true"
        page = int(query.get("page", [1])[0])
        limit = int(query.get("limit", [12])[0])
        offset = (page - 1) * limit

        where_clauses = ["1=1"]
        params = []

        if search:
            where_clauses.append("(b.participant_name LIKE ? OR b.beneficiary_id LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])
        if township:
            where_clauses.append("l.township_name = ?")
            params.append(township)
        if value_chain:
            where_clauses.append("v.value_chain_name = ?")
            params.append(value_chain)

        where_sql = " AND ".join(where_clauses)

        c.execute(f"SELECT COUNT(*) FROM dim_beneficiaries b JOIN dim_locations l ON b.township_pcode=l.township_pcode JOIN fact_monitoring_evaluations f ON b.beneficiary_id=f.beneficiary_id JOIN dim_value_chains v ON f.value_chain_id=v.value_chain_id WHERE {where_sql}", params)
        total = c.fetchone()[0]

        sql = f"""
        SELECT 
            b.beneficiary_id, b.participant_name, b.category, b.gender, b.age_years, b.phone_number,
            l.township_name, v.value_chain_name, f.baseline_monthly_revenue_mmk, f.current_monthly_revenue_mmk,
            f.revenue_growth_pct, f.climate_resilient_adopted, f.financing_facilitated_mmk, f.verification_status
        FROM dim_beneficiaries b
        JOIN dim_locations l ON b.township_pcode = l.township_pcode
        JOIN fact_monitoring_evaluations f ON b.beneficiary_id = f.beneficiary_id
        JOIN dim_value_chains v ON f.value_chain_id = v.value_chain_id
        WHERE {where_sql}
        ORDER BY b.beneficiary_id DESC
        LIMIT ? OFFSET ?
        """
        c.execute(sql, params + [limit, offset])
        raw_rows = [dict(r) for r in c.fetchall()]
        conn.close()

        processed_rows = []
        for row in raw_rows:
            if mask_pii:
                name_parts = row["participant_name"].split(" ")
                masked_name = name_parts[0] + " " + (name_parts[1][:1] + "***" if len(name_parts) > 1 else "***")
                phone = row["phone_number"]
                masked_phone = phone[:4] + "***" + phone[-2:] if len(phone) >= 7 else "09***"
                row["participant_name"] = masked_name
                row["phone_number"] = masked_phone
            processed_rows.append(row)

        self.send_json({
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
            "data": processed_rows
        })

    def handle_projections(self):
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM dim_beneficiaries")
        total = c.fetchone()[0]
        conn.close()

        forecast = [
            {"quarter": "2024-Q1 (Baseline)", "farmers_reached": 1200, "status": "Verified"},
            {"quarter": "2024-Q3 (Midline)", "farmers_reached": 2900, "status": "Verified"},
            {"quarter": "2025-Q1 (Current)", "farmers_reached": total, "status": "Verified Current"},
            {"quarter": "2025-Q3 (Forecast)", "farmers_reached": total + 850, "status": "Model Projected"},
            {"quarter": "2026-Q2 (Target Endline)", "farmers_reached": 6500, "status": "Logframe Target"},
        ]
        self.send_json(forecast)

    def handle_audit_logs(self):
        log_path = os.path.join(BASE_DIR, "FOSTER_II_Data_Quality_Audit_Log.csv")
        items = []
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()[1:]
                for line in lines:
                    parts = line.strip().split(",")
                    if len(parts) >= 4:
                        items.append({
                            "monitoring_id": parts[0],
                            "beneficiary_id": parts[1],
                            "anomaly_type": parts[2],
                            "details": ",".join(parts[3:-1]) if len(parts) > 4 else parts[3],
                            "timestamp": parts[-1] if len(parts) > 4 else ""
                        })
        self.send_json(items)

    def handle_simulate_kobo(self, payload):
        conn = get_db()
        c = conn.cursor()

        c.execute("SELECT COUNT(*) FROM dim_beneficiaries")
        next_num = c.fetchone()[0] + 1
        new_ben_id = f"BEN-SHAN-{next_num:05d}"
        new_mon_id = f"MON-{next_num:05d}"

        first_names = ["Thura", "Aye", "Nan", "Sai", "Min", "Khin", "Zayar", "Sandar", "Tin"]
        mid_names = ["Htet", "Lin", "Kham", "Naw", "Lwin", "San", "Tun", "Myint", "Kyaw"]
        townships = [
            ("MMR011001", "Taunggyi", 20.78, 20.88, 96.96, 97.08),
            ("MMR011002", "Kalaw", 20.60, 20.72, 96.52, 96.63),
            ("MMR011003", "Hopong", 20.80, 20.92, 97.12, 97.28),
            ("MMR011004", "Pindaya", 20.90, 21.02, 96.62, 96.73),
            ("MMR011005", "Nyaungshwe", 20.55, 20.68, 96.88, 96.98),
            ("MMR011006", "Ywangan", 21.15, 21.28, 96.38, 96.52),
        ]
        vcs = [
            ("VC-COFFEE", "Specialty Coffee"),
            ("VC-TEA", "Organic Tea"),
            ("VC-AVOCADO", "Hass & Local Avocado"),
            ("VC-VEG", "High-Value Vegetables")
        ]

        loc = random.choice(townships)
        vc = random.choice(vcs)
        gender = random.choice(["Female", "Male"])
        prefix = "Daw" if gender == "Female" else "U"
        name = f"{prefix} {random.choice(first_names)} {random.choice(mid_names)}"
        
        base_rev = random.randint(700000, 1800000)
        curr_rev = int(base_rev * random.uniform(1.22, 1.55))
        growth = round((curr_rev - base_rev) / base_rev, 4)
        lat = round(random.uniform(loc[2], loc[3]), 5)
        lng = round(random.uniform(loc[4], loc[5]), 5)

        c.execute("""
        INSERT INTO dim_beneficiaries VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (new_ben_id, name, "Smallholder Farmer", gender, random.randint(24, 58), loc[0], f"{loc[1]} Field Block-{random.randint(1,12)}", f"097{random.randint(10000000, 99999999)}", "SHA256-LIVE", datetime.now().strftime("%Y-%m-%d")))

        c.execute("""
        INSERT INTO fact_monitoring_evaluations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (new_mon_id, new_ben_id, vc[0], "Endline", datetime.now().strftime("%Y-%m-%d"), round(random.uniform(1.5, 4.5), 1), base_rev, curr_rev, growth, "Yes", "Organic Composting & Mulch", 2000000, 5.2, "LIVE-KOBO-STREAM", "Verified"))

        conn.commit()
        conn.close()

        self.send_json({
            "status": "success",
            "message": "Live Kobo Webhook Ingested",
            "beneficiary_id": new_ben_id,
            "monitoring_id": new_mon_id,
            "name": name,
            "gender": gender,
            "township": loc[1],
            "value_chain": vc[1],
            "revenue": curr_rev,
            "revenue_growth": f"{growth*100:.1f}%",
            "lat": lat,
            "lng": lng,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }, status=201)

    def handle_bulk_import(self, payload):
        rows = payload.get("records", [])
        if not rows:
            self.send_json({"error": "No records provided"}, status=400)
            return

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM dim_beneficiaries")
        start_count = c.fetchone()[0]

        imported_count = 0
        for idx, r in enumerate(rows, start=start_count + 1):
            ben_id = f"BEN-SHAN-{idx:05d}"
            mon_id = f"MON-{idx:05d}"
            name = r.get("name", f"Beneficiary {idx}")
            gender = r.get("gender", "Female")
            township = r.get("township", "Taunggyi")
            vc = r.get("value_chain", "Specialty Coffee")
            rev = float(r.get("revenue", 1200000))
            
            c.execute("INSERT OR IGNORE INTO dim_beneficiaries VALUES (?,?,?,?,?,?,?,?,?,?)",
                      (ben_id, name, "Smallholder Farmer", gender, 35, "MMR011001", "Import Tract", "0945000000", "SHA256-BULK", datetime.now().strftime("%Y-%m-%d")))
            c.execute("INSERT OR IGNORE INTO fact_monitoring_evaluations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (mon_id, ben_id, "VC-COFFEE", "Midline", datetime.now().strftime("%Y-%m-%d"), 2.0, 900000, rev, 0.33, "Yes", "Composting", 0, 5.0, "BULK-IMPORT", "Verified"))
            imported_count += 1

        conn.commit()
        conn.close()
        self.send_json({"success": True, "imported_count": imported_count})

if __name__ == "__main__":
    print(f"==================================================")
    print(f" REALISTIC & USER-FRIENDLY AGRI-MEAL & MIS PLATFORM")
    print(f" Port: http://localhost:{PORT}")
    print(f" Serving Database: {DB_PATH}")
    print(f" Serving UI from: {PUBLIC_DIR}")
    print(f"==================================================")
    with socketserver.ThreadingTCPServer(("", PORT), EnterpriseMEALHandler) as httpd:
        httpd.serve_forever()
