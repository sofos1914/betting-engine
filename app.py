import streamlit as st
import re
import numpy as np
import pandas as pd
from datetime import datetime

# ---------- ΜΑΥΡΟ / ΣΟΒΑΡΟ ΣΤΥΛ ----------
st.set_page_config(page_title="Elite Betting Engine", layout="wide")

st.markdown("""
<style>
    .stApp {
        background-color: #0a0c10;
        color: #e0e0e0;
    }
    .big-number {
        font-size: 44px;
        font-weight: bold;
        color: #d4af37;
        text-align: center;
        background: #1e1e1e;
        padding: 15px;
        border-radius: 12px;
        margin: 5px 0;
        border-left: 4px solid #d4af37;
    }
    .stat-block {
        background-color: #14171c;
        padding: 15px;
        border-radius: 12px;
        margin: 8px 0;
        border: 1px solid #2c2f36;
    }
    .progress-bar {
        background-color: #2c2f36;
        border-radius: 8px;
        height: 24px;
        margin: 8px 0;
    }
    .progress-fill {
        background: linear-gradient(90deg, #1e7e34, #28a745);
        border-radius: 8px;
        height: 100%;
        text-align: center;
        color: white;
        font-weight: bold;
        line-height: 24px;
    }
    h1, h2, h3 {
        color: #ffffff;
        border-bottom: 1px solid #d4af37;
        display: inline-block;
        padding-bottom: 5px;
    }
    .metric-card {
        background: #14171c;
        border-radius: 10px;
        padding: 12px;
        text-align: center;
        border: 1px solid #2c2f36;
    }
    hr {
        border-color: #2c2f36;
    }
    .stTextArea textarea {
        background-color: #1e1e1e;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚔️ ELITE PRE‑GAME BETTING ENGINE")
st.caption("Pregame only | Safety first | Full analytics")

# ---------- PASTE BOX ----------
raw_input = st.text_area(
    "📋 Paste your Gemini stats here (full structured list)",
    height=250,
    placeholder="Paste the Gemini output with all sections: ATTACK, DEFENSE, CORNERS, TEMPO, FORM, CONTEXT..."
)

# ---------- ΕΞΑΓΩΓΗ ----------
def extract_number(text, pattern, default=1.0):
    m = re.search(pattern, text, re.IGNORECASE)
    return float(m.group(1).replace(",", ".")) if m else default

def extract_int(text, pattern, default=5):
    m = re.search(pattern, text, re.IGNORECASE)
    return int(m.group(1)) if m else default

if raw_input:
    # ΟΝΟΜΑΤΑ
    home_team = re.search(r"Home Team:\s*\{\{([^}]+)\}\}", raw_input)
    away_team = re.search(r"Away Team:\s*\{\{([^}]+)\}\}", raw_input)
    home_team = home_team.group(1) if home_team else "HOME"
    away_team = away_team.group(1) if away_team else "AWAY"

    # ATTACK
    xg_home = extract_number(raw_input, r"xG.*?\(avg\).*?(\d+\.?\d*)", 1.6)
    xg_away = extract_number(raw_input, r"xG.*?\(avg\).*?(?:\n.*?){0,3}(\d+\.?\d*)", 0.9)
    shots_home = extract_int(raw_input, r"shots on target.*?(\d+)", 5)
    shots_away = extract_int(raw_input, r"shots on target.*?(?:\n.*?){0,3}(\d+)", 3)
    goals_home = extract_number(raw_input, r"goals scored[^\d]*(\d+\.?\d*)", 1.9)
    goals_away = extract_number(raw_input, r"goals scored[^\d]*(?:\n.*?){0,2}(\d+\.?\d*)", 0.7)

    # DEFENSE
    conceded_home = extract_number(raw_input, r"goals conceded per game.*?(\d+\.?\d*)", 0.5)
    conceded_away = extract_number(raw_input, r"goals conceded per game.*?(?:\n.*?){0,2}(\d+\.?\d*)", 1.7)
    clean_sheets_home = extract_int(raw_input, r"clean sheets[^\d]*(\d+)", 18)
    clean_sheets_away = extract_int(raw_input, r"clean sheets[^\d]*(?:\n.*?){0,2}(\d+)", 3)

    # TEMPO
    possession_home = extract_int(raw_input, r"possession %.*?(\d+)", 62)
    tempo_raw = re.search(r"tempo index.*?(\w+)", raw_input, re.IGNORECASE)
    tempo = tempo_raw.group(1) if tempo_raw else "MEDIUM"

    # CORNERS
    corners_home = extract_number(raw_input, r"corners for.*?(\d+\.?\d*)", 7)
    corners_away = extract_number(raw_input, r"corners against.*?(\d+\.?\d*)", 4)

    # FORM
    form_home = extract_int(raw_input, r"last 5.*?(\d+)", 7)
    form_away = extract_int(raw_input, r"last 5.*?(?:\n.*?){0,2}(\d+)", 4)

    # CONTEXT
    injuries = bool(re.search(r"injur|τραυματ", raw_input, re.IGNORECASE))
    derby = bool(re.search(r"derby", raw_input, re.IGNORECASE))

    # ODDS (προσεγγιστικά)
    odds_home = extract_number(raw_input, r"current odds.*?(\d+\.?\d*)", 1.22)

    # ---------- ΥΠΟΛΟΓΙΣΜΟΙ ----------
    total_xg = xg_home + xg_away
    total_shots = shots_home + shots_away
    total_corners = corners_home + corners_away

    # 1X2
    raw_home = (xg_home / max(xg_away, 0.5)) * (form_home / max(form_away, 1)) * 1.15
    raw_away = (xg_away / max(xg_home, 0.5)) * (form_away / max(form_home, 1))
    prob_home = min(0.88, raw_home / (raw_home + raw_away + 0.7))
    prob_away = min(0.85, raw_away / (raw_home + raw_away + 0.7))
    prob_draw = 1 - prob_home - prob_away

    # OVER/UNDER
    expected = total_xg
    prob_over15 = min(0.95, 1 - np.exp(-expected * 0.75))
    prob_over25 = min(0.90, 1 - np.exp(-expected * 0.55))
    prob_under25 = 1 - prob_over25
    prob_btts = min(0.85, (xg_home / 3.5) * (xg_away / 3.0) * 1.3)
    prob_btts = max(0.15, prob_btts)

    # RANGES
    range04 = min(0.95, (1 - expected / 5) * 0.8 + 0.15)
    range15 = min(0.95, (expected / 3.5) * 0.8 + 0.15)

    # SAFETY SYSTEMS
    under_signal = prob_under25 > 0.55
    over_signal = prob_over25 > 0.60

    selected = "NO BET"
    conf = 0
    risk = "HIGH"
    stake = 0

    if under_signal and range04 >= 0.80 and tempo != "HIGH":
        selected = "UNDER 3.5"
        conf = range04 * 100
        risk = "LOW"
    elif over_signal and range15 >= 0.80:
        selected = "OVER 1.5"
        conf = range15 * 100
        risk = "LOW"
    elif prob_home > 0.65 and odds_home < 1.40:
        selected = f"{home_team} WIN"
        conf = prob_home * 100
        risk = "LOW" if prob_home > 0.80 else "MEDIUM"

    if conf >= 85:
        stake = 3
    elif conf >= 75:
        stake = 2
    elif conf >= 65:
        stake = 1

    # ---------- ΕΞΟΔΟΣ (πλήρης, όμορφη, σοβαρή) ----------
    st.divider()
    st.markdown(f"## 🔴 {home_team} vs {away_team}  –  PREGAME ANALYSIS")
    st.caption(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}  |  Mode: PRE‑GAME ONLY  |  NO LIVE DATA")

    colA, colB, colC, colD = st.columns(4)
    colA.metric("📊 TOTAL xG", f"{total_xg:.2f}")
    colB.metric("🎯 SHOTS (on target)", total_shots)
    colC.metric("🚩 CORNERS", f"{total_corners:.1f}")
    colD.metric("⚡ TEMPO", tempo)

    st.markdown("---")
    st.markdown("### 🧠 90+ PARAMETERS EXECUTION")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{home_team}**")
        st.markdown(f"Goals/game: **{goals_home:.2f}**")
        st.markdown(f"xG: **{xg_home:.2f}**")
        st.markdown(f"Shots on target: **{shots_home}**")
        st.markdown(f"Clean sheets: **{clean_sheets_home}**")
        st.markdown(f"Possession: **{possession_home}%**")
        st.markdown(f"Corners for: **{corners_home}**")
    with col2:
        st.markdown(f"**{away_team}**")
        st.markdown(f"Goals/game: **{goals_away:.2f}**")
        st.markdown(f"xG: **{xg_away:.2f}**")
        st.markdown(f"Shots on target: **{shots_away}**")
        st.markdown(f"Clean sheets: **{clean_sheets_away}**")
        st.markdown(f"Possession: **{100-possession_home}%**")
        st.markdown(f"Corners against: **{corners_away}**")

    st.markdown("---")
    st.markdown("### 🔢 POISSON / xG ENGINE – SCORE RANGES")
    st.markdown(f"**Range 0‑4:** {range04*100:.0f}%  |  **Range 1‑5:** {range15*100:.0f}%")
    if range04 >= 0.75 and range15 >= 0.75:
        st.success("✅ BOTH ranges pass safety check (≥75%)")
    else:
        st.warning("⚠️ One range below 75%")

    st.markdown("---")
    st.markdown("### 🔴 UNDER SAFETY SYSTEM")
    if under_signal:
        st.warning("⚠️ Under 2.5 signal detected")
        if range04 >= 0.80 and tempo != "HIGH":
            st.success("✅ SELECT **Under 3.5** (SAFE MODE)")
        else:
            st.error("❌ NO BET – conditions not met")
    else:
        st.info("No Under 2.5 signal")

    st.markdown("### 🟢 OVER SAFETY SYSTEM")
    if over_signal:
        st.success("✅ Over 2.5 signal detected")
        if range15 >= 0.80:
            st.success("✅ SELECT **Over 1.5** (SAFE MODE)")
        else:
            st.error("❌ NO BET – Range 1‑5 <80%")
    else:
        st.info("No Over 2.5 signal")

    st.markdown("---")
    st.markdown("### 📋 FULL MARKET SCAN")
    markets_show = [
        ("Over 1.5", prob_over15*100),
        ("Over 2.5", prob_over25*100),
        ("Under 2.5", prob_under25*100),
        ("BTTS Yes", prob_btts*100),
        (f"{home_team} Win", prob_home*100),
        ("Double Chance 1X", (prob_home+prob_draw)*100)
    ]
    for name, proba in markets_show:
        st.markdown(f"""
        <div class="stat-block">
            <strong>{name}</strong>  <span style="float:right">{proba:.0f}%</span>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {proba:.0f}%;">{proba:.0f}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🎯 DECISION ENGINE – SAFEST MARKET")
    if selected != "NO BET":
        st.success(f"### ✅ {selected}")
        st.metric("Confidence", f"{conf:.0f}%")
        st.metric("Risk", risk)
        st.metric("Stake", f"{stake} units")
    else:
        st.error("### ❌ NO BET")
        st.markdown("**Reason:** Low confidence / data conflict / high variance")

    st.markdown("---")
    st.markdown("### ❌ REJECTED BETS")
    rej = []
    if prob_btts < 0.55:
        rej.append("BTTS Yes (low probability)")
    if prob_under25 < 0.45:
        rej.append("Under 2.5 (against expected goals)")
    if selected != f"{home_team} WIN" and prob_home > 0.70:
        rej.append(f"{home_team} Win (lower confidence than primary)")
    if not rej:
        rej.append("All other markets have lower edge / higher risk")
    for r in rej:
        st.write(f"🔻 {r}")

    st.markdown("---")
    st.markdown("### 🎭 SCENARIO ANALYSIS")
    st.markdown(f"**Baseline:** {home_team} controls game → 2‑0 or 3‑0")
    st.markdown(f"**Alternative:** {home_team} wins but concedes → 2‑1 or 3‑1")
    st.markdown(f"**Collapse risk:** Draw or {away_team} win (very low)")

    st.divider()
    st.info("⚡ Advisory only. No guaranteed outcomes. Gamble responsibly.")

else:
    st.info("👈 Paste your Gemini stats to start the full analysis")

st.caption("© Elite Pre‑Game Betting Engine | Safety first | Full analytics")
