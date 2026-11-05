"""
Mobile Robot Performance Dashboard
YaneCode Academy - Streamlit project
Author: BEDDIAF Marwa
Run:  streamlit run app.py
"""
import hashlib
import hmac
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

# ----------------------------------------------------------------------------
# PAGE CONFIG & THEME
# ----------------------------------------------------------------------------
st.set_page_config(page_title="Robot Performance Dashboard", page_icon="🤖",
                   layout="wide", initial_sidebar_state="expanded")

PRIMARY, ACCENT, DANGER, OK = "#4F46E5", "#06B6D4", "#EF4444", "#10B981"
PALETTE = ["#4F46E5", "#06B6D4", "#10B981", "#F59E0B", "#EF4444",
           "#8B5CF6", "#EC4899", "#64748B"]
sns.set_theme(style="whitegrid", palette=PALETTE, font_scale=0.9)
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 110})

st.markdown(f"""
<style>
.block-container {{padding-top: 1.5rem; max-width: 1400px;}}
.hero {{background: linear-gradient(120deg,{PRIMARY},{ACCENT}); color:white;
        padding: 1.4rem 1.8rem; border-radius: 16px; margin-bottom: 1.2rem;}}
.hero h1 {{margin:0; font-size:1.9rem; color:white;}}
.hero p {{margin:.2rem 0 0 0; opacity:.9;}}
.kpi {{background:white; border-radius:14px; padding:1rem 1.2rem;
       box-shadow:0 2px 10px rgba(15,23,42,.08); border-left:5px solid {PRIMARY};}}
.kpi .label {{font-size:.78rem; color:#64748B; text-transform:uppercase;
              letter-spacing:.04em;}}
.kpi .value {{font-size:1.65rem; font-weight:700; color:#0F172A;}}
.kpi .sub {{font-size:.75rem; color:#94A3B8;}}
.login-box {{max-width:420px; margin:6vh auto 0 auto; padding:2rem;
             background:white; border-radius:18px;
             box-shadow:0 8px 30px rgba(15,23,42,.12);}}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# AUTHENTICATION  (password stored as SHA-256 hash, not in clear text)
# ----------------------------------------------------------------------------
USERNAME = "marwa"
PASSWORD_HASH = hashlib.sha256("Marwabdf34".encode()).hexdigest()


def check_login(user: str, pwd: str) -> bool:
    ok_user = hmac.compare_digest(user.strip().lower(), USERNAME)
    ok_pwd = hmac.compare_digest(hashlib.sha256(pwd.encode()).hexdigest(),
                                 PASSWORD_HASH)
    return ok_user and ok_pwd


def login_page():
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    st.markdown("### 🤖 Robot Performance Dashboard")
    st.caption("Please sign in to access the analysis.")
    with st.form("login"):
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        go = st.form_submit_button("Sign in", use_container_width=True)
    if go:
        if check_login(user, pwd):
            st.session_state["auth"] = True
            st.session_state["user"] = user.strip().lower()
            st.rerun()
        else:
            st.error("Invalid username or password.")
    st.markdown("</div>", unsafe_allow_html=True)


if not st.session_state.get("auth"):
    login_page()
    st.stop()

# ----------------------------------------------------------------------------
# DATA LOADING & CLEANING
# ----------------------------------------------------------------------------
COLUMN_MAP = {
    "timestamp": "timestamp", "robot_id": "robot_id", "mission_id": "mission_id",
    "mode": "mode", "type_sol": "floor_type", "charge_utile_kg": "payload_kg",
    "x_m": "x_m", "y_m": "y_m", "orientation_deg": "heading_deg",
    "cible_x_m": "target_x_m", "cible_y_m": "target_y_m",
    "distance_cible_m": "target_dist_m", "vitesse_consigne_ms": "speed_cmd_ms",
    "vitesse_reelle_ms": "speed_ms", "vitesse_angulaire_rads": "ang_vel_rads",
    "erreur_vitesse_ms": "speed_err_ms", "erreur_trajectoire_m": "traj_err_m",
    "roue_gauche_rpm": "rpm_left", "roue_droite_rpm": "rpm_right",
    "courant_moteur_g_A": "current_left_A", "courant_moteur_d_A": "current_right_A",
    "tension_batterie_V": "battery_V", "niveau_batterie_pct": "battery_pct",
    "temperature_moteur_C": "motor_temp_C", "distance_obstacle_m": "obstacle_dist_m",
    "glissement_pct": "slip_pct", "puissance_W": "power_W",
    "energie_cumulee_Wh": "energy_Wh", "distance_cumulee_m": "distance_m",
    "evenement": "event",
}
VALUE_MAP = {
    "mode": {"Navigation": "Navigation", "Évitement": "Obstacle avoidance",
             "Charge": "Charging", "Retour charge": "Return to charger"},
    "floor_type": {"Carrelage": "Tile", "Béton lisse": "Smooth concrete",
                   "Béton brut": "Rough concrete"},
    "event": {"Aucun": "None", "Mission terminée": "Mission completed",
              "Obstacle évité": "Obstacle avoided", "Collision": "Collision",
              "Blocage roue": "Wheel blockage", "Batterie faible": "Low battery",
              "Arrivée station de charge": "Arrived at charger",
              "Charge terminée": "Charge completed"},
}
NUMERIC = [c for c in COLUMN_MAP.values()
           if c not in ("timestamp", "robot_id", "mission_id", "mode",
                        "floor_type", "event")]


def clean_data(raw: pd.DataFrame):
    """Return (clean_df, report_dict). Each step is logged for the Cleaning page."""
    rep = {"rows_raw": len(raw), "cols_raw": raw.shape[1]}
    df = raw.copy()
    df.columns = [c.strip().lstrip("\ufeff") for c in df.columns]
    df = df.rename(columns=COLUMN_MAP)

    # 1. text columns
    for c in ["robot_id", "mission_id", "mode", "floor_type", "event"]:
        if c in df:
            df[c] = df[c].astype(str).str.strip()
    for c, m in VALUE_MAP.items():
        if c in df:
            df[c] = df[c].replace(m)
    # 2. types
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    for c in NUMERIC:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    rep["missing_before"] = int(df.isna().sum().sum())
    # 3. duplicates & invalid timestamps
    rep["duplicates"] = int(df.duplicated().sum())
    df = df.drop_duplicates()
    rep["bad_timestamps"] = int(df["timestamp"].isna().sum())
    df = df.dropna(subset=["timestamp", "robot_id"])
    df = df.sort_values(["robot_id", "timestamp"]).reset_index(drop=True)
    # 4. missing numeric values -> interpolate within each robot
    df[NUMERIC] = (df.groupby("robot_id")[NUMERIC]
                   .transform(lambda s: s.interpolate(limit_direction="both")))
    # 5. physically impossible values
    rep["neg_slip"] = int((df["slip_pct"] < 0).sum())
    rep["slip_over_100"] = int((df["slip_pct"] > 100).sum())
    df["slip_pct"] = df["slip_pct"].clip(0, 100)
    rep["neg_speed"] = int((df["speed_ms"] < 0).sum())
    df["speed_ms"] = df["speed_ms"].clip(lower=0)
    df["battery_pct"] = df["battery_pct"].clip(0, 100)
    # 6. derived columns
    df["abs_speed_err"] = df["speed_err_ms"].abs()
    df["current_avg_A"] = (df["current_left_A"] + df["current_right_A"]) / 2
    df["step_dist_m"] = df["speed_ms"] * 2.0               # 2 s sampling
    df["step_energy_Wh"] = df["power_W"] * 2.0 / 3600.0
    df["date"] = df["timestamp"].dt.date
    # 7. statistical outliers (IQR) - reported, not removed
    out = {}
    for c in ["speed_ms", "traj_err_m", "motor_temp_C", "power_W", "slip_pct"]:
        q1, q3 = df[c].quantile([.25, .75])
        iqr = q3 - q1
        out[c] = int(((df[c] < q1 - 1.5 * iqr) | (df[c] > q3 + 1.5 * iqr)).sum())
    rep["outliers"] = out
    rep["missing_after"] = int(df[NUMERIC].isna().sum().sum())
    rep["rows_clean"] = len(df)
    return df, rep


@st.cache_data(show_spinner="Loading and cleaning data...")
def load(file_or_path):
    raw = pd.read_csv(file_or_path, encoding="utf-8-sig")
    return raw, *clean_data(raw)


# ----------------------------------------------------------------------------
# KPI FUNCTIONS
# ----------------------------------------------------------------------------
def kpi_by_robot(d: pd.DataFrame) -> pd.DataFrame:
    g = d.groupby("robot_id")
    k = pd.DataFrame({
        "missions_completed": g["event"].apply(lambda s: (s == "Mission completed").sum()),
        "distance_m": g["step_dist_m"].sum(),
        "energy_Wh": g["step_energy_Wh"].sum(),
        "avg_speed_ms": g["speed_ms"].mean(),
        "speed_mae_ms": g["abs_speed_err"].mean(),
        "traj_err_m": g["traj_err_m"].mean(),
        "avg_current_A": g["current_avg_A"].mean(),
        "avg_motor_temp_C": g["motor_temp_C"].mean(),
        "max_motor_temp_C": g["motor_temp_C"].max(),
        "avg_slip_pct": g["slip_pct"].mean(),
        "collisions": g["event"].apply(lambda s: (s == "Collision").sum()),
        "blockages": g["event"].apply(lambda s: (s == "Wheel blockage").sum()),
    })
    k["Wh_per_m"] = k["energy_Wh"] / k["distance_m"].replace(0, np.nan)
    # battery autonomy: discharge rate (%/h) outside charging, usable range 100 -> 20 %
    rates = {}
    for rid, x in d.groupby("robot_id"):
        x = x[x["mode"] != "Charging"]
        drop = -x["battery_pct"].diff().clip(upper=0).sum()
        hours = len(x) * 2 / 3600
        rates[rid] = drop / hours if hours else np.nan
    k["discharge_pct_per_h"] = pd.Series(rates)
    k["autonomy_h"] = 80 / k["discharge_pct_per_h"]
    return k


def fleet_kpis(d: pd.DataFrame) -> dict:
    dist, en = d["step_dist_m"].sum(), d["step_energy_Wh"].sum()
    k = kpi_by_robot(d)
    return {
        "missions": int((d["event"] == "Mission completed").sum()),
        "distance_km": dist / 1000,
        "wh_per_m": en / dist if dist else np.nan,
        "speed_mae": d["abs_speed_err"].mean(),
        "traj_err": d["traj_err_m"].mean(),
        "autonomy_h": k["autonomy_h"].mean(),
        "collisions": int((d["event"] == "Collision").sum()),
        "blockages": int((d["event"] == "Wheel blockage").sum()),
        "slip": d["slip_pct"].mean(),
        "avg_speed": d["speed_ms"].mean(),
    }


def kpi_card(col, label, value, sub="", color=PRIMARY):
    col.markdown(f"<div class='kpi' style='border-left-color:{color}'>"
                 f"<div class='label'>{label}</div><div class='value'>{value}</div>"
                 f"<div class='sub'>{sub}</div></div>", unsafe_allow_html=True)


def show(fig):
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


# ----------------------------------------------------------------------------
# SIDEBAR : DATA SOURCE + NAVIGATION + FILTERS
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"### 👋 Hello, {st.session_state['user'].capitalize()}")
    if st.button("Log out", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.divider()
    st.markdown("**📂 Data source**")
    uploaded = st.file_uploader("Upload the robot CSV", type="csv")

DEFAULT_PATHS = ["beddiaf_marwa.csv", "data/beddiaf_marwa.csv"]
source = uploaded or next((p for p in DEFAULT_PATHS if os.path.exists(p)), None)

if source is None:
    st.markdown("<div class='hero'><h1>🤖 Mobile Robot Performance Dashboard</h1>"
                "<p>Upload <b>beddiaf_marwa.csv</b> in the sidebar to start "
                "(or place it next to app.py).</p></div>", unsafe_allow_html=True)
    st.info("No dataset found. Use the uploader in the left sidebar.")
    st.stop()

raw, df, report = load(source)

with st.sidebar:
    st.divider()
    page = st.radio("**Navigation**", ["📊 Dashboard", "🧹 Data Cleaning",
                                       "📈 Visualizations", "🎯 KPIs",
                                       "💡 Conclusions"])
    st.divider()
    st.markdown("**🔎 Filters**")
    tmin, tmax = df["timestamp"].min().to_pydatetime(), df["timestamp"].max().to_pydatetime()
    t_range = st.slider("Time window", tmin, tmax, (tmin, tmax), format="HH:mm")
    robots = st.multiselect("Robots", sorted(df["robot_id"].unique()),
                            default=sorted(df["robot_id"].unique()))
    modes = st.multiselect("Mode", sorted(df["mode"].unique()),
                           default=sorted(df["mode"].unique()))
    floors = st.multiselect("Floor type", sorted(df["floor_type"].unique()),
                            default=sorted(df["floor_type"].unique()))
    p_lo, p_hi = float(df["payload_kg"].min()), float(df["payload_kg"].max())
    payload = st.slider("Payload (kg)", p_lo, p_hi, (p_lo, p_hi))

f = df[(df["timestamp"].between(*t_range)) & df["robot_id"].isin(robots)
       & df["mode"].isin(modes) & df["floor_type"].isin(floors)
       & df["payload_kg"].between(*payload)]

st.markdown("<div class='hero'><h1>🤖 Mobile Robot Performance Dashboard</h1>"
            "<p>Differential-drive fleet telemetry · 8 robots · 20 m × 15 m workshop</p>"
            "</div>", unsafe_allow_html=True)

if f.empty:
    st.warning("No data matches the current filters. Please widen your selection.")
    st.stop()

K = fleet_kpis(f)
KR = kpi_by_robot(f)


def kpi_row():
    c = st.columns(5)
    kpi_card(c[0], "Missions completed", f"{K['missions']:,}", "mission-completed events")
    kpi_card(c[1], "Distance travelled", f"{K['distance_km']:.1f} km", "fleet total", ACCENT)
    kpi_card(c[2], "Energy / distance", f"{K['wh_per_m']:.3f} Wh/m", "fleet average", OK)
    kpi_card(c[3], "Speed error (MAE)", f"{K['speed_mae']:.3f} m/s", "mean |error|", "#F59E0B")
    kpi_card(c[4], "Trajectory error", f"{K['traj_err']:.3f} m", "mean tracking error", "#8B5CF6")
    st.write("")
    c = st.columns(5)
    kpi_card(c[0], "Battery autonomy", f"{K['autonomy_h']:.1f} h", "100% → 20% estimate", OK)
    kpi_card(c[1], "Collisions", f"{K['collisions']}", "events", DANGER)
    kpi_card(c[2], "Wheel blockages", f"{K['blockages']}", "events", DANGER)
    kpi_card(c[3], "Avg. wheel slip", f"{K['slip']:.2f} %", "all floors", "#F59E0B")
    kpi_card(c[4], "Avg. speed", f"{K['avg_speed']:.2f} m/s", "actual speed", ACCENT)


# ----------------------------------------------------------------------------
# PAGES
# ----------------------------------------------------------------------------
def plot_trajectories(d, ax=None, max_pts=4000):
    ax = ax or plt.gca()
    for i, (rid, x) in enumerate(d.groupby("robot_id")):
        x = x.iloc[::max(1, len(x) // max_pts)]
        ax.plot(x["x_m"], x["y_m"], lw=.8, alpha=.8, label=rid,
                color=PALETTE[i % len(PALETTE)])
    ax.set(xlim=(0, 20), ylim=(0, 15), xlabel="x (m)", ylabel="y (m)", aspect="equal")
    ax.legend(ncol=4, fontsize=7, loc="upper center", bbox_to_anchor=(.5, 1.18))


def page_dashboard():
    kpi_row()
    st.write("")
    a, b = st.columns(2)
    with a:
        st.subheader("Trajectories (x-y)")
        fig, ax = plt.subplots(figsize=(6, 4.6))
        plot_trajectories(f, ax)
        show(fig)
    with b:
        st.subheader("Speed trend (5-min mean)")
        t = (f.set_index("timestamp").groupby("robot_id")["speed_ms"]
             .resample("5min").mean().reset_index())
        fig, ax = plt.subplots(figsize=(6, 4.6))
        sns.lineplot(data=t, x="timestamp", y="speed_ms", hue="robot_id", ax=ax, lw=1.4)
        ax.set(xlabel="Time", ylabel="Speed (m/s)")
        ax.legend(ncol=4, fontsize=7)
        show(fig)
    a, b = st.columns(2)
    with a:
        st.subheader("Energy consumption by robot")
        fig, ax = plt.subplots(figsize=(6, 3.8))
        d = KR.reset_index().sort_values("Wh_per_m", ascending=False)
        sns.barplot(data=d, x="robot_id", y="Wh_per_m", ax=ax, palette=PALETTE[:len(d)],
                    hue="robot_id", legend=False)
        ax.set(xlabel="", ylabel="Wh / m")
        show(fig)
    with b:
        st.subheader("Time share by mode")
        m = f["mode"].value_counts()
        fig, ax = plt.subplots(figsize=(6, 3.8))
        ax.pie(m, labels=m.index, autopct="%1.1f%%", colors=PALETTE, startangle=90,
               wedgeprops=dict(width=.45, edgecolor="white"), textprops={"fontsize": 8})
        show(fig)
    st.subheader("Incidents Pareto")
    pareto_chart()


def pareto_chart():
    ev = f[~f["event"].isin(["None", "Mission completed"])]["event"].value_counts()
    if ev.empty:
        st.info("No incident events in the selection.")
        return
    cum = ev.cumsum() / ev.sum() * 100
    fig, ax = plt.subplots(figsize=(10, 3.6))
    ax.bar(ev.index, ev.values, color=PRIMARY)
    ax.set_ylabel("Count")
    ax.tick_params(axis="x", rotation=20)
    ax2 = ax.twinx()
    ax2.plot(ev.index, cum.values, color=DANGER, marker="o")
    ax2.axhline(80, ls="--", color="grey", lw=.8)
    ax2.set(ylim=(0, 105), ylabel="Cumulative %")
    ax2.spines["right"].set_visible(True)
    ax2.grid(False)
    show(fig)


def page_cleaning():
    st.subheader("🧹 Data cleaning report")
    c = st.columns(4)
    kpi_card(c[0], "Raw rows", f"{report['rows_raw']:,}")
    kpi_card(c[1], "Clean rows", f"{report['rows_clean']:,}", color=OK)
    kpi_card(c[2], "Duplicates removed", report["duplicates"], color=DANGER)
    kpi_card(c[3], "Missing values (after)", report["missing_after"], color=OK)
    st.write("")
    a, b = st.columns(2)
    with a:
        st.markdown("**Cleaning steps applied**")
        st.markdown(f"""
1. Column names trimmed, BOM removed and translated to English
2. Categories translated (modes, floor types, events)
3. Types converted (`timestamp` → datetime, numeric columns)
4. Missing values before cleaning: **{report['missing_before']}** → interpolated per robot
5. Duplicates removed: **{report['duplicates']}**; invalid timestamps: **{report['bad_timestamps']}**
6. Wheel slip: **{report['neg_slip']}** negative values and **{report['slip_over_100']}** values > 100 % clipped to [0, 100]
7. Negative speeds clipped to 0 ({report['neg_speed']} found)
8. Derived columns: |speed error|, mean motor current, step distance, step energy
""")
    with b:
        st.markdown("**IQR outliers detected (kept, flagged only)**")
        st.dataframe(pd.DataFrame(report["outliers"].items(),
                                  columns=["variable", "outliers"]),
                     hide_index=True, use_container_width=True)
    st.markdown("**Preview of the cleaned dataset**")
    st.dataframe(df.head(200), use_container_width=True, height=280)
    st.markdown("**Descriptive statistics**")
    st.dataframe(df[NUMERIC].describe().T.round(3), use_container_width=True)
    st.download_button("⬇️ Download cleaned CSV", df.to_csv(index=False).encode(),
                       "robot_data_clean.csv", "text/csv")


def page_viz():
    t1, t2, t3, t4, t5 = st.tabs(["Trajectories", "Speed & heading", "Distance & energy",
                                  "Motor & battery", "Slip & correlations"])
    with t1:
        sel = st.selectbox("Robot", ["All"] + sorted(f["robot_id"].unique()))
        d = f if sel == "All" else f[f["robot_id"] == sel]
        fig, ax = plt.subplots(figsize=(9, 6.2))
        plot_trajectories(d, ax)
        ax.scatter(d["target_x_m"].iloc[::60], d["target_y_m"].iloc[::60], s=8,
                   c="black", alpha=.4, label="targets")
        show(fig)
    with t2:
        a, b = st.columns(2)
        with a:
            st.markdown("**Commanded vs actual speed**")
            s = f.sample(min(3000, len(f)), random_state=1)
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.scatterplot(data=s, x="speed_cmd_ms", y="speed_ms", hue="floor_type",
                            s=10, alpha=.5, ax=ax)
            ax.plot([0, 1], [0, 1], "k--", lw=.8)
            ax.set(xlabel="Commanded (m/s)", ylabel="Actual (m/s)")
            show(fig)
        with b:
            st.markdown("**Speed error distribution**")
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.histplot(f["speed_err_ms"].clip(-.2, .3), bins=50, kde=True,
                         color=PRIMARY, ax=ax)
            ax.set(xlabel="Speed error (m/s)")
            show(fig)
        a, b = st.columns(2)
        with a:
            st.markdown("**Heading distribution (polar)**")
            fig = plt.figure(figsize=(5, 4))
            ax = fig.add_subplot(111, projection="polar")
            ax.hist(np.deg2rad(f["heading_deg"]), bins=36, color=ACCENT, alpha=.85)
            show(fig)
        with b:
            st.markdown("**Heading over time (first robot in selection)**")
            r = f[f["robot_id"] == f["robot_id"].iloc[0]].iloc[:600]
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.plot(r["timestamp"], r["heading_deg"], lw=.8, color=PRIMARY)
            ax.set(ylabel="Heading (deg)", xlabel="Time")
            show(fig)
    with t3:
        a, b = st.columns(2)
        with a:
            st.markdown("**Cumulative distance per robot**")
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.lineplot(data=f, x="timestamp", y="distance_m", hue="robot_id", ax=ax, lw=1)
            ax.set(ylabel="Distance (m)", xlabel="Time")
            ax.legend(ncol=4, fontsize=7)
            show(fig)
        with b:
            st.markdown("**Cumulative energy per robot**")
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.lineplot(data=f, x="timestamp", y="energy_Wh", hue="robot_id", ax=ax, lw=1)
            ax.set(ylabel="Energy (Wh)", xlabel="Time")
            ax.legend(ncol=4, fontsize=7)
            show(fig)
        st.markdown("**Power vs payload by floor type**")
        fig, ax = plt.subplots(figsize=(9, 4))
        s = f.sample(min(4000, len(f)), random_state=2)
        sns.scatterplot(data=s, x="payload_kg", y="power_W", hue="floor_type", s=10,
                        alpha=.5, ax=ax)
        show(fig)
    with t4:
        a, b = st.columns(2)
        with a:
            st.markdown("**Motor current by robot**")
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.boxplot(data=f, x="robot_id", y="current_avg_A", ax=ax, palette=PALETTE,
                        hue="robot_id", legend=False, fliersize=1)
            ax.set(xlabel="", ylabel="Mean motor current (A)")
            show(fig)
        with b:
            st.markdown("**Motor temperature by robot**")
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.boxplot(data=f, x="robot_id", y="motor_temp_C", ax=ax, palette=PALETTE,
                        hue="robot_id", legend=False, fliersize=1)
            ax.set(xlabel="", ylabel="Motor temperature (°C)")
            show(fig)
        st.markdown("**Battery level over time**")
        fig, ax = plt.subplots(figsize=(10, 4))
        sns.lineplot(data=f, x="timestamp", y="battery_pct", hue="robot_id", ax=ax, lw=1)
        ax.set(ylabel="Battery (%)", xlabel="Time")
        ax.legend(ncol=8, fontsize=7)
        show(fig)
    with t5:
        a, b = st.columns(2)
        with a:
            st.markdown("**Wheel slip by floor type**")
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.boxplot(data=f, x="floor_type", y="slip_pct", ax=ax, palette=PALETTE,
                        hue="floor_type", legend=False, fliersize=1)
            ax.set(xlabel="", ylabel="Slip (%)")
            show(fig)
        with b:
            st.markdown("**Slip: floor type × payload class**")
            g = f.assign(payload_class=pd.cut(f["payload_kg"], [-.1, 0.1, 8, 16, 25],
                                              labels=["0", "0-8", "8-16", "16-25"]))
            pv = g.pivot_table(index="floor_type", columns="payload_class",
                               values="slip_pct", aggfunc="mean", observed=True)
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.heatmap(pv, annot=True, fmt=".1f", cmap="YlOrRd", ax=ax)
            ax.set(xlabel="Payload (kg)", ylabel="")
            show(fig)
        st.markdown("**Correlation matrix**")
        cols = ["speed_ms", "speed_err_ms", "traj_err_m", "current_avg_A", "motor_temp_C",
                "power_W", "slip_pct", "payload_kg", "battery_pct"]
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.heatmap(f[cols].corr(), annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax)
        show(fig)


def page_kpis():
    kpi_row()
    st.subheader("KPI table by robot")
    t = KR.round(3)
    st.dataframe(t.style.background_gradient(cmap="Blues", axis=0), use_container_width=True)
    st.download_button("⬇️ Download KPI table", t.to_csv().encode(), "kpi_by_robot.csv",
                       "text/csv")
    a, b = st.columns(2)
    with a:
        st.subheader("Missions per robot")
        fig, ax = plt.subplots(figsize=(6, 3.6))
        sns.barplot(x=KR.index, y=KR["missions_completed"], ax=ax, palette=PALETTE,
                    hue=KR.index, legend=False)
        ax.set(xlabel="", ylabel="Missions")
        show(fig)
    with b:
        st.subheader("Tracking precision")
        fig, ax = plt.subplots(figsize=(6, 3.6))
        d = KR.reset_index().melt("robot_id", ["speed_mae_ms", "traj_err_m"])
        sns.barplot(data=d, x="robot_id", y="value", hue="variable", ax=ax)
        ax.set(xlabel="", ylabel="Error")
        show(fig)
    a, b = st.columns(2)
    with a:
        st.subheader("Battery autonomy (h)")
        fig, ax = plt.subplots(figsize=(6, 3.6))
        sns.barplot(x=KR.index, y=KR["autonomy_h"], ax=ax, palette=PALETTE,
                    hue=KR.index, legend=False)
        ax.set(xlabel="", ylabel="Hours (100% → 20%)")
        show(fig)
    with b:
        st.subheader("Collisions & blockages")
        fig, ax = plt.subplots(figsize=(6, 3.6))
        d = KR.reset_index().melt("robot_id", ["collisions", "blockages"])
        sns.barplot(data=d, x="robot_id", y="value", hue="variable", ax=ax,
                    palette=[DANGER, "#F59E0B"])
        ax.set(xlabel="", ylabel="Count")
        show(fig)
    st.subheader("Pareto of incidents")
    pareto_chart()


def page_conclusions():
    st.subheader("💡 Conclusions & recommendations")
    if len(KR) < 2:
        st.info("Select at least two robots to compare them.")
        return
    cur_med, temp_med = KR["avg_current_A"].median(), KR["avg_motor_temp_C"].median()
    worst = KR["avg_current_A"].idxmax()
    dc = (KR.loc[worst, "avg_current_A"] / cur_med - 1) * 100
    dt = KR.loc[worst, "avg_motor_temp_C"] - temp_med
    de = (KR.loc[worst, "Wh_per_m"] / KR["Wh_per_m"].median() - 1) * 100
    floor_slip = f.groupby("floor_type")["slip_pct"].mean().sort_values(ascending=False)
    ev = f[f["event"].isin(["Collision", "Wheel blockage"])]
    top_inc = ev["robot_id"].value_counts()

    c = st.columns(3)
    kpi_card(c[0], "Most stressed motor", worst, f"+{dc:.0f}% current vs median", DANGER)
    kpi_card(c[1], f"{worst} temperature", f"+{dt:.1f} °C", "vs fleet median", DANGER)
    kpi_card(c[2], f"{worst} energy", f"+{de:.0f}%", "Wh/m vs fleet median", "#F59E0B")
    st.write("")
    st.markdown(f"""
### Key findings
- **Worn motor suspected on {worst}.** It draws **{dc:+.0f}%** more current than the fleet
  median, runs **{dt:+.1f} °C** hotter and consumes **{de:+.0f}%** more energy per metre.
- **Tracking precision:** mean speed error is **{K['speed_mae']:.3f} m/s** and mean
  trajectory error **{K['traj_err']:.3f} m**, which is a good level for a 20 × 15 m workshop.
- **Floor influence:** slip is highest on **{floor_slip.index[0]}**
  ({floor_slip.iloc[0]:.2f}%) and lowest on **{floor_slip.index[-1]}** ({floor_slip.iloc[-1]:.2f}%).
- **Safety:** {K['collisions']} collisions and {K['blockages']} wheel blockages in the
  selection{f"; most affected robot: **{top_inc.index[0]}** ({top_inc.iloc[0]} events)" if len(top_inc) else ""}.
- **Autonomy:** average estimated autonomy is **{K['autonomy_h']:.1f} h** (100 % → 20 %).

### Recommendations
1. 🔧 **Schedule inspection / replacement of the {worst} motor** before failure; add an alert
   when current or temperature exceeds the fleet median by more than 20 %.
2. 🚧 **Reduce speed setpoint or payload on {floor_slip.index[0]}** to limit slip and
   energy waste; consider traction-control tuning.
3. 🔋 **Plan charging returns** at ≈30 % battery to avoid low-battery events and keep
   missions uninterrupted.
4. 🧭 **Review obstacle-avoidance thresholds** (increase detection margin) to cut collisions
   and wheel blockages, following the Pareto chart.
5. 📊 **Keep monitoring** Wh/m, tracking errors and temperature as continuous health KPIs.
""")


{"📊 Dashboard": page_dashboard, "🧹 Data Cleaning": page_cleaning,
 "📈 Visualizations": page_viz, "🎯 KPIs": page_kpis,
 "💡 Conclusions": page_conclusions}[page]()

st.caption("YaneCode Academy · Streamlit project · BEDDIAF Marwa")
