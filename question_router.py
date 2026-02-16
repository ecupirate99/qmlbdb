# question_router.py - FIXED VERSION (No More Freddie Freeman Spam!)
import re
from datetime import datetime, timedelta
from mlb_api_client import mlb

async def route_question(q_raw: str) -> str:
    q = q_raw.lower()

    # === ALL-TIME LEADERS ===
    if any(x in q for x in ["all.time", "all time", "career leaders", "all-time"]):
        return await handle_all_time_leaders(q)

    # === PROBABLE PITCHERS ===
    if any(p in q for p in ["pitching", "pitcher", "starter", "probable"]) and any(t in q for t in ["today", "tonight", "game"]):
        return await handle_probable_pitchers()

    # === INJURIES ===
    if any(w in q for w in ["injured", "il", "injury", "hurt", "doubtful"]):
        name = extract_player_name(q_raw)
        if name:
            return await handle_injury_status(name)

    # === TRANSACTIONS ===
    if any(w in q for w in ["traded", "signed", "trade", "acquired"]):
        name = extract_player_name(q_raw)
        if name:
            return await handle_transactions(name)

    # === CURRENT LEADERBOARDS ===
    if any(x in q for x in ["lead", "top ", "most ", "best ", "home run", "hr ", "average", "era", "strikeout"]):
        resp = await handle_current_leaderboard(q)
        if resp:
            return resp

    # === COMPARISON ===
    if " vs " in q or " vs. " in q or "compare" in q:
        return await handle_comparison(q_raw)

    # === BOX SCORE ===
    if "box score" in q or ("score" in q and any(d in q for d in ["yesterday", "last night"])):
        return await handle_box_score()

    # === PLAYER LOOKUP (Only if clear name) ===
    name = extract_player_name(q_raw)
    if name and len(name.split()) >= 2:
        return await handle_player_lookup(name)

    return "Ask me about players, injuries, trades, pitchers, leaderboards, or matchups!"

def extract_player_name(text: str) -> str | None:
    # Look for capitalized first + last name
    match = re.search(r'\b([A-Z][a-z]+(?:-[A-Z][a-z]+)?)\s+([A-Z][a-z]+(?:-[A-Z][a-z]+)?)\b', text)
    if match:
        return f"{match.group(1)} {match.group(2)}"
    return None

async def handle_player_lookup(name: str):
    search = await mlb.search_player(name)
    people = search.get("people", [])
    if not people:
        return f"Couldn't find player: {name}"
    p = people[0]
    data = await mlb.get_player(p["id"])
    person = data["people"][0]
    team = person.get("currentTeam", {}).get("name", "Free Agent")
    pos = person.get("primaryPosition", {}).get("abbreviation", "?")
    
    stats_list = person.get("stats", [])
    hitting_stats = None
    for s in stats_list:
        if s.get("type", {}).get("displayName") == "season" and s.get("group", {}).get("displayName") == "hitting":
            splits = s.get("splits")
            if splits:
                hitting_stats = splits[0]["stat"]
                break
    
    if hitting_stats:
        hr = hitting_stats.get("homeRuns", 0)
        avg = hitting_stats.get("avg", ".000")
        return f"**{person['fullName']}** ({pos}, {team})\n2025: {hr} HR, {avg} AVG"
    else:
        return f"**{person['fullName']}** ({pos}, {team})\nNo 2025 stats yet"

async def handle_probable_pitchers():
    today = datetime.now().strftime("%Y-%m-%d")
    data = await mlb.get_schedule(date=today)
    games = data.get("dates", [{}])[0].get("games", [])
    if not games:
        return "No games scheduled today."
    lines = ["**Today's Probable Pitchers**\n"]
    for g in games[:10]:
        away = g["teams"]["away"]["team"]["name"].split()[-1]
        home = g["teams"]["home"]["team"]["name"].split()[-1]
        ap = g["teams"]["away"].get("probablePitcher", {}).get("fullName", "TBD")
        hp = g["teams"]["home"].get("probablePitcher", {}).get("fullName", "TBD")
        lines.append(f"• {away} @ {home}: {ap} vs {hp}")
    return "\n".join(lines)

async def handle_injury_status(name: str):
    search = await mlb.search_player(name)
    if not search.get("people"): return "Player not found."
    p = search["people"][0]
    data = await mlb.get_player(p["id"])
    person = data["people"][0]
    injuries = person.get("injuries", [])
    status = person.get("status", {}).get("description", "Active")
    if injuries:
        injury = injuries[-1]
        desc = injury.get("description") or "Injured"
        return f"**{person['fullName']}** – {desc} ({status})"
    return f"**{person['fullName']}** – Active ({status})"

async def handle_transactions(name: str):
    search = await mlb.search_player(name)
    if not search.get("people"): return "Player not found."
    p = search["people"][0]
    data = await mlb.get_player(p["id"])
    txns = data["people"][0].get("transactions", [])
    if not txns:
        return f"No recent transactions for {name}."
    recent = txns[-1]
    desc = recent.get("description", "Transaction")
    date = recent.get("date", "")[:10]
    return f"**{name}**: {desc} ({date})"

async def handle_current_leaderboard(q: str):
    stat_map = {
        "home run": "homeRuns", "hr": "homeRuns",
        "average": "battingAverage", "avg": "battingAverage",
        "rbi": "rbi", "hit": "hits",
        "era": "era", "strikeout": "strikeOuts", "win": "wins"
    }
    for phrase, code in stat_map.items():
        if phrase in q:
            group = "pitching" if code in ["era", "strikeOuts", "wins"] else "hitting"
            data = await mlb.get_leaderboard(code, group=group, limit=8)
            leaders = data.get("leagueLeaders", [{}])[0].get("leaders", [])
            title = code.replace("battingAverage", "AVG").replace("homeRuns", "HR").upper()
            lines = [f"**2025 {title} Leaders**\n"]
            for i, l in enumerate(leaders, 1):
                name = l["person"]["fullName"]
                team = l["team"]["name"].split()[-1]
                val = l["value"]
                if code == "battingAverage":
                    val = f".{int(float(val)*1000)}"
                elif code == "era":
                    val = f"{val:.2f}"
                lines.append(f"{i}. {name} ({team}) – {val}")
            return "\n".join(lines)
    return None

async def handle_all_time_leaders(q: str):
    stat_map = {
        "home run": "homeRuns", "strikeout": "strikeOuts", "hit": "hits", "win": "wins"
    }
    for phrase, code in stat_map.items():
        if phrase in q:
            group = "pitching" if "strikeout" in phrase or "win" in phrase else "hitting"
            data = await mlb.get_leaderboard(code, season=False, group=group, limit=8)
            leaders = data.get("leagueLeaders", [{}])[0].get("leaders", [])
            title = f"All-Time {code.replace('homeRuns', 'HR').replace('strikeOuts', 'K').upper()}"
            lines = [f"**{title}**\n"]
            for i, l in enumerate(leaders, 1):
                name = l["person"]["fullName"]
                val = l["value"]
                lines.append(f"{i}. {name} – {val}")
            return "\n".join(lines)
    return "Try: all-time home run leaders"

async def handle_comparison(q: str):
    players = re.findall(r"[A-Z][a-z]+ [A-Z][a-z]+", q)
    if len(players) < 2:
        return "Please name two players."
    p1, p2 = players[:2]
    # Simplified — just acknowledge
    return f"Comparing **{p1}** vs **{p2}** in 2025...\n(Full stats coming soon!)"

async def handle_box_score():
    return "Box scores for recent games are loading..."
