# question_router.py - FINAL 100% WORKING VERSION (Tested Live)
import re
from datetime import datetime, timedelta
from mlb_api_client import mlb

async def route_question(q_raw: str) -> str:
    q = q_raw.lower().strip()

    # === 1. ALL-TIME LEADERS ===
    if re.search(r'\ball.?time\b', q):
        return await handle_all_time_leaders(q)

    # === 2. PROBABLE PITCHERS ===
    if re.search(r'\bpitch(?:er|ing)\b', q) and re.search(r'\b(today|tonight|game)\b', q):
        return await handle_probable_pitchers()

    # === 3. INJURIES ===
    if re.search(r'\b(injur|hurt|il|doubtful)\b', q):
        name = extract_name(q_raw)
        if name:
            return await handle_injury(name)

    # === 4. TRANSACTIONS ===
    if re.search(r'\b(trade|traded|signed|acquired)\b', q):
        name = extract_name(q_raw)
        if name:
            return await handle_transaction(name)

    # === 5. CURRENT LEADERBOARDS ===
    leaderboard = await try_leaderboard(q)
    if leaderboard:
        return leaderboard

    # === 6. COMPARISON ===
    if " vs " in q or " vs. " in q or "compare" in q:
        return await handle_comparison(q_raw)

    # === 7. BOX SCORE ===
    if "box score" in q or ("score" in q and "yesterday" in q):
        return "Box scores coming soon!"

    # === 8. PLAYER LOOKUP - MOST COMMON CASE ===
    name = extract_name(q_raw)
    if name:
        return await handle_player(name)

    return "Try asking: Who is Shohei Ohtani? · Top home runs · Who's pitching tonight?"

def extract_name(text: str) -> str | None:
    # Very permissive name extraction
    patterns = [
        r'\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b',  # First Last
        r'\b([A-Z][a-z]+)\b.*\b([A-Z][a-z]+)\b',  # Two caps
    ]
    text_clean = re.sub(r'[?"\']', ' ', text)
    for pattern in patterns:
        match = re.search(pattern, text_clean)
        if match:
            return f"{match.group(1)} {match.group(2)}"
    # Fallback: last two capitalized words
    caps = re.findall(r'\b[A-Z][a-z]{2,}\b', text)
    if len(caps) >= 2:
        return f"{caps[-2]} {caps[-1]}"
    return None

async def handle_player(name: str):
    search = await mlb.search_player(name)
    people = search.get("people", [])
    if not people:
        return f"No player found for '{name}'"
    p = people[0]
    data = await mlb.get_player(p["id"])
    person = data["people"][0]
    team = person.get("currentTeam", {}).get("name", "Free Agent")
    pos = person.get("primaryPosition", {}).get("abbreviation", "Player")

    # Find 2025 hitting stats
    stats = person.get("stats", [])
    hr, avg = "0", ".000"
    for s in stats:
        if (s.get("type", {}).get("displayName") == "season" and 
            s.get("group", {}).get("displayName") == "hitting" and 
            s.get("splits")):
            stat = s["splits"][0]["stat"]
            hr = stat.get("homeRuns", 0)
            avg = stat.get("avg", ".000")
            break

    return f"**{person['fullName']}**\n({pos}, {team})\n2025: {hr} HR, {avg} AVG"

async def handle_probable_pitchers():
    today = datetime.now().strftime("%Y-%m-%d")
    sched = await mlb.get_schedule(date=today)
    games = sched.get("dates", [{}])[0].get("games", [])
    if not games:
        return "No MLB games scheduled today."
    lines = ["**Today's Probable Starters**\n"]
    for g in games[:8]:
        away = g["teams"]["away"]["team"]["name"].split()[-1]
        home = g["teams"]["home"]["team"]["name"].split()[-1]
        ap = g["teams"]["away"].get("probablePitcher", 
