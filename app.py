import streamlit as st
import re
import numpy as np
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Elite Pre-Game Betting Engine", layout="wide")

# ========== CUSTOM CSS FOR FANCY LOOK ==========
st.markdown("""
<style>
.big-number {
    font-size: 48px;
    font-weight: bold;
    text-align: center;
    background: linear-gradient(90deg, #1e3c72, #2a5298);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    padding: 10px;
}
.stat-card {
    background-color: #f0f2f6;
    border-radius: 15px;
    padding: 20px;
    text-align: center;
    box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    margin: 10px 0;
}
.progress-bar-container {
    background-color: #e0e0e0;
    border-radius: 10px;
    height: 25px;
    margin: 10px 0;
}
.progress-bar-fill {
    background: linear-gradient(90deg, #00c853, #69f0ae);
    border-radius: 10px;
    height: 100%;
    text-align: center;
    color: white;
    font-weight: bold;
    line-height: 25px;
}
.market-row {
    margin: 15px 0;
    padding: 10px;
    background-color: #ffffff;
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

st.title("🛡️ ELITE PRE-GAME BETTING ANALYTICS ENGINE")
st.markdown("**Paste stats from Gemini → Full analysis with Safety Systems → Decision**")

# ---------- ΚΟΥΤΙ ΓΙΑ PASTE ----------
st.markdown("### 📋 Paste your Gemini stats here")
raw_input = st.text_area(
    "Copy-paste ολόκληρη τη λίστα στατιστικών:",
    height=300,
    placeholder="Paste the Gemini output here..."
)

# ---------- ΕΞΑΓΩΓΗ ΣΤΑΤΙΣΤΙΚΩΝ (ίδια) ----------
def extract_number(text, pattern, default=1.0):
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1).replace(",", "."))
        except:
            return default
    return default

def extract_int(text, pattern, default=10):
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        try:
            return int(match.group(1))
        except:
            return default
    return default

if raw_input:
    home_match = re.search(r"Home Team:\s*\{\{([^}]+)\}\}", raw_input)
    away_match = re.search(r"Away Team:\s*\{\{([^}]+)\}\}", raw_input)
    home_team = home_match.group(1) if home_match else "HOME"
    away_team = away_match.group(1) if away_match else "AWAY"
    
    xg_home = extract_number(raw_input, r"xG \(avg\):\s*(\d+\.?\d*)", 1.5)
    xg_away = extract_number(raw_input, r"xG \(avg\):.*?(?:\n|.*?)(\d+\.?\d*)", 1.0)
    shots_home = extract_int(raw_input, r"shots on target \(avg\):\s*(\d+)", 5)
    shots_away = extract_int(raw_input, r"shots on target \(avg\):.*?(?:\n|.*?)(\d+)", 3)
    goals_home = extract_number(raw_input, r"goals scored:.*?(\d+\.?\d*)", 1.8)
    goals_away = extract_number(raw_input, r"goals scored:.*?(?:\n|.*?)(\d+\.?\d*)", 0.8)
    conceded_home = extract_number(raw_input, r"goals conceded per game:\s*(\d+\.?\d*)", 0.6)
    conceded_away = extract_number(raw_input, r"goals conceded per game:.*?(?:\n|.*?)(\d+\.?\d*)", 1.6)
    clean_sheet_home = extract_int(raw_input, r"clean sheets:\s*(\d+)", 15)
    clean_sheet_away = extract_int(raw_input, r"clean sheets:.*?(?:\n|.*?)(\d+)", 3)
    possession_home = extract_int(raw_input, r"possession %:\s*(\d+)", 60)
    tempo_raw = re.search(r"tempo index:\s*(\w+)", raw_input, re.IGNORECASE)
    tempo = tempo_raw.group(1) if tempo_raw else "MEDIUM"
    corners_home = extract_number(raw_input, r"corners for \(avg\):\s*(\d+\.?\d*)", 6)
    corners_away = extract_number(raw_input, r"corners against \(avg\):.*?(?:\n|.*?)(\d+\.?\d*)", 5)
    form_home = extract_int(raw_input, r"last 5.*?(\d+)", 7)
    form_away = extract_int(raw_input, r"last 5.*?(?:\n|.*?)(\d+)", 4)
    injuries = "τραυματ" in raw_input.lower() or "injur" in raw_input.lower()
    derby = "derby" in raw_input.lower()
    odds_home = extract_number(raw_input, r"current odds:.*?(\d+\.?\d*)", 1.25)
    odds_draw = extract_number(raw_input, r"current odds:.*?(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)", 6.0)
    if isinstance(odds_draw, tuple):
        odds_draw = odds_draw[1] if odds_draw[1] else 6.0
    odds_over25 = extract_number(raw_input, r"over/under line & odds:.*?(\d+\.?\d*)", 1.65)
    
    total_xg = xg_home + xg_away
    total_shots = shots_home + shots_away
    total_corners = corners_home + corners_away
    
    def calc_prob():
        raw_home = (xg_home / max(xg_away, 0.5)) * (form_home / max(form_away, 1)) * 1.15
        raw_away = (xg_away / max(xg_home, 0.5)) * (form_away / max(form_home, 1))
        prob_home = min(0.88, raw_home / (raw_home + raw_away + 0.7))
        prob_away = min(0.85, raw_away / (raw_home + raw_away + 0.7))
        prob_draw = 1 - prob_home - prob_away
        return prob_home, prob_draw, prob_away
    
    prob_home, prob_draw, prob_away = calc_prob()
    expected_goals = total_xg
    prob_over15 = min(0.95, 1 - np.exp(-expected_goals * 0.75))
    prob_over25 = min(0.90, 1 - np.exp(-expected_goals * 0.55))
    prob_under25 = 1 - prob_over25
    prob_btts = min(0.85, (xg_home / 3.5) * (xg_away / 3.0) * 1.3)
    prob_btts = max(0.15, min(0.85, prob_btts))
    range_04_prob = min(0.95, (1 - expected_goals / 5) * 0.8 + 0.15)
    range_15_prob = min(0.95, (expected_goals / 3.5) * 0.8 + 0.15)
    
    under_signal = (prob_under25 > 0.55)
    over_signal = (prob_over25 > 0.60)
    
    selected_bet = "NO BET"
    confidence = 0
    risk = "HIGH"
    stake = 0
    
    if under_signal and range_04_prob >= 0.80 and tempo != "HIGH":
        selected_bet = "UNDER 3.5"
        confidence = range_04_prob * 100
        risk = "LOW"
    elif over_signal and range_15_prob >= 0.80:
        selected_bet = "OVER 1.5"
        confidence = range_15_prob * 100
        risk = "LOW"
    elif prob_home > 0.65 and odds_home < 1.40:
        selected_bet = f"{home_team} WIN"
        confidence = prob_home * 100
        risk = "LOW" if prob_home > 0.80 else "MEDIUM"
    
    if confidence >= 85:
        stake = 3
    elif confidence >= 75:
        stake = 2
    elif confidence >= 65:
        stake = 1
    
    # ========== FANCY VISUAL OUTPUT ==========
    st.divider()
    st.markdown(f"## 🔴 {home_team} vs {away_team} – PREGAME ANALYSIS")
    st.markdown(f"**{datetime.now().strftime('%d/%m/%Y %H:%M')} | Pregame (ΟΧΙ live)**")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📊 Total xG", f"{total_xg:.2f}")
    col2.metric("🎯 Total Shots", total_shots)
    col3.metric("🚩 Total Corners", f"{total_corners:.1f}")
    col4.metric("⚡ Tempo", tempo)
    
    st.markdown("### 📈 FULL MARKET SCAN")
    
    markets_fancy = [
        ("Over 1.5", prob_over15*100, "LOW" if prob_over15>0.80 else "MEDIUM"),
        ("Over 2.5", prob_over25*100, "LOW" if prob_over25>0.80 else "MEDIUM"),
        ("Under 2.5", prob_under25*100, "HIGH" if prob_under25<0.40 else "MEDIUM"),
        ("BTTS Yes", prob_btts*100, "LOW" if prob_btts>0.70 else "MEDIUM"),
        (f"{home_team} Win", prob_home*100, "LOW" if prob_home>0.75 else "MEDIUM"),
        ("Double Chance 1X", (prob_home+prob_draw)*100, "LOW")
    ]
    
    for name, prob, risk_lvl in markets_fancy:
        color = "🟢" if risk_lvl == "LOW" else "🟡" if risk_lvl == "MEDIUM" else "🔴"
        st.markdown(f"""
        <div class="market-row">
            <strong>{name}</strong> <span style="float:right">{color} {risk_lvl}</span>
            <div class="progress-bar-container">
                <div class="progress-bar-fill" style="width: {prob:.0f}%;">{prob:.0f}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### 🎯 DECISION ENGINE")
    if selected_bet != "NO BET":
        st.markdown(f"""
        <div class="stat-card">
            <div class="big-number">✅ {selected_bet}</div>
            <div>Confidence: <b>{confidence:.0f}%</b> | Risk: {risk} | Stake: {stake} units</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="stat-card">
            <div class="big-number">❌ NO BET</div>
            <div>Conflict / Low confidence / High variance</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### 🔴 UNDER SAFETY SYSTEM")
    if under_signal and range_04_prob >= 0.80 and tempo != "HIGH":
        st.success("✅ SELECT Under 3.5 (SAFE MODE)")
    elif under_signal:
        st.warning("⚠️ Under 2.5 signal detected but conditions not met → NO BET")
    else:
        st.info("No Under 2.5 signal")
    
    st.markdown("### 🟢 OVER SAFETY SYSTEM")
    if over_signal and range_15_prob >= 0.80:
        st.success("✅ SELECT Over 1.5 (SAFE MODE)")
    elif over_signal:
        st.warning("⚠️ Over 2.5 signal but Range 1-5 <80%")
    else:
        st.info("No Over 2.5 signal")
    
    st.markdown("### 🎭 SCENARIO ANALYSIS")
    st.markdown(f"**Base:** {home_team} dominates → 2-0 or 3-0")
    st.markdown(f"**Alternative:** {home_team} wins 2-1 or 3-1")
    st.markdown(f"**Collapse risk:** Draw or {away_team} win (low probability)")
    
    st.divider()
    st.info("💡 Advisory only. Gamble responsibly.")
    
else:
    st.info("👈 Paste your Gemini stats on the left")

st.caption("⚽ Elite Pre-Game Betting Analytics Engine | Safety First")
