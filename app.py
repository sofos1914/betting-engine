import streamlit as st
import pandas as pd
import re
import numpy as np

st.set_page_config(page_title="Pre-Game Football Analyzer", layout="wide")

st.title("⚽ PRE-GAME FOOTBALL ANALYZER")
st.markdown("**Paste stats from Gemini → Auto analysis → You decide**")

# ---------- ΚΟΥΤΙ ΓΙΑ PASTE ----------
st.markdown("### 📋 Paste your stats here (from Gemini)")
raw_input = st.text_area(
    "Copy-paste ολόκληρη τη λίστα στατιστικών:",
    height=300,
    placeholder="Paste the Gemini output here..."
)

# ---------- ΕΞΑΓΩΓΗ ΣΤΑΤΙΣΤΙΚΩΝ ΜΕ REGEX ----------
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
    # HOME / AWAY extraction
    home_match = re.search(r"Home Team:\s*\{\{([^}]+)\}\}", raw_input)
    away_match = re.search(r"Away Team:\s*\{\{([^}]+)\}\}", raw_input)
    home_team = home_match.group(1) if home_match else "HOME"
    away_team = away_match.group(1) if away_match else "AWAY"
    
    # ATTACK
    xg_home = extract_number(raw_input, r"xG average.*?(\d+\.?\d*)", 1.4)
    xg_away = extract_number(raw_input, r"xG average.*?(?:\n|.*?)(\d+\.?\d*)", 1.2)
    shots_home = extract_int(raw_input, r"Shots per game.*?(\d+)", 12)
    shots_away = extract_int(raw_input, r"Shots per game.*?(?:\n|.*?)(\d+)", 10)
    goals_home = extract_number(raw_input, r"Goals per game.*?(\d+\.?\d*)", 1.6)
    goals_away = extract_number(raw_input, r"Goals per game.*?(?:\n|.*?)(\d+\.?\d*)", 1.3)
    
    # DEFENSE
    conceded_home = extract_number(raw_input, r"Goals conceded per game.*?(\d+\.?\d*)", 1.0)
    conceded_away = extract_number(raw_input, r"Goals conceded per game.*?(?:\n|.*?)(\d+\.?\d*)", 1.2)
    clean_sheet_home = extract_int(raw_input, r"Clean sheets %.*?(\d+)", 25)
    clean_sheet_away = extract_int(raw_input, r"Clean sheets %.*?(?:\n|.*?)(\d+)", 20)
    
    # TEMPO
    possession_home = extract_int(raw_input, r"Possession %.*?(\d+)", 55)
    corners_home = extract_int(raw_input, r"Corners for avg.*?(\d+)", 5)
    corners_away = extract_int(raw_input, r"Corners against avg.*?(\d+)", 4)
    
    # FORM
    form_home = 10 - extract_int(raw_input, r"Last 5 matches.*?(\d+)", 5)
    form_away = 10 - extract_int(raw_input, r"Last 5 matches.*?(?:\n|.*?)(\d+)", 5)
    
    # CONTEXT
    injuries = "injury" in raw_input.lower() or "τραυματισμ" in raw_input.lower()
    derby = "derby" in raw_input.lower()
    
    st.success("✅ Stats extracted successfully!")
    
    # ---------- ΥΠΟΛΟΓΙΣΜΟΙ ----------
    total_xg = xg_home + xg_away
    total_shots = shots_home + shots_away
    total_corners = corners_home + corners_away
    
    def calc_prob():
        raw_home = (xg_home / max(xg_away, 0.5)) * (form_home / max(form_away, 1)) * 1.15
        raw_away = (xg_away / max(xg_home, 0.5)) * (form_away / max(form_home, 1))
        prob_home = min(0.85, raw_home / (raw_home + raw_away + 0.8))
        prob_away = min(0.85, raw_away / (raw_home + raw_away + 0.8))
        prob_draw = 1 - prob_home - prob_away
        return prob_home, prob_draw, prob_away
    
    prob_home, prob_draw, prob_away = calc_prob()
    
    expected_goals = total_xg
    prob_over25 = min(0.88, 1 - np.exp(-expected_goals * 0.55))
    prob_over15 = min(0.92, 1 - np.exp(-expected_goals * 0.7))
    prob_over35 = min(0.75, 1 - np.exp(-expected_goals * 0.4))
    prob_under25 = 1 - prob_over25
    prob_btts = min(0.85, (xg_home / 3) * (xg_away / 2.5) * 1.2)
    prob_btts = max(0.15, min(0.85, prob_btts))
    
    def risk_level(prob):
        if prob >= 70: return "🟢 LOW"
        elif prob >= 55: return "🟡 MEDIUM"
        else: return "🔴 HIGH"
    
    # ---------- ΠΙΝΑΚΑΣ MARKETS ----------
    st.divider()
    st.markdown("## 📊 ΠΙΝΑΚΑΣ MARKETS")
    
    markets = {
        "1X2 - HOME WIN": f"{prob_home*100:.1f}%",
        "1X2 - DRAW": f"{prob_draw*100:.1f}%",
        "1X2 - AWAY WIN": f"{prob_away*100:.1f}%",
        "Double Chance - 1X": f"{(prob_home+prob_draw)*100:.1f}%",
        "Double Chance - X2": f"{(prob_away+prob_draw)*100:.1f}%",
        "Double Chance - 12": f"{(prob_home+prob_away)*100:.1f}%",
        "BTTS - YES": f"{prob_btts*100:.1f}%",
        "BTTS - NO": f"{(1-prob_btts)*100:.1f}%",
        "Over 1.5": f"{prob_over15*100:.1f}%",
        "Over 2.5": f"{prob_over25*100:.1f}%",
        "Over 3.5": f"{prob_over35*100:.1f}%",
        "Under 2.5": f"{prob_under25*100:.1f}%",
    }
    
    df_markets = pd.DataFrame(markets.items(), columns=["Market", "Probability"])
    df_markets["Risk"] = df_markets["Probability"].str.replace("%", "").astype(float).apply(risk_level)
    st.dataframe(df_markets, use_container_width=True, hide_index=True)
    
    # ---------- ΑΝΑΛΥΣΗ ----------
    st.divider()
    st.markdown("## 📈 ΑΝΑΛΥΣΗ ΑΓΩΝΑ")
    colR1, colR2, colR3 = st.columns(3)
    colR1.metric("📊 Συνολικό xG", f"{total_xg:.2f}")
    colR2.metric("🎯 Σύνολο Σουτ", total_shots)
    colR3.metric("🚩 Σύνολο Κόρνερ", total_corners)
    
    conclusions = []
    if prob_home > 60:
        conclusions.append(f"✅ {home_team} φαβορί ({prob_home*100:.0f}%)")
    elif prob_away > 60:
        conclusions.append(f"✅ {away_team} φαβορί ({prob_away*100:.0f}%)")
    else:
        conclusions.append("⚖️ Ισορροπημένο ματς")
    if prob_over25 > 65:
        conclusions.append(f"⚽ Υψηλή Over 2.5 ({prob_over25*100:.0f}%)")
    else:
        conclusions.append(f"🛡️ Πιθανό Under 2.5 ({prob_under25*100:.0f}%)")
    if injuries:
        conclusions.append("⚠️ Τραυματισμοί → αυξημένο ρίσκο")
    if derby:
        conclusions.append("🔥 Derby → απρόβλεπτο")
    for c in conclusions:
        st.write(c)
    
    st.info("💡 Απόφαση δική σου. Βλέπεις τις πιθανότητες και επιλέγεις.")
    
else:
    st.info("👈 Paste your Gemini stats on the left to start analysis")

st.caption("⚽ Pre-Game Analyzer | Paste stats → Auto analysis")
