
import streamlit as st
import re
import numpy as np
import pandas as pd
import math
from datetime import datetime

st.set_page_config(layout="wide")

# ================= STYLE =================
st.markdown("""
<style>
.stApp {background:#0a0c10;color:#e0e0e0;}
.block {background:#14171c;padding:15px;border-radius:12px;border:1px solid #2c2f36;}
.title {color:#d4af37;font-size:28px;font-weight:bold;}
.small {color:#aaa;font-size:13px;}
.bar {background:#2c2f36;height:10px;border-radius:6px;}
.fill {background:#28a745;height:10px;border-radius:6px;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">⚔️ ELITE BETTING ENGINE</div>', unsafe_allow_html=True)

# ================= INPUT =================
raw = st.text_area("📋 Paste Gemini Stats", height=250)

# ================= PARSE =================
def get(text, pattern, d=1.0):
    m = re.search(pattern, text, re.I)
    return float(m.group(1).replace(",", ".")) if m else d

def geti(text, pattern, d=5):
    m = re.search(pattern, text, re.I)
    return int(m.group(1)) if m else d

if raw:

    home = re.search(r"Home Team:\s*\{\{([^}]+)\}\}", raw)
    away = re.search(r"Away Team:\s*\{\{([^}]+)\}\}", raw)

    home = home.group(1) if home else "HOME"
    away = away.group(1) if away else "AWAY"

    xg_h = get(raw, r"xG.*?(\d+\.?\d*)", 1.5)
    xg_a = get(raw, r"xG.*?(?:\n.*?){0,3}(\d+\.?\d*)", 1.0)

    shots_h = geti(raw, r"shots on target.*?(\d+)", 5)
    shots_a = geti(raw, r"shots on target.*?(?:\n.*?){0,2}(\d+)", 4)

    corners_h = get(raw, r"corners for.*?(\d+\.?\d*)", 6)
    corners_a = get(raw, r"corners against.*?(\d+\.?\d*)", 4)

    odds_home = get(raw, r"odds.*?(\d+\.?\d*)", 1.40)

    total_xg = xg_h + xg_a
    shots = shots_h + shots_a
    corners = corners_h + corners_a

    # ================= POISSON =================
    def p(l, k):
        return (l**k * math.exp(-l)) / math.factorial(k)

    range04 = sum(p(total_xg, k) for k in range(0,5))
    range15 = sum(p(total_xg, k) for k in range(1,6))

    # ================= PROBS =================
    over25 = 1 - np.exp(-total_xg * 0.55)
    under25 = 1 - over25
    over15 = 1 - np.exp(-total_xg * 0.75)

    prob_home = min(0.88, xg_h / max(xg_a,0.5))

    # ================= TEMPO =================
    if shots > 22:
        tempo = "HIGH"
    elif shots > 14:
        tempo = "MEDIUM"
    else:
        tempo = "LOW"

    # ================= EDGE =================
    implied = 1 / odds_home
    edge = over25 - implied

    # ================= DECISION =================
    selected = "NO BET"
    conf = 0
    risk = "HIGH"

    if under25 > 0.55 and range04 >= 0.80 and tempo != "HIGH":
        selected = "UNDER 3.5"
        conf = range04*100
        risk = "LOW"

    elif over25 > 0.60 and range15 >= 0.80 and edge > 0.08:
        selected = "OVER 1.5"
        conf = range15*100
        risk = "LOW"

    elif prob_home > 0.65:
        selected = f"{home} WIN"
        conf = prob_home*100
        risk = "MEDIUM"

    # ================= STAKE =================
    if conf >= 85: stake = 3
    elif conf >= 75: stake = 2
    elif conf >= 65: stake = 1
    else: stake = 0

    # ================= UI =================
    st.divider()

    st.markdown(f"""
    <div class="block">
    <div class="title">{home} vs {away}</div>
    <div class="small">{datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
    </div>
    """, unsafe_allow_html=True)

    col1,col2,col3,col4 = st.columns(4)

    col1.metric("xG", round(total_xg,2))
    col2.metric("Shots", shots)
    col3.metric("Corners", round(corners,1))
    col4.metric("Tempo", tempo)

    # ===== RANGE =====
    st.markdown("### 📊 RANGE SAFETY")

    def bar(label,val):
        st.markdown(f"""
        <div>{label} {val*100:.0f}%</div>
        <div class="bar"><div class="fill" style="width:{val*100:.0f}%"></div></div>
        """, unsafe_allow_html=True)

    bar("0-4 Goals", range04)
    bar("1-5 Goals", range15)

    # ===== TABLE =====
    st.markdown("### 📋 MARKET TABLE")

    df = pd.DataFrame([
        ["Over 1.5","1-5",over15*100],
        ["Over 2.5","1-5",over25*100],
        ["Under 3.5","0-4",range04*100],
        ["BTTS","-",60],
        [f"{home} Win","-",prob_home*100]
    ],columns=["Bet","Range","Confidence"])

    df["Risk"] = df["Confidence"].apply(lambda x: "LOW" if x>80 else "MED" if x>65 else "HIGH")
    df["Stake"] = df["Confidence"].apply(lambda x: "3u" if x>=85 else "2u" if x>=75 else "1u" if x>=65 else "-")

    st.dataframe(df,use_container_width=True)

    # ===== FINAL =====
    st.markdown("### 🎯 FINAL DECISION")

    if selected != "NO BET":
        st.success(f"{selected} | {conf:.0f}% | {risk} | {stake}u")
    else:
        st.error("NO BET")

    # ===== CORNERS =====
    st.markdown("### 🟣 CORNERS")

    if corners > 9:
        st.success("YES Over 8.5")
    else:
        st.error("NO")

else:
    st.info("Paste stats to run analysis")
