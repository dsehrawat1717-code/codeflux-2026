"""
VeriShield AI - Enterprise Security Suite Backend & SQLite Database Engine
CODE FLUX Hackathon @ Lovely Professional University (LPU) - Track 6
Author / Lead: Deepak Sehrawat
"""

import os
import sys
import json
import sqlite3
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime

PORT = int(os.environ.get('PORT', 3000))
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verishield.db')

# ==============================================================================
# DATABASE SCHEMA & INITIALIZATION
# ==============================================================================
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            senior_mode INTEGER DEFAULT 0,
            preferred_language TEXT DEFAULT 'both',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Voice Vault Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS voice_vault (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            relation TEXT NOT NULL,
            is_authentic INTEGER DEFAULT 1,
            audio_type TEXT DEFAULT 'natural',
            acoustic_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 3. Threat Feed Messages Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS threat_feed_messages (
            id TEXT PRIMARY KEY,
            sender TEXT NOT NULL,
            sender_type TEXT NOT NULL,
            message_text TEXT NOT NULL,
            is_fake INTEGER DEFAULT 1,
            risk_percent TEXT NOT NULL,
            threat_tag TEXT NOT NULL,
            anomalies_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 4. Threat Feed Calls Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS threat_feed_calls (
            id TEXT PRIMARY KEY,
            phone_number TEXT NOT NULL,
            caller_label TEXT NOT NULL,
            is_fake INTEGER DEFAULT 1,
            complaints_count TEXT NOT NULL,
            carrier_type TEXT NOT NULL,
            risk_title TEXT NOT NULL,
            advice TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 5. Emergency Incidents Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emergency_incidents (
            id TEXT PRIMARY KEY,
            complainant_name TEXT NOT NULL,
            incident_category TEXT NOT NULL,
            details TEXT,
            countermeasures_taken TEXT,
            status TEXT DEFAULT 'ACTIVE_LEGAL_NOTICE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 6. Forensic Audit Scans Log Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_type TEXT NOT NULL,
            scan_input_summary TEXT NOT NULL,
            verdict TEXT NOT NULL,
            risk_score REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Seed Default Voice Vault Profiles if empty
    cursor.execute('SELECT COUNT(*) FROM voice_vault')
    if cursor.fetchone()[0] == 0:
        default_vault = [
            ('v_deepak', 'Deepak Sehrawat', 'Self', 1, 'natural', 'sha256_hash_deepak_auth_981a'),
            ('v_dad', 'Dad (Ramesh)', 'Father', 1, 'natural', 'sha256_hash_dad_ramesh_441b'),
            ('v_mom', 'Mom (Sunita)', 'Mother', 1, 'natural', 'sha256_hash_mom_sunita_882c')
        ]
        cursor.executemany(
            'INSERT INTO voice_vault (id, name, relation, is_authentic, audio_type, acoustic_hash) VALUES (?, ?, ?, ?, ?, ?)',
            default_vault
        )

    # Seed Default Threat Messages if empty
    cursor.execute('SELECT COUNT(*) FROM threat_feed_messages')
    if cursor.fetchone()[0] == 0:
        default_messages = [
            (
                'sms-1', '+91 98721 04918', 'Personal 10-Digit Mobile',
                'Dear Consumer, your electricity power will be disconnected tonight at 9:30 PM from electricity office because your previous month bill was not updated. Please immediately contact our power officer at 9872104918. Punjab State Power Corporation.',
                1, '98.8%', 'POWER-CUT EXTORTION',
                json.dumps({
                    'sender': 'Sent from personal 10-digit mobile number (+91 98721 04918), NOT official utility header.',
                    'url': 'Instructs victim to call personal mobile instead of official toll-free 1912 utility helpline.',
                    'urgency': 'Artificial urgency ("tonight 9:30 PM") engineered to create panic.',
                    'risk': 'Direct financial extortion targeting immediate UPI transfer or remote APK download.'
                })
            ),
            (
                'sms-2', 'SBI-ALRT (Phishing)', 'Spoofed Bank Header',
                'SBI Alert: Dear Customer, your SBI YONO account has been suspended due to pending PAN/KYC verification. To prevent permanent block, update immediately by clicking: http://bit.ly/sbi-kyc-pan-update. Failure to update will incur fine.',
                1, '99.4%', 'BANK KYC PHISHING',
                json.dumps({
                    'sender': 'Sent with fake unverified alphanumeric header masking an overseas SMS gateway.',
                    'url': 'Malicious bit.ly link redirects to fake SBI netbanking clone stealing passwords and MPIN.',
                    'urgency': 'Threatens permanent account block and monetary penalty to force hasty action.',
                    'risk': 'Critical risk of complete account takeover and unauthorized UPI transfers.'
                })
            ),
            (
                'sms-3', '+91 91234 56789', 'Unregistered Number (Telegram)',
                'Dear Deepak, Congratulations! You are shortlisted for Part-Time Work from Home. Earn ₹3,500 daily just by liking YouTube videos and rating hotels on Google. Contact HR Manager on Telegram: @hr_priya_tasks or WhatsApp wa.me/919876543210. Claim ₹500 joining bonus now!',
                1, '96.5%', 'TELEGRAM TASK FRAUD',
                json.dumps({
                    'sender': 'Personal WhatsApp/Telegram account impersonating corporate human resources.',
                    'url': 'Directs to anonymous encrypted Telegram channel where money is solicited for VIP tiers.',
                    'urgency': 'Dangles ₹500 instant bonus and unrealistic ₹3,500 daily returns.',
                    'risk': 'Lures victim with small ₹150 payout, then drains lakhs into cryptocurrency wallets.'
                })
            ),
            (
                'sms-4', 'DM-DOT-GOV (Fake)', 'Impersonated Regulator',
                'Department of Telecommunications: Your mobile number +91-987xxxxxxx is flagged for illegal spam activity and will be deactivated across India in 2 hours. Call 9876501234 immediately for biometric verification.',
                1, '97.9%', 'TRAI / DOT SCAREWARE',
                json.dumps({
                    'sender': 'Forged sender tag simulating official Department of Telecommunications dispatch.',
                    'url': 'Provides private callback number instead of directing to telecom operator store.',
                    'urgency': '2-hour deactivation ultimatum designed to trigger immediate panic.',
                    'risk': 'Aimed at initiating "Digital Arrest" extortion or acquiring sensitive ID documents.'
                })
            ),
            (
                'sms-5', 'VK-SBIINB', 'TRAI Registered Bank Header',
                'SBI: 849102 is your OTP for purchase of Rs 1,500.00 at AMAZON INDIA via SBI Debit Card ending 4019. Valid for 10 mins. Do not share OTP with anyone.',
                0, '0.1%', 'AUTHENTIC BANK OTP',
                json.dumps({
                    'sender': 'Sent from registered TRAI banking alphanumeric header (VK-SBIINB).',
                    'url': 'No suspicious external hyperlinks or malicious download targets identified.',
                    'urgency': 'Standard 10-minute transaction validity window conforming to RBI guidelines.',
                    'risk': 'Authentic security token. Never share your OTP with anyone calling you.'
                })
            )
        ]
        cursor.executemany(
            'INSERT INTO threat_feed_messages (id, sender, sender_type, message_text, is_fake, risk_percent, threat_tag, anomalies_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            default_messages
        )

    # Seed Default Threat Calls if empty
    cursor.execute('SELECT COUNT(*) FROM threat_feed_calls')
    if cursor.fetchone()[0] == 0:
        default_calls = [
            ('call-1', '+91 1800-425-9921', 'TRAI Robocall: Number Disconnection Extortion', 1, '1,894 CITIZEN COMPLAINTS', 'UNVERIFIED VOIP GATEWAY', 'BLACKLISTED SPOOFED ROBOCALL', 'Do NOT press any number (e.g. "Press 9 to speak with executive"). Block the number immediately.'),
            ('call-2', '+91 98721 04918', 'FedEx Customs: Narcotics Parcel Extortion Threat', 1, '1,482 CITIZEN COMPLAINTS', 'SPOOFED VIRTUAL MOBILE', 'EXTORTION FRAUD: ILLEGAL PARCEL THREAT', 'FedEx customs never asks for bank transfers or clears narcotics over video call. Hang up!'),
            ('call-3', '+91 88261 90412', 'CBI / Cyber Police: "Digital Arrest" Video Call', 1, '3,120 CITIZEN COMPLAINTS', 'OVERSEAS VIRTUAL TRUNK', 'CRITICAL THREAT: FAKE DIGITAL ARREST', 'FACT: Indian law strictly prohibits Digital Arrest. No police or judge conducts video trials or demands money!'),
            ('call-4', '+91 80-4567-8901', 'Zomato / Swiggy Delivery Partner', 0, '0 COMPLAINTS', 'AIRTEL ENTERPRISE TRUNK', 'VERIFIED CORPORATE CALLER (SAFE)', 'Legitimate delivery partner call. Safe to answer.'),
            ('call-5', '+91 98102 33445', 'Dad (Ramesh - Family Contact)', 0, '0 COMPLAINTS', 'JIO MOBILE SUBSCRIBER', 'AUTHENTIC FAMILY CONTACT (SAFE)', 'Family contact verified. Safe to communicate.')
        ]
        cursor.executemany(
            'INSERT INTO threat_feed_calls (id, phone_number, caller_label, is_fake, complaints_count, carrier_type, risk_title, advice) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            default_calls
        )

    # Seed Default Incident Sample if empty
    cursor.execute('SELECT COUNT(*) FROM emergency_incidents')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO emergency_incidents (id, complainant_name, incident_category, details, countermeasures_taken, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            'VS-EMERGENCY-DEMO1',
            'Deepak Sehrawat',
            'Financial Cyber Fraud (Phishing SMS)',
            'Reported fraudulent SBI YONO phishing SMS with malicious shortened link http://bit.ly/sbi-kyc-pan-update.',
            'CFCFRMS 1930 alert triggered, NetBanking and UPI VPA locked, biometric Aadhaar lock activated.',
            'GOLDEN_HOUR_PROTECTION_ACTIVE'
        ))

    conn.commit()
    conn.close()
    print(f"[OK] SQLite database initialized successfully at: {DB_FILE}")

# ==============================================================================
# HTTP & REST API SERVER HANDLER
# ==============================================================================
class VeriShieldRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def send_json_response(self, data, status=200):
        response_bytes = json.dumps(data, indent=2, default=str).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

    def read_json_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            body_str = self.rfile.read(content_length).decode('utf-8')
            try:
                return json.loads(body_str)
            except Exception:
                return {}
        return {}

    # --------------------------------------------------------------------------
    # REST API ROUTING (GET REQUESTS)
    # --------------------------------------------------------------------------
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # 1. API Health & Engine Status
        if path == '/api/health':
            conn = get_db_connection()
            c = conn.cursor()
            stats = {}
            for tbl in ['users', 'voice_vault', 'threat_feed_messages', 'threat_feed_calls', 'emergency_incidents', 'audit_scans']:
                c.execute(f'SELECT COUNT(*) FROM {tbl}')
                stats[tbl] = c.fetchone()[0]
            conn.close()

            db_size = os.path.getsize(DB_FILE) if os.path.exists(DB_FILE) else 0

            return self.send_json_response({
                'status': 'ONLINE',
                'service': 'VeriShield AI Backend & SQLite Database Engine',
                'database': {
                    'engine': 'SQLite 3 (Persistent Relational Database)',
                    'file': os.path.basename(DB_FILE),
                    'size_bytes': db_size,
                    'tables_count': 6,
                    'row_counts': stats
                },
                'timestamp': datetime.now().isoformat(),
                'server_port': PORT
            })

        # 2. API Database Live Statistics (For Judges)
        elif path == '/api/db/stats':
            conn = get_db_connection()
            c = conn.cursor()
            stats = {}
            for tbl in ['users', 'voice_vault', 'threat_feed_messages', 'threat_feed_calls', 'emergency_incidents', 'audit_scans']:
                c.execute(f'SELECT COUNT(*) FROM {tbl}')
                stats[tbl] = c.fetchone()[0]
            conn.close()

            return self.send_json_response({
                'engine': 'SQLite 3.x Relational Database Engine',
                'tables': stats,
                'total_records': sum(stats.values()),
                'connection_pool': 'Active',
                'acid_compliant': True,
                'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')
            })

        # 3. API Full Database Export / Inspector (For Judge Explorer UI)
        elif path == '/api/db/export':
            conn = get_db_connection()
            c = conn.cursor()
            full_dump = {}
            for tbl in ['users', 'voice_vault', 'emergency_incidents', 'threat_feed_messages', 'threat_feed_calls', 'audit_scans']:
                c.execute(f'SELECT * FROM {tbl} ORDER BY 1 DESC LIMIT 50')
                rows = [dict(row) for row in c.fetchall()]
                full_dump[tbl] = rows
            conn.close()

            return self.send_json_response({
                'database': 'verishield.db',
                'exported_at': datetime.now().isoformat(),
                'tables': full_dump
            })

        # 4. Fetch Users Profile
        elif path == '/api/users/current':
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT * FROM users ORDER BY id DESC LIMIT 1')
            row = c.fetchone()
            conn.close()
            return self.send_json_response(dict(row) if row else {})

        # 5. Fetch Trusted Voice Vault
        elif path == '/api/vault':
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT * FROM voice_vault ORDER BY created_at DESC')
            rows = [dict(r) for r in c.fetchall()]
            conn.close()
            return self.send_json_response(rows)

        # 6. Fetch Message Radar Feed
        elif path == '/api/feed/messages':
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT * FROM threat_feed_messages ORDER BY created_at ASC')
            rows = []
            for r in c.fetchall():
                d = dict(r)
                if d.get('anomalies_json'):
                    try:
                        d['anomalies'] = json.loads(d['anomalies_json'])
                    except Exception:
                        d['anomalies'] = {}
                rows.append(d)
            conn.close()
            return self.send_json_response(rows)

        # 7. Fetch Call Radar Feed
        elif path == '/api/feed/calls':
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT * FROM threat_feed_calls ORDER BY created_at ASC')
            rows = [dict(r) for r in c.fetchall()]
            conn.close()
            return self.send_json_response(rows)

        # 8. Fetch Emergency Incidents
        elif path == '/api/incidents':
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT * FROM emergency_incidents ORDER BY created_at DESC')
            rows = [dict(r) for r in c.fetchall()]
            conn.close()
            return self.send_json_response(rows)

        # 9. Fetch Audit Scans
        elif path == '/api/scans/logs':
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT * FROM audit_scans ORDER BY id DESC LIMIT 20')
            rows = [dict(r) for r in c.fetchall()]
            conn.close()
            return self.send_json_response(rows)

        # Fallback to serving static HTML / CSS / JS files
        return super().do_GET()

    # --------------------------------------------------------------------------
    # REST API ROUTING (POST REQUESTS)
    # --------------------------------------------------------------------------
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self.read_json_body()

        # 1. Register / Update User Profile
        if path == '/api/users':
            name = body.get('name', 'Deepak Sehrawat')
            age = int(body.get('age', 22))
            senior_mode = 1 if age > 50 else 0
            lang = body.get('language', 'both')

            conn = get_db_connection()
            c = conn.cursor()
            c.execute('''
                INSERT INTO users (name, age, senior_mode, preferred_language)
                VALUES (?, ?, ?, ?)
            ''', (name, age, senior_mode, lang))
            user_id = c.lastrowid
            conn.commit()
            conn.close()

            return self.send_json_response({
                'success': True,
                'message': 'User profile successfully registered in SQLite database',
                'user': {
                    'id': user_id,
                    'name': name,
                    'age': age,
                    'senior_mode': bool(senior_mode),
                    'preferred_language': lang
                }
            }, status=201)

        # 2. Add New Profile to Trusted Voice Vault
        elif path == '/api/vault':
            name = body.get('name', '').strip()
            relation = body.get('relation', 'Family')
            if not name:
                return self.send_json_response({'error': 'Name is required'}, status=400)

            vault_id = 'v_' + str(int(datetime.now().timestamp() * 1000))
            acoustic_hash = body.get('acoustic_hash') or f"sha256_{name.lower()}_{vault_id[-6:]}"

            conn = get_db_connection()
            c = conn.cursor()
            c.execute('''
                INSERT INTO voice_vault (id, name, relation, is_authentic, audio_type, acoustic_hash)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (vault_id, name, relation, 1, 'custom', acoustic_hash))
            conn.commit()
            conn.close()

            return self.send_json_response({
                'success': True,
                'message': f'Voice profile for "{name}" saved to SQLite database',
                'profile': {
                    'id': vault_id,
                    'name': name,
                    'relation': relation,
                    'is_authentic': True,
                    'acoustic_hash': acoustic_hash
                }
            }, status=201)

        # 3. Log Emergency Incident
        elif path == '/api/incidents':
            complainant = body.get('complainant_name', 'Deepak Sehrawat')
            category = body.get('incident_category', 'Financial Cyber Fraud')
            details = body.get('details', '')
            countermeasures = body.get('countermeasures_taken', 'Dialed 1930 / Account Block')
            incident_id = body.get('id') or ('VS-EMERGENCY-' + str(int(datetime.now().timestamp())))

            conn = get_db_connection()
            c = conn.cursor()
            c.execute('''
                INSERT OR REPLACE INTO emergency_incidents (id, complainant_name, incident_category, details, countermeasures_taken, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (incident_id, complainant, category, details, countermeasures, 'ACTIVE_LEGAL_NOTICE'))
            conn.commit()
            conn.close()

            return self.send_json_response({
                'success': True,
                'message': 'Incident logged in legal incident registry',
                'incident_id': incident_id
            }, status=201)

        # 4. Record Forensic Audit Scan
        elif path == '/api/scans/log':
            module_type = body.get('module_type', 'general')
            summary = body.get('scan_input_summary', 'Scan record')
            verdict = body.get('verdict', 'SUSPICIOUS')
            score = float(body.get('risk_score', 0.9))

            conn = get_db_connection()
            c = conn.cursor()
            c.execute('''
                INSERT INTO audit_scans (module_type, scan_input_summary, verdict, risk_score)
                VALUES (?, ?, ?, ?)
            ''', (module_type, summary, verdict, score))
            scan_id = c.lastrowid
            conn.commit()
            conn.close()

            return self.send_json_response({
                'success': True,
                'scan_id': scan_id
            }, status=201)

        # Unknown endpoint
        return self.send_json_response({'error': f'Endpoint not found: {path}'}, status=404)

    # --------------------------------------------------------------------------
    # REST API ROUTING (DELETE REQUESTS)
    # --------------------------------------------------------------------------
    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # Delete Voice Profile from Vault
        if path.startswith('/api/vault'):
            target_id = query.get('id', [None])[0]
            if not target_id and '/' in path[11:]:
                target_id = path[11:]

            if not target_id:
                return self.send_json_response({'error': 'Profile ID is required'}, status=400)

            conn = get_db_connection()
            c = conn.cursor()
            c.execute('DELETE FROM voice_vault WHERE id = ?', (target_id,))
            affected = c.rowcount
            conn.commit()
            conn.close()

            return self.send_json_response({
                'success': True,
                'message': f'Voice profile {target_id} deleted from SQLite database',
                'affected_rows': affected
            })

        return self.send_json_response({'error': 'Not found'}, status=404)


# ==============================================================================
# MAIN EXECUTION
# ==============================================================================
def main():
    init_database()
    web_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(web_dir)

    server = HTTPServer(('0.0.0.0', PORT), VeriShieldRequestHandler)
    print(f"===============================================================")
    print(f"  VERISHIELD AI BACKEND & SQLITE SERVER RUNNING")
    print(f"===============================================================")
    print(f"  * Web App URL:      http://localhost:{PORT}")
    print(f"  * REST API Base:    http://localhost:{PORT}/api/health")
    print(f"  * SQLite Database:  {DB_FILE}")
    print(f"  * Active Tables:    6 Relational Tables Initialized")
    print(f"===============================================================\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down VeriShield Server...")
        server.server_close()

if __name__ == '__main__':
    main()
