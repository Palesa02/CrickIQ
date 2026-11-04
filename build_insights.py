import json, os, glob, pickle
from collections import defaultdict

# player -> stats
players = defaultdict(lambda: {"runs":0, "innings":0, "balls":0, "wickets":0, "matches":set(), "gender":"male", "teams":set()})

folders = {
    "tests_male_json": "male",
    "tests_female_json": "female", 
    "odis_json": "male",
    "t20s_json": "male",
    "t20s_female_json": "female"
}

for folder, gender in folders.items():
    if not os.path.exists(folder): continue
    for file in glob.glob(os.path.join(folder, "*.json")):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                match_id = os.path.basename(file)
                for inn in data.get('innings', []):
                    team = inn.get('team', 'Unknown')
                    overs = inn.get('overs', [])
                    for over in overs:
                        for delivery in over.get('deliveries', []):
                            batter = delivery.get('batter')
                            bowler = delivery.get('bowler')
                            runs = delivery.get('runs',{}).get('batter',0)
                            # track batters
                            if batter:
                                players[batter]["runs"] += runs
                                players[batter]["balls"] += 1
                                players[batter]["teams"].add(team)
                                players[batter]["gender"] = gender
                                players[batter]["matches"].add(match_id)
                            if bowler:
                                players[bowler]["teams"].add(team)
                                players[bowler]["gender"] = gender
                                players[bowler]["matches"].add(match_id)
                            # wickets for bowler
                            for w in delivery.get('wickets', []):
                                kind = w.get('kind','')
                                if kind not in ['run out','retired hurt','obstructing the field']:
                                    if bowler:
                                        players[bowler]["wickets"] += 1
                        # count innings for batters in this over
                    # count unique batters per innings as an innings
                    batters_in_inn = set()
                    for over in overs:
                        for d in over.get('deliveries', []):
                            if d.get('batter'):
                                batters_in_inn.add(d.get('batter'))
                    for b in batters_in_inn:
                        players[b]["innings"] += 1
        except: continue

# Build ranking lists
def get_top_batters(gender, limit=5):
    cands = []
    for name, s in players.items():
        if s["gender"] != gender: continue
        if s["innings"] < 5: continue
        if s["runs"] < 100: continue
        avg = s["runs"] / max(1, s["innings"])
        cands.append({"name":name, "avg":round(avg,1), "runs":s["runs"], "innings":s["innings"], "team": list(s["teams"])[0] if s["teams"] else "Unknown"})
    return sorted(cands, key=lambda x: x["avg"], reverse=True)[:limit]

def get_top_bowlers(gender, limit=5):
    cands = []
    for name, s in players.items():
        if s["gender"] != gender: continue
        if s["wickets"] < 5: continue
        avg_wkts = s["wickets"] / max(1, len(s["matches"]))
        cands.append({"name":name, "avg":round(avg_wkts,1), "wickets":s["wickets"], "team": list(s["teams"])[0] if s["teams"] else "Unknown"})
    return sorted(cands, key=lambda x: x["wickets"], reverse=True)[:limit]

insights = {
    "men_batters": get_top_batters("male"),
    "women_batters": get_top_batters("female"),
    "men_bowlers": get_top_bowlers("male"),
    "women_bowlers": get_top_bowlers("female"),
}

with open('insights.pkl','wb') as f:
    pickle.dump(insights, f)

print("Insights built!")
print("Men Batters:", insights["men_batters"][:3])
print("Women Batters:", insights["women_batters"][:3])