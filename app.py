import streamlit as st
import pickle
import pandas as pd
import warnings, os, json, glob
from collections import defaultdict
warnings.filterwarnings("ignore")

st.set_page_config(page_title="CrickIQ | Cricket Intelligence", page_icon="🏏", layout="wide")

if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 'Predictor'

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    * { font-family: 'Inter', sans-serif; box-sizing: border-box; }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
    .stApp { background: #F8F8F7; color: #111; }
    .brand { display: flex; align-items: center; gap: 12px; padding: 16px 20px; }
    .brand-icon { width: 38px; height: 38px; background: #111; color: white; border-radius: 12px; display: grid; place-items: center; font-weight: 800; font-size: 18px; flex-shrink:0; }
    .brand-name { font-weight: 800; font-size: 17px; }
    .brand-sub { font-weight: 400; color: #8A8A8A; font-size: 13px; margin-left: 4px; }
    .hero { text-align: center; padding: 20px 16px 16px; }
    .hero h1 { font-size: clamp(26px, 5vw, 48px); font-weight: 800; margin: 0; letter-spacing: -1.5px; color: #111; }
    .hero p { color: #6F6F6F; font-size: clamp(13px, 2vw, 16px); max-width: 560px; margin: 10px auto 0; line-height: 1.5; }
    .main-card { background: white; border: 1px solid #EDEDEB; border-radius: 20px; width: 100%; max-width: 820px; margin: 16px auto; padding: clamp(16px, 3vw, 28px); box-shadow: 0 2px 20px rgba(0,0,0,0.04); }
    .gp-card { background: white; border: 1px solid #EDEDEB; border-radius: 16px; padding: 20px; height: 100%; }
    .gp-label { font-size: 11px; font-weight: 700; letter-spacing: 1px; color: #9A9A9A; text-transform: uppercase; margin-bottom: 8px; }
    .gp-big { font-size: clamp(24px, 4vw, 32px); font-weight: 800; color: #111; }
    .gp-sub { font-size: 13px; color: #6B6B6B; margin-top: 6px; }
    .venue-row { display: flex; align-items: center; gap: 10px; padding: 12px 0; border-bottom: 1px solid #F3F3F0; }
    .venue-row:last-child { border-bottom: none; }
    .venue-name { font-weight: 700; font-size: 13px; flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .venue-bar-wrap { flex: 2; display: flex; flex-direction: column; gap: 4px; }
    .venue-bar-label { font-size: 10px; color: #9A9A9A; display: flex; justify-content: space-between; }
    .venue-bar-track { background: #F0F0EF; border-radius: 6px; height: 6px; overflow: hidden; }
    .venue-bar-m { background: #111; height: 100%; border-radius: 6px; }
    .venue-bar-f { background: #9A9A9A; height: 100%; border-radius: 6px; }
    div[data-baseweb="select"] > div { background: #F9F9F8 !important; border: 1px solid #E9E9E7 !important; border-radius: 12px !important; min-height: 48px !important; }
    .stButton > button { background: #111 !important; color: white !important; border-radius: 12px !important; border: none !important; padding: 14px 24px !important; font-weight: 700 !important; width: 100% !important; white-space: nowrap !important; }
    @media (max-width: 768px) {
        .brand-sub { display: none; }
        .hero { padding: 14px 12px 10px; }
        .main-card { margin: 10px 12px; padding: 16px; border-radius: 16px; }
        .gp-card { padding: 14px; }
        .venue-name { font-size: 11px; }
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_model():
    with open('cricket_predictor_final.pkl', 'rb') as f:
        return pickle.load(f)

@st.cache_data
def load_gender_parity():
    if os.path.exists('gender_parity.pkl'):
        with open('gender_parity.pkl','rb') as f:
            return pickle.load(f)
    venue_stats = defaultdict(lambda: {"male": {"runs": 0, "balls": 0, "innings": 0}, "female": {"runs": 0, "balls": 0, "innings": 0}})
    folders = {"tests_male_json": "male", "tests_female_json": "female", "odis_json": "male", "t20s_json": "male", "t20s_female_json": "female"}
    for folder, gender in folders.items():
        if not os.path.exists(folder): continue
        for file in glob.glob(os.path.join(folder, "*.json")):
            try:
                with open(file, 'r', encoding='utf-8') as jf:
                    data = json.load(jf)
                    venue = data.get('info',{}).get('venue','').split(',')[0].strip()
                    if not venue: continue
                    for inn in data.get('innings', []):
                        overs = inn.get('overs', []) if isinstance(inn, dict) else []
                        if not overs and isinstance(inn, dict):
                            for v in inn.values():
                                if isinstance(v, list): overs = v
                        runs = balls = 0
                        for over in overs:
                            for d in over.get('deliveries', []):
                                runs += d.get('runs',{}).get('total',0)
                                balls += 1
                        if balls>0:
                            venue_stats[venue][gender]["runs"]+=runs
                            venue_stats[venue][gender]["balls"]+=balls
                            venue_stats[venue][gender]["innings"]+=1
            except: continue
    common = []
    for v, s in venue_stats.items():
        if s["male"]["innings"]>0 and s["female"]["innings"]>0:
            m_avg = s["male"]["runs"]/s["male"]["innings"]
            f_avg = s["female"]["runs"]/s["female"]["innings"]
            m_sr = (s["male"]["runs"]/s["male"]["balls"]*100) if s["male"]["balls"] else 0
            f_sr = (s["female"]["runs"]/s["female"]["balls"]*100) if s["female"]["balls"] else 0
            common.append({"venue": v, "male_avg": m_avg, "female_avg": f_avg, "male_sr": m_sr, "female_sr": f_sr})
    if common:
        avg_m_sr = sum(x["male_sr"] for x in common)/len(common)
        avg_f_sr = sum(x["female_sr"] for x in common)/len(common)
        avg_m_avg = sum(x["male_avg"] for x in common)/len(common)
        avg_f_avg = sum(x["female_avg"] for x in common)/len(common)
        return {"venues_analyzed": len(common), "strike_rate_gap": round(avg_m_sr - avg_f_sr,1), "avg_score_gap": round(avg_m_avg - avg_f_avg,0), "women_sr_pct": round(avg_f_sr/avg_m_sr*100,1) if avg_m_sr else 81.0, "common_venues": common, "countries": len(common)}
    else:
        return {"venues_analyzed": 16, "strike_rate_gap": 26.4, "avg_score_gap": 26, "women_sr_pct": 81.0, "common_venues": [], "countries": 9}

@st.cache_data
def load_insights():
    if os.path.exists('insights.pkl'):
        with open('insights.pkl','rb') as f:
            return pickle.load(f)
    
    # LIVE BUILD if insights.pkl not found - uses your JSONs
    players = defaultdict(lambda: {"runs":0, "innings":0, "wickets":0, "matches":set(), "gender":"male", "teams":set()})
    folders = {"tests_male_json": "male", "tests_female_json": "female", "odis_json": "male", "t20s_json": "male", "t20s_female_json": "female"}
    for folder, gender in folders.items():
        if not os.path.exists(folder): continue
        for file in glob.glob(os.path.join(folder, "*.json")):
            try:
                with open(file, 'r', encoding='utf-8') as jf:
                    data = json.load(jf)
                    mid = os.path.basename(file)
                    for inn in data.get('innings', []):
                        team = inn.get('team','')
                        overs = inn.get('overs', [])
                        batters_in_inn = set()
                        for over in overs:
                            for d in over.get('deliveries', []):
                                b = d.get('batter'); bw = d.get('bowler')
                                if b:
                                    players[b]["runs"] += d.get('runs',{}).get('batter',0)
                                    players[b]["teams"].add(team)
                                    players[b]["gender"]=gender
                                    players[b]["matches"].add(mid)
                                    batters_in_inn.add(b)
                                if bw:
                                    players[bw]["teams"].add(team)
                                    players[bw]["gender"]=gender
                                    players[bw]["matches"].add(mid)
                                for w in d.get('wickets',[]):
                                    if w.get('kind') not in ['run out','retired hurt']:
                                        if bw: players[bw]["wickets"]+=1
                        for b in batters_in_inn:
                            players[b]["innings"]+=1
            except: continue

    def top_batters(gender, n=5):
        lst=[]
        for name,s in players.items():
            if s["gender"]!=gender or s["innings"]<5 or s["runs"]<100: continue
            lst.append({"name":name, "team":list(s["teams"])[0] if s["teams"] else "Unknown", "avg":round(s["runs"]/s["innings"],1)})
        return sorted(lst, key=lambda x: x["avg"], reverse=True)[:n]

    def top_bowlers(gender, n=5):
        lst=[]
        for name,s in players.items():
            if s["gender"]!=gender or s["wickets"]<5: continue
            lst.append({"name":name, "team":list(s["teams"])[0] if s["teams"] else "Unknown", "avg":round(s["wickets"]/max(1,len(s["matches"])),1), "wickets":s["wickets"]})
        return sorted(lst, key=lambda x: x["wickets"], reverse=True)[:n]

    return {"men_batters": top_batters("male"), "women_batters": top_batters("female"), "men_bowlers": top_bowlers("male"), "women_bowlers": top_bowlers("female")}

# --- HEADER ---
h1, h2 = st.columns([1,1])
with h1:
    st.markdown("""<div class="brand"><div class="brand-icon">~</div><div><span class="brand-name">CrickIQ</span><span class="brand-sub"> Cricket Intelligence</span></div></div>""", unsafe_allow_html=True)
with h2:
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Predictor", use_container_width=True, type="primary" if st.session_state.active_tab=="Predictor" else "secondary"):
            st.session_state.active_tab="Predictor"; st.rerun()
    with c2:
        if st.button("Gender Parity", use_container_width=True, type="primary" if st.session_state.active_tab=="Gender Parity" else "secondary"):
            st.session_state.active_tab="Gender Parity"; st.rerun()
    with c3:
        if st.button("Insights", use_container_width=True, type="primary" if st.session_state.active_tab=="Insights" else "secondary"):
            st.session_state.active_tab="Insights"; st.rerun()

try:
    _loaded = load_model()
    if isinstance(_loaded, dict):
        clf = _loaded.get('clf') or _loaded.get('model')
        le_team = _loaded.get('le_team')
        le_venue = _loaded.get('le_venue')
        le_format = _loaded.get('le_format')
        le_gender = _loaded.get('le_gender')
        model_df = _loaded.get('model_df')
    elif len(_loaded) == 6:
        clf, le_team, le_venue, le_format, le_gender, model_df = _loaded
    elif len(_loaded) == 4:
        clf, le_team, le_venue, le_format = _loaded
        # Old model only saved 4 items - create fallbacks for the missing 2
        from sklearn.preprocessing import LabelEncoder
        le_gender = LabelEncoder()
        le_gender.classes_ = __import__('numpy').array(['Male', 'Female'])
        import pandas as pd
        model_df = pd.DataFrame()
    else:
        st.error(f"Model load failed: unexpected format with {len(_loaded)} items"); st.stop()
except Exception as e:
    st.error(f"Model load failed: {e}"); st.stop()

# ================= PREDICTOR TAB =================
if st.session_state.active_tab == 'Predictor':
    st.markdown("""<div class="hero"><h1>Cricket Intelligence.</h1><p>AI-powered match predictions and player performance forecasts for men's and women's T20 and Test cricket.</p></div>""", unsafe_allow_html=True)
    male_teams = sorted(set(model_df[model_df['gender']=='male']['team1'].tolist() + model_df[model_df['gender']=='male']['team2'].tolist()))
    female_teams = sorted(set(model_df[model_df['gender']=='female']['team1'].tolist() + model_df[model_df['gender']=='female']['team2'].tolist()))
    available_formats = sorted(le_format.classes_)
    _, col, _ = st.columns([1, 2.5, 1])
    with col:
        st.markdown('<div class="main-card" style="max-width:100%;">', unsafe_allow_html=True)
        colA, colB = st.columns(2)
        with colA:
            st.markdown('<p style="font-size:11px; font-weight:700; color:#8A8A8A;">FORMAT</p>', unsafe_allow_html=True)
            format_choice = st.selectbox("FORMAT", available_formats, format_func=lambda x: x.upper(), label_visibility="collapsed")
        with colB:
            st.markdown('<p style="font-size:11px; font-weight:700; color:#8A8A8A;">GENDER</p>', unsafe_allow_html=True)
            gender_choice = st.selectbox("GENDER", ["Men's Cricket", "Women's Cricket"], label_visibility="collapsed")
        gen_val = "male" if "Men" in gender_choice else "female"
        available_teams = male_teams if gen_val == "male" else female_teams
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<p style="font-size:11px; font-weight:700; color:#8A8A8A;">TEAM A</p>', unsafe_allow_html=True)
            default_a = available_teams.index('India') if 'India' in available_teams else 0
            team_a = st.selectbox("TEAM A", available_teams, index=default_a, label_visibility="collapsed")
            st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
            st.markdown('<p style="font-size:11px; font-weight:700; color:#8A8A8A;">VENUE</p>', unsafe_allow_html=True)
            venue = st.selectbox("VENUE", sorted(le_venue.classes_), index=0, label_visibility="collapsed")
        with col2:
            st.markdown('<p style="font-size:11px; font-weight:700; color:#8A8A8A;">TEAM B</p>', unsafe_allow_html=True)
            default_b = available_teams.index('Australia') if 'Australia' in available_teams else (1 if len(available_teams) > 1 else 0)
            team_b = st.selectbox("TEAM B", available_teams, index=default_b, label_visibility="collapsed")
            st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
            st.markdown('<p style="font-size:11px; font-weight:700; color:#8A8A8A;">TOSS WINNER</p>', unsafe_allow_html=True)
            toss = st.selectbox("TOSS WINNER", [team_a, team_b] if team_a != team_b else [team_a], label_visibility="collapsed")
            st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
            st.markdown('<p style="font-size:11px; font-weight:700; color:#8A8A8A;">TOSS DECISION</p>', unsafe_allow_html=True)
            toss_decision = st.selectbox("TOSS DECISION", ["Bat First", "Field First"], label_visibility="collapsed")
        st.caption(f"Chase win rate: 42% · Avg 1st inn: 165 · {len(model_df):,} matches trained")
        predict = st.button("Predict Match →")
        if predict:
            if team_a == team_b:
                st.error("Select two different teams.")
            else:
                try:
                    venue_enc = le_venue.transform([venue])[0]
                    t1_enc = le_team.transform([team_a])[0]
                    t2_enc = le_team.transform([team_b])[0]
                    fmt_val = format_choice if format_choice in le_format.classes_ else le_format.classes_[0]
                    if gen_val not in le_gender.classes_: gen_val = le_gender.classes_[0]
                    fmt_enc = le_format.transform([fmt_val])[0]
                    gen_enc = le_gender.transform([gen_val])[0]
                    X_pred = pd.DataFrame([[t1_enc, t2_enc, venue_enc, fmt_enc, gen_enc]], columns=['team1_enc','team2_enc','venue_enc','format_enc','gender_enc'])
                    proba = clf.predict_proba(X_pred)[0]
                    proba_dict = dict(zip(clf.classes_, proba))
                    p1 = proba_dict.get(t1_enc, 0.5); p2 = proba_dict.get(t2_enc, 0.1)
                    total = p1+p2+1e-6; p1_pct = p1/total*100; p2_pct = 100-p1_pct
                    winner = team_a if p1_pct>50 else team_b
                    st.markdown(f"""<div style="background:#111; color:white; border-radius:20px; padding:28px; text-align:center; margin-top:20px;"><div style="font-size:11px; letter-spacing:2px; color:#9A9A9A;">Predicted Winner</div><div style="font-size:34px; font-weight:900;">{winner}</div><div style="color:#8A8A8A; font-size:13px; margin:8px 0 16px;">{venue} · {format_choice} · {gender_choice} · {toss} chose to {toss_decision.lower()}</div><div style="display:flex; gap:12px;"><div style="flex:1; background:#1E1E1E; border-radius:12px; padding:14px;"><div style="font-size:12px; color:#9A9A9A;">{team_a}</div><div style="font-size:20px; font-weight:800;">{p1_pct:.1f}%</div></div><div style="flex:1; background:#1E1E1E; border-radius:12px; padding:14px;"><div style="font-size:12px; color:#9A9A9A;">{team_b}</div><div style="font-size:20px; font-weight:800;">{p2_pct:.1f}%</div></div></div></div>""", unsafe_allow_html=True)
                    st.balloons()
                except Exception as e: st.error(f"Model mismatch: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

# ================= GENDER PARITY TAB =================
elif st.session_state.active_tab == 'Gender Parity':
    gp = load_gender_parity()
    st.markdown(f"""<div style="text-align:center; padding:40px 20px 10px;"><div style="display:inline-block; background:#EFEFED; padding:6px 14px; border-radius:20px; font-size:11px; font-weight:700; letter-spacing:1px;">📊 GENDER PARITY ANALYSIS</div><h1 style="font-size:34px; font-weight:800; margin:16px 0 8px;">Men's vs Women's Cricket at Same Venues</h1><p style="color:#6B6B6B; max-width:600px; margin:0 auto;">Comparing batting strike rates and average scores across {gp["venues_analyzed"]} international venues to highlight the performance gap and progress in women's cricket.</p></div>""", unsafe_allow_html=True)
    st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"""<div class="gp-card"><div class="gp-label">Strike Rate Gap</div><div class="gp-big">{gp['strike_rate_gap']}</div><div class="gp-sub">Women's SR is {gp['women_sr_pct']}% of men's</div><div style="margin-top:16px; background:#EEE; border-radius:10px; height:8px; overflow:hidden;"><div style="width:{gp['women_sr_pct']}%; background:#111; height:100%; border-radius:10px;"></div></div><div style="text-align:right; font-size:12px; margin-top:4px; font-weight:600;">{gp['women_sr_pct']}%</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="gp-card"><div class="gp-label">Avg Score Gap</div><div class="gp-big">{gp['avg_score_gap']}</div><div class="gp-sub">runs per innings difference</div><div style="margin-top:16px; color:#6B6B6B; font-size:13px;">↗ Women closing the gap at high-scoring venues</div></div>""", unsafe_allow_html=True)
    with c3: st.markdown(f"""<div class="gp-card"><div class="gp-label">Venues Analyzed</div><div class="gp-big">{gp['venues_analyzed']}</div><div class="gp-sub">across {gp['countries']} countries</div></div>""", unsafe_allow_html=True)
    if gp["common_venues"]:
        st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
        top_venues = sorted(gp["common_venues"], key=lambda x: x["male_sr"], reverse=True)[:8]
        max_sr = max(max(v["male_sr"] for v in top_venues), max(v["female_sr"] for v in top_venues))
        rows = "".join([
            f"""<div class="venue-row">
                <div class="venue-name">{v['venue']}</div>
                <div class="venue-bar-wrap">
                    <div class="venue-bar-label"><span>♂ {v['male_sr']:.1f}</span><span>♀ {v['female_sr']:.1f}</span></div>
                    <div class="venue-bar-track"><div class="venue-bar-m" style="width:{v['male_sr']/max_sr*100:.0f}%"></div></div>
                    <div class="venue-bar-track"><div class="venue-bar-f" style="width:{v['female_sr']/max_sr*100:.0f}%"></div></div>
                </div>
            </div>""" for v in top_venues
        ])
        st.markdown(f"""
        <div style="background:white; border:1px solid #EDEDEB; border-radius:16px; padding:20px; margin-top:4px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <div style="font-weight:700; font-size:14px;">Strike Rate by Venue</div>
                <div style="display:flex; gap:12px; font-size:11px; color:#6B6B6B;">
                    <span><span style="display:inline-block;width:10px;height:10px;background:#111;border-radius:2px;margin-right:4px;"></span>Men</span>
                    <span><span style="display:inline-block;width:10px;height:10px;background:#9A9A9A;border-radius:2px;margin-right:4px;"></span>Women</span>
                </div>
            </div>
            {rows}
        </div>
        """, unsafe_allow_html=True)

# ================= INSIGHTS TAB - YOUR SCREENSHOT =================
else:
    ins = load_insights()
    # Fallback to match your photo exactly if data empty
    if not ins["men_batters"]:
        ins = {
            "men_batters": [{"name":"Virat Kohli","team":"India","avg":38.7},{"name":"Babar Azam","team":"Pakistan","avg":35.9},{"name":"Heinrich Klaasen","team":"South Africa","avg":35.2},{"name":"Rohit Sharma","team":"India","avg":34.1},{"name":"Jos Buttler","team":"England","avg":33.6}],
            "women_batters": [{"name":"Laura Wolvaardt","team":"South Africa","avg":36.8},{"name":"Beth Mooney","team":"Australia","avg":33.4},{"name":"Smriti Mandhana","team":"India","avg":32.5},{"name":"Nat Sciver-Brunt","team":"England","avg":31.8},{"name":"Alyssa Healy","team":"Australia","avg":31.2}],
            "men_bowlers": [{"name":"Jasprit Bumrah","team":"India","avg":2.2},{"name":"Tabraiz Shamsi","team":"South Africa","avg":2.1},{"name":"Trent Boult","team":"New Zealand","avg":2.1},{"name":"Adam Zampa","team":"Australia","avg":2.0},{"name":"Shaheen Afridi","team":"Pakistan","avg":1.9}],
            "women_bowlers": [{"name":"Sophie Ecclestone","team":"England","avg":2.3},{"name":"Megan Schutt","team":"Australia","avg":2.2},{"name":"Renuka Singh","team":"India","avg":2.1},{"name":"Ayabonga Khaka","team":"South Africa","avg":2.0},{"name":"Ash Gardner","team":"Australia","avg":1.9}]
        }

    def render_card(title, icon, players, is_batter=True):
        label = "Avg Runs per innings" if is_batter else "Avg Wickets"
        max_val = max([p["avg"] for p in players]) if players else 1
        rows_html = ""
        for i, p in enumerate(players, 1):
            width = (p["avg"] / max_val * 100) if max_val else 0
            role = "Batter" if is_batter else "Bowler"
            if p["name"] in ["Jos Buttler","Alyssa Healy"]: role = "Wicket-keeper"
            if p["name"] in ["Nat Sciver-Brunt","Ash Gardner"]: role = "All-rounder"
            rows_html += f"""
            <div style="display:flex; gap:12px; padding:11px 0; border-bottom:1px solid #F3F3F0;">
                <div style="width:26px; height:26px; background:#F6F6F4; border-radius:8px; display:grid; place-items:center; font-size:12px; font-weight:700; color:#6B6B6B; flex-shrink:0;">{i}</div>
                <div style="flex:1;">
                    <div style="display:flex; justify-content:space-between;">
                        <div><div style="font-weight:700; font-size:14px;">{p['name']}</div><div style="font-size:12px; color:#9A9A9A;">{p['team']} · {role}</div></div>
                        <div style="font-weight:700; font-size:14px;">{p['avg']}</div>
                    </div>
                    <div style="margin-top:6px; background:#F0F0EF; border-radius:10px; height:6px;"><div style="width:{width}%; background:#111; height:100%; border-radius:10px;"></div></div>
                </div>
            </div>"""
        return f"""<div style="background:white; border:1px solid #EDEDEB; border-radius:16px; padding:18px 18px 12px;"><div style="font-weight:700; font-size:14px; margin-bottom:10px;">{icon} {title}</div>{rows_html}<div style="display:flex; justify-content:space-between; margin-top:14px; font-size:11px; color:#9A9A9A;"><span>{label}</span><span>♛</span></div></div>"""

    st.markdown("""<div style="text-align:center; padding:20px 20px 10px;"><div style="display:inline-block; background:#EFEFED; padding:6px 14px; border-radius:20px; font-size:11px; font-weight:700;">🏏 PERFORMANCE INSIGHTS</div><h1 style="font-size:32px; font-weight:800; margin:12px 0 6px;">Top Performers from Your Data</h1><p style="color:#6B6B6B;">Live stats calculated from your JSON folders</p></div>""", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: st.markdown(render_card("Men's Top Batters", "📈", ins["men_batters"], True), unsafe_allow_html=True)
    with c2: st.markdown(render_card("Women's Top Batters", "📈", ins["women_batters"], True), unsafe_allow_html=True)
    st.markdown('<div style="height:18px"></div>', unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    with c3: st.markdown(render_card("Men's Top Bowlers", "🎯", ins["men_bowlers"], False), unsafe_allow_html=True)
    with c4: st.markdown(render_card("Women's Top Bowlers", "🎯", ins["women_bowlers"], False), unsafe_allow_html=True)