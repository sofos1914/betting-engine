import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Pre-Game Football Analyzer", layout="wide")

st.title("⚽ PRE-GAME FOOTBALL ANALYZER")
st.markdown("**Εσύ διαβάζεις στατιστικά → Εσύ αποφασίζεις**")

# ---------- ΟΜΑΔΕΣ ----------
col1, col2 = st.columns(2)
with col1:
    home = st.text_input("🏠 HOME TEAM", "MAN UNITED")
with col2:
    away = st.text_input("✈️ AWAY TEAM", "LIVERPOOL")

st.divider()

# ---------- ΣΤΑΤΙΣΤΙΚΑ ΕΙΣΟΔΟΥ ----------
st.markdown("### 📊 ΕΙΣΑΓΩΓΗ ΣΤΑΤΙΣΤΙΚΩΝ (από FBref, SofaScore, FootyStats)")

tab1, tab2, tab3 = st.tabs(["⚽ ΕΠΙΘΕΣΗ & ΑΜΥΝΑ", "🎯 TEMPO & ΕΜΦΑΝΙΣΗ", "🏆 ΕΞΩΤΕΡΙΚΟΙ ΠΑΡΑΓΟΝΤΕΣ"])

with tab1:
    colA, colB = st.columns(2)
    with colA:
        st.markdown(f"**{home}**")
        goals_home = st.number_input("Γκολ/παιχνίδι", 0.0, 4.0, 1.7, key="gh")
        xg_home = st.number_input("xG", 0.0, 4.0, 1.5, key="xgh")
        shots_home = st.number_input("Σουτ/παιχνίδι", 0, 35, 14, key="sh")
        shots_ot_home = st.number_input("Σουτ στον στόχο", 0, 20, 5, key="soth")
        form_home = st.slider("Form (τελευταία 5)", 0, 10, 7, key="fh")
        clean_sheet_home = st.slider("Clean sheet %", 0, 100, 30, key="csh")
    with colB:
        st.markdown(f"**{away}**")
        goals_away = st.number_input("Γκολ/παιχνίδι", 0.0, 4.0, 1.4, key="ga")
        xg_away = st.number_input("xG", 0.0, 4.0, 1.3, key="xga")
        shots_away = st.number_input("Σουτ/παιχνίδι", 0, 35, 12, key="sa")
        shots_ot_away = st.number_input("Σουτ στον στόχο", 0, 20, 4, key="sota")
        form_away = st.slider("Form (τελευταία 5)", 0, 10, 5, key="fa")
        clean_sheet_away = st.slider("Clean sheet %", 0, 100, 20, key="csa")

with tab2:
    possession_home = st.slider("Κατοχή % HOME", 20, 80, 55)
    tempo = st.selectbox("TEMPO ΑΓΩΝΑ", ["LOW", "MEDIUM", "HIGH"])
    corners_home = st.number_input("Κόρνερ HOME", 0, 15, 5)
    corners_away = st.number_input("Κόρνερ AWAY", 0, 15, 4)

with tab3:
    injuries = st.checkbox("Σημαντικοί τραυματισμοί")
    derby = st.checkbox("Derby / Υψηλή πίεση")
    rest_home = st.selectbox("Ξεκούραση HOME", ["Φυσιολογική", "Περισσότερη", "Λιγότερη"])
    rest_away = st.selectbox("Ξεκούραση AWAY", ["Φυσιολογική", "Περισσότερη", "Λιγότερη"])

# ---------- ΥΠΟΛΟΓΙΣΜΟΙ ----------
total_xg = xg_home + xg_away
total_shots = shots_home + shots_away
total_corners = corners_home + corners_away

def calc_prob(home_advantage=1.15):
    raw_home = (xg_home / max(xg_away, 0.5)) * (form_home / max(form_away, 1)) * home_advantage
    raw_away = (xg_away / max(xg_home, 0.5)) * (form_away / max(form_home, 1))
    
    prob_home = min(0.85, raw_home / (raw_home + raw_away + 0.8))
    prob_away = min(0.85, raw_away / (raw_home + raw_away + 0.8))
    prob_draw = 1 - prob_home - prob_away
    
    if tempo == "HIGH":
        prob_home *= 0.95
        prob_away *= 0.95
        prob_draw = 1 - prob_home - prob_away
    elif tempo == "LOW":
        prob_draw *= 1.1
        prob_home *= 0.97
        prob_away *= 0.97
        prob_draw = min(0.45, prob_draw)
        prob_home = (1 - prob_draw) / 2
        prob_away = (1 - prob_draw) / 2
    
    return prob_home, prob_draw, prob_away

prob_home, prob_draw, prob_away = calc_prob()

expected_goals = total_xg
prob_over15 = min(0.92, 1 - np.exp(-expected_goals * 0.7))
prob_over25 = min(0.88, 1 - np.exp(-expected_goals * 0.55))
prob_over35 = min(0.75, 1 - np.exp(-expected_goals * 0.4))
prob_under15 = 1 - prob_over15
prob_under25 = 1 - prob_over25
prob_under35 = 1 - prob_over35

prob_btts = min(0.85, (xg_home / 3) * (xg_away / 2.5) * 1.2)
prob_btts = max(0.15, min(0.85, prob_btts))

prob_dc_home_draw = prob_home + prob_draw
prob_dc_away_draw = prob_away + prob_draw
prob_dc_home_away = prob_home + prob_away

def risk_level(prob):
    if prob >= 70:
        return "🟢 LOW"
    elif prob >= 55:
        return "🟡 MEDIUM"
    else:
        return "🔴 HIGH"

# ---------- ΠΙΝΑΚΑΣ MARKETS ----------
st.divider()
st.markdown("## 📊 ΠΙΝΑΚΑΣ MARKETS")

markets = {
    "1X2 - HOME WIN": f"{prob_home*100:.1f}%",
    "1X2 - DRAW": f"{prob_draw*100:.1f}%",
    "1X2 - AWAY WIN": f"{prob_away*100:.1f}%",
    "Double Chance - 1X": f"{prob_dc_home_draw*100:.1f}%",
    "Double Chance - X2": f"{prob_dc_away_draw*100:.1f}%",
    "Double Chance - 12": f"{prob_dc_home_away*100:.1f}%",
    "BTTS - YES": f"{prob_btts*100:.1f}%",
    "BTTS - NO": f"{100-pro_btts*100:.1f}%",
    "Over 1.5": f"{prob_over15*100:.1f}%",
    "Over 2.5": f"{prob_over25*100:.1f}%",
    "Over 3.5": f"{prob_over35*100:.1f}%",
    "Under 1.5": f"{prob_under15*100:.1f}%",
    "Under 2.5": f"{prob_under25*100:.1f}%",
    "Under 3.5": f"{prob_under35*100:.1f}%",
}

df_markets = pd.DataFrame(markets.items(), columns=["Market", "Probability"])
df_markets["Risk"] = df_markets["Probability"].str.replace("%", "").astype(float).apply(risk_level)

st.dataframe(df_markets, use_container_width=True, hide_index=True)

# ---------- ΑΝΑΛΥΣΗ ΑΓΩΝΑ ----------
st.divider()
st.markdown("## 📈 ΑΝΑΛΥΣΗ ΑΓΩΝΑ")

colR1, colR2, colR3 = st.columns(3)
colR1.metric("📊 Συνολικό xG", f"{total_xg:.2f}")
colR2.metric("🎯 Σύνολο Σουτ", total_shots)
colR3.metric("🚩 Σύνολο Κόρνερ", total_corners)

st.markdown("### 🔍 ΣΥΜΠΕΡΑΣΜΑΤΑ")
conclusions = []

if prob_home > 60:
    conclusions.append(f"✅ {home} μεγάλο φαβορί ({prob_home*100:.0f}%)")
elif prob_away > 60:
    conclusions.append(f"✅ {away} μεγάλο φαβορί ({prob_away*100:.0f}%)")
else:
    conclusions.append("⚖️ Ισορροπημένο ματς")

if prob_over25 > 65:
    conclusions.append(f"⚽ Υψηλή πιθανότητα Over 2.5 ({prob_over25*100:.0f}%)")
else:
    conclusions.append(f"🛡️ Πιθανό Under 2.5 ({prob_under25*100:.0f}%)")

if prob_btts > 60:
    conclusions.append(f"🤝 Πιθανό BTTS ({prob_btts*100:.0f}%)")

if injuries:
    conclusions.append("⚠️ Σημαντικοί τραυματισμοί → αυξημένο ρίσκο")
if derby:
    conclusions.append("🔥 Derby → απρόβλεπτο αποτέλεσμα")

for c in conclusions:
    st.write(c)

st.divider()
st.info("💡 **Απόφαση δική σου.** Βλέπεις τις πιθανότητες και επιλέγεις το market που σου ταιριάζει.")
