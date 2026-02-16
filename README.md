# MLB Chatbot v3 – The Most Advanced Public MLB Bot

The **best open-source MLB chatbot** powered 100% by the official MLB StatsAPI — no paid APIs, no limits.

Ask anything:
- "Who’s pitching tonight?"
- "Is Aaron Judge injured?"
- "When was Juan Soto traded?"
- "All-time home run leaders"
- "Shohei Ohtani vs Aaron Judge"
- "Box score of yesterday’s Yankees game"
- "Top 10 in ERA"

Works for 2025 season, spring training, all-time stats, and more!

**Live Demo**: Coming soon! (Run locally in 30 seconds)

## Features

- Real-time 2025 season stats
- All-time career leaderboards
- Probable pitchers for today
- Injury status (IL or active)
- Trade & transaction history
- Player comparisons
- Box scores
- Leaderboards (HR, AVG, ERA, etc.)
- Natural language understanding
- Beautiful web interface
- No API key required

## Quick Start

```bash
git clone https://github.com/robmllb/mlb-chatbot.git
cd mlb-chatbot
pip install -r requirements.txt
uvicorn main:app --reload
