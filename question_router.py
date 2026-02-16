# question_router.py
import re
from datetime import datetime, timedelta
from mlb_api_client import mlb

async def route_question(q_raw: str) -> str:
    q = q_raw.lower().strip()

    # === NEW: Probable Pitchers ===
    if any(p in q for p in ["pitching", "pitcher", "starter", "probable"]) and ("tonight" in q or "today" in q or "game" in q):
        return await handle_probable_pitchers()

    # === NEW: Injuries ===
    if "injured" in q or "il" in q or "injury" in q or "hurt" in q:
        name = extract_player_name(q_raw)
        if name:
            return await handle_injury_status(name)
        return "Who are you asking about?"

    # === NEW: Transactions / Trades ===
    if any(t in q for t in ["traded", "signed", "trade", "acquired", "transaction"]):
        name = extract_player_name(q_raw)
        if name:
            return await handle_transactions(name)

    # === NEW: All-Time Leaders ===
    if "all.time" in q or "all time" in q or "career leaders" in q:
        return await handle_all_time_leaders(q)

    # Leaderboards (current season)
    if any(x in q for x in ["lead", "top ", "most ", "best "]):
        resp = await handle_leaderboard(q)
        if resp: return resp

    if " vs " in q or "compare" in q:
        return await handle_comparison(q_raw)

    if "box score" in q or ("score" in q and any(d in q for d in ["yesterday", "last night", "final"])):
        return await handle_box_score()

    name = extract_player_name(q_raw)
    if name:
        return await handle_player(name, q_raw)

    if "standing" in q:
        return await handle_standings()

    return "I can help with players, stats, injuries, trades, pitchers, and more! Try asking about Shohei Ohtani or today's matchups."

def extract_player_name(text: str):
    pattern = r"(?:who.*?|about)?\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)"
    match = re.search(pattern, text, re.I)
    return match.group(1) if match else None

async def handle_probable_pitchers():
    today = datetime.now().strftime("%Y-%m-%d")
    data = await mlb.get_schedule(date=today)
    games = data.get("dates", [{}])[0].get("games", [])
    lines = ["**Today's Probable Pitchers**\n"]
    for g in games[:12]:
        away = g["teams"]["away"]["team"]["name"].split()[-1]
        home = g["teams"]["home"]["team"]["name"].split()[-1]
        a_pitcher = g["teams"]["away"].get("probablePitcher", {}).get("fullName", "TBD")
        h_pitcher = g["teams"]["home"].get("probablePitcher", {}).get("fullName", "TBD")
        lines.append(f"{away} @ {home}: {a_pitcher} vs {h_pitcher}")
    return "\n".join(lines) if len(lines) > 1 else "No games scheduled today."

async def handle_injury_status(name: str):
    search = await mlb.search_player(name)
    people = search.get("people", [])
    if not people:
        return f"Couldn't find {name}"
    p = people[0]
    data = await mlb.get_player(p["id"])
    person = data["people"][0]
    injuries = person.get("injuries", [])
    status = person.get("status", {}).get("description", "Active")
    if injuries:
        latest = injuries[-1]
        desc = latest.get("description", "Injured")
        return f"**{person['fullName']}** – {desc} ({status})"
    return f"**{person['fullName']}** – Active ({status})"

async def handle_transactions(name: str):
    search = await mlb.search_player(name)
    if not search.get("people"): return "Player not found"
    p = search["people"][0]
    data = await mlb.get_player(p["id"])
    txns = data["people"][0].get("transactions", [])
    if not txns:
        return f"No recent transactions for {name}"
    recent = txns[-1]
    desc = recent.get("description", "Transaction")
    date = recent.get("date", "")[:10]
    return f"**{name}**: {desc} ({date})"

async def handle_all_time_leaders(q: str):
    stat_map = {
        "home run": "homeRuns", "hr": "homeRuns",
        "hit": "hits", "strikeout": "strikeOuts", "win": "wins",
        "rbi": "rbi", "average": "battingAverage"
    }
    for phrase, stat in stat_map.items():
        if phrase in q:
            group = "pitching" if stat in ["strikeOuts", "wins"] else "hitting"
            data = await mlb.get_leaderboard(stat, season=False, group=group, limit=10)
            leaders = data.get("leagueLeaders", [{}])[0].get("leaders", [])
            lines = [f"**All-Time {stat.replace('battingAverage', 'AVG').upper()} Leaders**\n"]
            for i, l in enumerate(leaders[:8], 1):
                name = l["person"]["fullName"]
                val = l["value"]
                if stat == "battingAverage":
                    val = f".{int(float(val)*1000)}"
                lines.append(f"{i}. {name} – {val}")
            return "\n".join(lines)
    return "Try asking for all-time home run or strikeout leaders!"

async def handle_leaderboard(q: str):
    stat_map = {
        "home run": "homeRuns", "hr": "homeRuns", "homer": "homeRuns",
        "average": "battingAverage", "avg": "battingAverage",
        "rbi": "rbi", "hit": "hits", "strikeout": "strikeOuts", "era": "era", "win": "wins"
    }
    for phrase, stat in stat_map.items():
        if phrase in q:
            group = "pitching" if stat in ["era", "strikeOuts", "wins"] else "hitting"
            data = await mlb.get_leaderboard(stat, group=group)
            leaders = data.get("leagueLeaders", [{}])[0].get("leaders", [])
            lines = [f"**2025 {stat.replace('battingAverage', 'AVG').upper()} Leaders**\n"]
            for i, l in enumerate(leaders[:10], 1):
                name = l["person"]["fullName"]
                team = l["team"]["name"].split()[-1]
                val = l["value"]
                if stat == "battingAverage":
                    val = f".{int(float(val)*1000)}"
                elif stat == "era":
                    val = f"{val:.2f}"
                lines.append(f"{i}. {name} ({team}) – {val}")
            return "\n".join(lines)
    return None

async def handle_comparison(q: str):
    players = re.findall(r"[A-Z][a-z]+ [A-Z][a-z]+", q)
    if len(players) < 2: return "Name two players to compare."
    p1, p2 = players[0], players[1]
    s1 = await mlb.search_player(p1)
    s2 = await mlb.search_player(p2)
    if not s1.get("people") or not s2.get("people"):
        return "Couldn't find one of the players."
    id1, id2 = s1["people"][0]["id"], s2["people"][0]["id"]
    d1 = await mlb.get_player_stats(id1)
    d2 = await mlb.get_player_stats(id2)
    def get(stat): 
        try:
            return d1["people"][0]["stats"][0]["splits"][0]["stat"].get(stat, "0")
        except:
            return "0"
    def get2(stat):
        try:
            return d2["people"][0]["stats"][0]["splits"][0]["stat"].get(stat, "0")
        except:
            return "0"
    return f"**2025 Stats**\n{p1}: {get('homeRuns')} HR, {get('avg')} AVG\n{p2}: {get2('homeRuns')} HR, {get2('avg')} AVG"

async def handle_player(name: str, original: str):
    search = await mlb.search_player(name)
    if not search.get("people"): return "Player not found"
    p = search["people"][0]
    data = await mlb.get_player(p["id"])
    person = data["people"][0]
    team = person.get("currentTeam", {}).get("name", "Free Agent")
    pos = person.get("primaryPosition", {}).get("abbreviation", "?")
    stats = person.get("stats", [])
    hitting = next((s for s in stats if s["type"]["displayName"] == "season" and s["group"]["displayName"] == "hitting"), None)
    hr = hitting["splits"][0]["stat"]["homeRuns"] if hitting and hitting["splits"] else "0"
    avg = hitting["splits"][0]["stat"]["avg"] if hitting and hitting["splits"] else ".000"
    return f"**{person['fullName']}** ({pos}, {team})\n2025: {hr} HR, {avg} AVG"

async def handle_standings():
    return "**2025 Standings available** – Ask for AL East, NL West, etc."

async def handle_box_score():
    yesterday = (datetime.now() - timedelta(1)).strftime("%Y-%m-%d")
    data = await mlb.get_schedule(date=yesterday)
    games = data.get("dates", [{}])[0].get("games", [])
    if not games: return "No games yesterday."
    g = games[0]
    box = await mlb.get_game_boxscore(g["gamePk"])
    away = box["teams"]["away"]["team"]["name"]
    home = box["teams"]["home"]["team"]["name"]
    a_r = box["teams"]["away"]["teamStats"]["batting"]["runs"]
    h_r = box["teams"]["home"]["teamStats"]["batting"]["runs"]
    return f"**{away} {a_r} – {home} {h_r}** (Final, yesterday)"
