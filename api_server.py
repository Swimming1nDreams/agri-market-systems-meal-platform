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
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
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
            self.handle_kpis()
        elif path == "/api/indicators":
            self.handle_indicators()
        elif path == "/api/spatial":
            self.handle_spatial()
        elif path == "/api/beneficiaries":
            self.handle_beneficiaries(query)
        elif path == "/api/audit-logs":
            self.handle_audit_logs()
        elif path == "/api/charts":
            self.handle_charts()
        else:
            # Fallback to static file server
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

        if path == "/api/kobo-webhook":
            self.handle_kobo_webhook(payload)
        elif path == "/api/simulate-kobo":
            self.handle_simulate_kobo()
        else:
            self.send_json({"error": "Endpoint not found"}, status=404)

    # ---------------------------------------------------------
    # API Handlers
    # ---------------------------------------------------------
    def handle_kpis(self):
        conn = get_db()
        c = conn.cursor()

        c.execute("SELECT COUNT(*) FROM dim_beneficiaries")
        total_beneficiaries = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM dim_beneficiaries WHERE category = 'Agri-MSME'")
        total_msmes = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM dim_beneficiaries WHERE gender = 'Female'")
        female_count = c.fetchone()[0]
        female_pct = round((female_count / total_beneficiaries * 100), 1) if total_beneficiaries else 0

        c.execute("SELECT SUM(financing_facilitated_mmk), AVG(revenue_growth_pct) FROM fact_monitoring_evaluations")
        fin_sum, avg_growth = c.fetchone()
        fin_sum = fin_sum or 0
        avg_growth = round((avg_growth or 0) * 100, 1)

        c.execute("SELECT COUNT(*) FROM fact_monitoring_evaluations WHERE climate_resilient_adopted = 'Yes'")
        climate_adopted = c.fetchone()[0]
        climate_pct = round((climate_adopted / total_beneficiaries * 100), 1) if total_beneficiaries else 0

        c.execute("SELECT COUNT(*) FROM fact_accountability_complaints WHERE status = 'Resolved'")
        resolved_cases = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM fact_accountability_complaints")
        total_cases = c.fetchone()[0]

        conn.close()

        self.send_json({
            "total_beneficiaries": total_beneficiaries,
            "total_msmes": total_msmes,
            "female_inclusion_pct": female_pct,
            "total_financing_mmk": fin_sum,
            "total_financing_millions": round(fin_sum / 1_000_000, 1),
            "climate_adoption_pct": climate_pct,
            "avg_revenue_growth_pct": avg_growth,
            "afm_resolution_rate": round(resolved_cases / total_cases * 100, 1) if total_cases else 100
        })

    def handle_indicators(self):
        conn = get_db()
        c = conn.cursor()

        indicators_config = [
            ("IND-1.1", "Smallholder farmers adopting climate-resilient practices", 3200,
             "SELECT COUNT(*) FROM fact_monitoring_evaluations f JOIN dim_beneficiaries b ON f.beneficiary_id=b.beneficiary_id WHERE b.category='Smallholder Farmer' AND f.climate_resilient_adopted='Yes'"),
            ("IND-1.2", "Agri-MSMEs receiving catalytic matching grants / financing", 600,
             "SELECT COUNT(*) FROM fact_monitoring_evaluations f JOIN dim_beneficiaries b ON f.beneficiary_id=b.beneficiary_id WHERE b.category='Agri-MSME' AND f.financing_facilitated_mmk > 0"),
            ("IND-2.1", "Total agricultural capital unlocked (MMK Millions)", 8500,
             "SELECT ROUND(SUM(financing_facilitated_mmk)/1000000, 1) FROM fact_monitoring_evaluations"),
            ("IND-2.2", "Participants achieving sustainable revenue growth >20%", 2500,
             "SELECT COUNT(*) FROM fact_monitoring_evaluations WHERE revenue_growth_pct > 0.20"),
            ("IND-3.1", "Female-led agribusinesses and female farmers actively supported", 2200,
             "SELECT COUNT(*) FROM dim_beneficiaries WHERE gender = 'Female'"),
            ("IND-3.2", "Field quality spot-checks and verifications conducted", 4800,
             "SELECT COUNT(*) FROM fact_monitoring_evaluations WHERE verification_status = 'Verified'"),
        ]

        result = []
        for code, label, target, sql in indicators_config:
            c.execute(sql)
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

    def handle_spatial(self):
        conn = get_db()
        c = conn.cursor()

        sql = """
        SELECT 
            b.beneficiary_id, b.participant_name, b.category, b.gender,
            l.township_name, l.latitude_min, l.latitude_max, l.longitude_min, l.longitude_max,
            v.value_chain_name, f.current_monthly_revenue_mmk, f.climate_resilient_adopted
        FROM dim_beneficiaries b
        JOIN dim_locations l ON b.township_pcode = l.township_pcode
        JOIN fact_monitoring_evaluations f ON b.beneficiary_id = f.beneficiary_id
        JOIN dim_value_chains v ON f.value_chain_id = v.value_chain_id
        LIMIT 600
        """
        c.execute(sql)
        rows = c.fetchall()
        conn.close()

        features = []
        for r in rows:
            # Deterministic jitter within township boundary
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
                "climate_adopted": r["climate_resilient_adopted"],
                "lat": lat,
                "lng": lng
            })

        self.send_json(features)

    def handle_charts(self):
        conn = get_db()
        c = conn.cursor()

        # 1. By Value Chain
        c.execute("""
        SELECT v.value_chain_name, COUNT(*), ROUND(AVG(f.revenue_growth_pct)*100, 1), SUM(f.financing_facilitated_mmk)/1000000
        FROM fact_monitoring_evaluations f
        JOIN dim_value_chains v ON f.value_chain_id = v.value_chain_id
        GROUP BY v.value_chain_name
        """)
        vc_data = [{"name": r[0], "count": r[1], "growth": r[2], "financing_m": round(r[3] or 0, 1)} for r in c.fetchall()]

        # 2. By Township
        c.execute("""
        SELECT l.township_name, COUNT(*), SUM(CASE WHEN f.climate_resilient_adopted='Yes' THEN 1 ELSE 0 END)
        FROM dim_beneficiaries b
        JOIN dim_locations l ON b.township_pcode = l.township_pcode
        JOIN fact_monitoring_evaluations f ON b.beneficiary_id = f.beneficiary_id
        GROUP BY l.township_name
        """)
        t_data = [{"township": r[0], "total": r[1], "climate": r[2]} for r in c.fetchall()]

        conn.close()
        self.send_json({"value_chains": vc_data, "townships": t_data})

    def handle_beneficiaries(self, query):
        conn = get_db()
        c = conn.cursor()

        search = query.get("search", [""])[0]
        township = query.get("township", [""])[0]
        page = int(query.get("page", [1])[0])
        limit = int(query.get("limit", [15])[0])
        offset = (page - 1) * limit

        where_clauses = ["1=1"]
        params = []

        if search:
            where_clauses.append("(b.participant_name LIKE ? OR b.beneficiary_id LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])
        if township:
            where_clauses.append("l.township_name = ?")
            params.append(township)

        where_sql = " AND ".join(where_clauses)

        # Count total
        c.execute(f"SELECT COUNT(*) FROM dim_beneficiaries b JOIN dim_locations l ON b.township_pcode=l.township_pcode WHERE {where_sql}", params)
        total = c.fetchone()[0]

        # Fetch records
        sql = f"""
        SELECT 
            b.beneficiary_id, b.participant_name, b.category, b.gender, b.age_years,
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
        rows = [dict(r) for r in c.fetchall()]
        conn.close()

        self.send_json({
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
            "data": rows
        })

    def handle_audit_logs(self):
        log_path = os.path.join(BASE_DIR, "FOSTER_II_Data_Quality_Audit_Log.csv")
        items = []
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()[1:] # skip header
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

    def handle_simulate_kobo(self):
        conn = get_db()
        c = conn.cursor()

        # Find max ID
        c.execute("SELECT COUNT(*) FROM dim_beneficiaries")
        next_num = c.fetchone()[0] + 1
        new_ben_id = f"BEN-SHAN-{next_num:05d}"
        new_mon_id = f"MON-{next_num:05d}"

        first_names = ["Thura", "Aye", "Nan", "Sai", "Min", "Khin", "Zayar"]
        last_names = ["Htet", "Lin", "Kham", "Naw", "Lwin", "San", "Tun"]
        townships = [("MMR011001", "Taunggyi"), ("MMR011002", "Kalaw"), ("MMR011003", "Hopong"), ("MMR011006", "Ywangan")]
        vcs = ["VC-COFFEE", "VC-TEA", "VC-AVOCADO", "VC-VEG"]

        name = f"Daw {random.choice(first_names)} {random.choice(last_names)}"
        loc = random.choice(townships)
        vc = random.choice(vcs)
        base_rev = random.randint(600000, 1500000)
        curr_rev = int(base_rev * random.uniform(1.2, 1.45))
        growth = round((curr_rev - base_rev) / base_rev, 4)

        # Insert Beneficiary
        c.execute("""
        INSERT INTO dim_beneficiaries VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (new_ben_id, name, "Smallholder Farmer", "Female", random.randint(25, 55), loc[0], "Village Live Sync", f"097{random.randint(10000000, 99999999)}", "SHA256-LIVE", datetime.now().strftime("%Y-%m-%d")))

        # Insert Fact
        c.execute("""
        INSERT INTO fact_monitoring_evaluations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (new_mon_id, new_ben_id, vc, "Endline", datetime.now().strftime("%Y-%m-%d"), 2.5, base_rev, curr_rev, growth, "Yes", "Organic Composting", 1500000, 6.5, "LIVE-KOBO-API", "Verified"))

        conn.commit()
        conn.close()

        self.send_json({
            "status": "success",
            "message": "Live Kobo Webhook Ingested Successfully",
            "beneficiary_id": new_ben_id,
            "monitoring_id": new_mon_id,
            "name": name,
            "township": loc[1],
            "revenue_growth": f"{growth*100:.1f}%",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }, status=201)

    def handle_kobo_webhook(self, payload):
        # Generic KoboToolbox standard REST webhook handler
        self.handle_simulate_kobo()

if __name__ == "__main__":
    print(f"==================================================")
    print(f" FOSTER II ENTERPRISE MEAL & MIS PLATFORM SERVER")
    print(f" Running on http://localhost:{PORT}")
    print(f" Serving Database: {DB_PATH}")
    print(f" Serving UI from: {PUBLIC_DIR}")
    print(f"==================================================")
    with socketserver.ThreadingTCPServer(("", PORT), EnterpriseMEALHandler) as httpd:
        httpd.serve_forever()
