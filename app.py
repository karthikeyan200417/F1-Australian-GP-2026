import streamlit as st
import fastf1 as ff1
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import os

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="🏎️ Ferrari Strategy Autopsy | AUS GP 2026",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    body, .stApp { background-color: #0f0f0f; color: #ffffff; }
    .block-container { padding-top: 1rem; }
    h1, h2, h3 { color: #e10600; font-family: 'Arial Black', sans-serif; }
    .metric-card {
        background: #1a1a1a; border-left: 4px solid #e10600;
        border-radius: 8px; padding: 1rem; margin: 0.3rem 0;
    }
    .stMetric label { color: #aaaaaa !important; }
    .stMetric div { color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# COLORS & CONSTANTS
# ============================================================
COLORS = {
    'RUS': '#27F4D2',
    'ANT': '#00B8A0',
    'LEC': '#E8002D',
    'HAM': '#FF6B6B',
}
FULL_NAMES = {
    'RUS': 'George Russell',
    'ANT': 'Kimi Antonelli',
    'LEC': 'Charles Leclerc',
    'HAM': 'Lewis Hamilton',
}
TEAMS = {
    'RUS': 'Mercedes',
    'ANT': 'Mercedes',
    'LEC': 'Ferrari',
    'HAM': 'Ferrari',
}
DRIVERS = ['RUS', 'ANT', 'LEC', 'HAM']

# ============================================================
# DATA LOADING
# ============================================================
@st.cache_resource(show_spinner=False)
def load_session():
    os.makedirs('/tmp/f1_cache', exist_ok=True)
    ff1.Cache.enable_cache('/tmp/f1_cache')
    race = ff1.get_session(2026, 'Australia', 'R')
    race.load(laps=True, telemetry=True, weather=True)
    return race

@st.cache_data(show_spinner=False)
def get_gap_per_lap(_laps, d1, d2):
    df1 = _laps.pick_drivers(d1)[['LapNumber','LapTime']].copy()
    df2 = _laps.pick_drivers(d2)[['LapNumber','LapTime']].copy()
    df1['Cum1'] = df1['LapTime'].dt.total_seconds().cumsum()
    df2['Cum2'] = df2['LapTime'].dt.total_seconds().cumsum()
    m = df1.merge(df2, on='LapNumber')
    m['Gap'] = m['Cum2'] - m['Cum1']  # positive = d1 ahead of d2
    return m

@st.cache_data(show_spinner=False)
def get_pit_data(_laps, drivers):
    rows = []
    for d in drivers:
        try:
            dl = _laps.pick_drivers(d)
            pits = dl[dl['PitOutTime'].notna()]
            for _, r in pits.iterrows():
                rows.append({
                    'Driver': d,
                    'FullName': FULL_NAMES[d],
                    'Team': TEAMS[d],
                    'PitLap': int(r['LapNumber']),
                    'TyreLife': int(r['TyreLife']) if pd.notna(r['TyreLife']) else None,
                    'Compound': r['Compound'],
                    'Position': int(r['Position']) if pd.notna(r['Position']) else None,
                })
        except:
            pass
    return pd.DataFrame(rows)

@st.cache_data(show_spinner=False)
def get_clean_laps(_laps, driver):
    d = _laps.pick_drivers(driver).pick_accurate().copy()
    d['LapTime_s'] = d['LapTime'].dt.total_seconds()
    d = d[d['LapTime_s'].between(75, 120)]
    return d[['LapNumber','LapTime_s','TyreLife','Compound','Position']]

# ============================================================
# LOAD DATA
# ============================================================
with st.spinner("🔄 Loading 2026 Australian GP Race Data..."):
    try:
        race = load_session()
        laps = race.laps
        st.success("✅ Race data loaded successfully!")
        data_loaded = True
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        data_loaded = False

if not data_loaded:
    st.stop()

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/3/33/F1.svg",
             width=120)
    st.title("🏎️ AUS GP 2026")
    st.markdown("### Ferrari Strategy Autopsy")
    st.divider()

    st.markdown("**Drivers**")
    show_rus = st.checkbox("🔵 George Russell (RUS)", value=True)
    show_ant = st.checkbox("🩵 Kimi Antonelli (ANT)", value=True)
    show_lec = st.checkbox("🔴 Charles Leclerc (LEC)", value=True)
    show_ham = st.checkbox("🟠 Lewis Hamilton (HAM)", value=True)

    active = [d for d, s in zip(DRIVERS, [show_rus, show_ant, show_lec, show_ham]) if s]

    st.divider()
    st.markdown("**Analysis Sections**")
    show_verdict  = st.checkbox("📋 Race Verdict",    value=True)
    show_gap      = st.checkbox("📉 Gap Analysis",    value=True)
    show_position = st.checkbox("🏁 Position Tracker",value=True)
    show_deg      = st.checkbox("⏱️ Tyre Degradation", value=True)
    show_pitstops = st.checkbox("🔧 Pit Stop Timing",  value=True)
    show_tel      = st.checkbox("📡 Telemetry Compare",value=True)
    show_ers      = st.checkbox("⚡ ERS Proxy",        value=True)

# ============================================================
# HEADER
# ============================================================
st.title("🏎️ How Ferrari Lost the 2026 Australian GP")
st.markdown(
    "**Leclerc led the race from Lap 1 — Mercedes took the win with a perfect undercut. "
    "This analysis breaks down every lap, every pit call, every second lost.**"
)
st.divider()

# ============================================================
# RACE VERDICT CARDS
# ============================================================
if show_verdict:
    st.subheader("📋 Race Verdict at a Glance")
    c1, c2, c3, c4 = st.columns(4)
    try:
        result_data = {}
        for d in DRIVERS:
            dl = laps.pick_drivers(d)
            final_pos  = dl['Position'].dropna().iloc[-1]  if not dl.empty else "N/A"
            best_lap   = dl.pick_accurate()['LapTime'].min()
            best_lap_s = best_lap.total_seconds() if pd.notna(best_lap) else None
            laps_led   = len(dl[dl['Position'] == 1])
            pit_laps   = dl[dl['PitOutTime'].notna()]['LapNumber'].tolist()
            result_data[d] = {
                'pos': int(final_pos) if final_pos != "N/A" else "N/A",
                'best': f"{best_lap_s:.3f}s" if best_lap_s else "N/A",
                'led': laps_led,
                'pits': pit_laps
            }

        for col, d in zip([c1, c2, c3, c4], DRIVERS):
            r = result_data[d]
            emoji = "🏆" if r['pos'] == 1 else ("🥈" if r['pos'] == 2 else
                    "🥉" if r['pos'] == 3 else "🏎️")
            col.markdown(f"""
            <div class="metric-card" style="border-color:{COLORS[d]}">
                <h3 style="color:{COLORS[d]};margin:0">{emoji} {d}</h3>
                <p style="color:#aaa;margin:4px 0">{FULL_NAMES[d]}</p>
                <p style="margin:2px 0">P{r['pos']} | Best: {r['best']}</p>
                <p style="margin:2px 0">Laps Led: <b>{r['led']}</b></p>
                <p style="margin:2px 0">Pitted: Lap {r['pits']}</p>
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Verdict cards: {e}")

    st.divider()

# ============================================================
# GAP ANALYSIS
# ============================================================
if show_gap:
    st.subheader("📉 The Moment Ferrari Lost the Lead — Gap Per Lap")

    tab1, tab2, tab3 = st.tabs(
        ["LEC vs RUS (Main Battle)",
         "HAM vs ANT (Mercedes battle)",
         "All 4 Drivers vs Russell"]
    )

    with tab1:
        try:
            gap = get_gap_per_lap(laps, 'LEC', 'RUS')
            pit_df = get_pit_data(laps, ['LEC', 'RUS'])

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=gap['LapNumber'], y=gap['Gap'],
                name='Gap: LEC → RUS',
                line=dict(color='#E8002D', width=3),
                fill='tozeroy',
                fillcolor='rgba(232,0,45,0.12)',
                hovertemplate='Lap %{x}<br>Gap: %{y:.3f}s<extra></extra>'
            ))
            fig.add_hline(y=0, line_dash='dot',
                          line_color='white', opacity=0.5,
                          annotation_text="P1/P2 boundary")

            for _, row in pit_df.iterrows():
                fig.add_vline(
                    x=row['PitLap'],
                    line_dash='dash',
                    line_color=COLORS[row['Driver']],
                    line_width=2,
                    annotation_text=f"{row['Driver']} L{row['PitLap']}",
                    annotation_font_color=COLORS[row['Driver']]
                )

            fig.update_layout(
                title="Gap: Leclerc vs Russell — Positive = LEC ahead",
                xaxis_title="Lap Number",
                yaxis_title="Gap (seconds)",
                template='plotly_dark',
                paper_bgcolor='#0f0f0f',
                plot_bgcolor='#1a1a1a',
                height=420
            )
            st.plotly_chart(fig, use_container_width=True)

            # Auto verdict
            lec_led = gap[gap['Gap'] > 0]
            cross_lap = gap[gap['Gap'] <= 0]['LapNumber'].min()
            if pd.notna(cross_lap):
                st.error(
                    f"❌ **Leclerc led for {len(lec_led)} laps "
                    f"but lost P1 on Lap {int(cross_lap)}** — "
                    f"the pit stop window was the turning point."
                )
        except Exception as e:
            st.warning(f"Gap LEC/RUS: {e}")

    with tab2:
        try:
            gap2 = get_gap_per_lap(laps, 'HAM', 'ANT')
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=gap2['LapNumber'], y=gap2['Gap'],
                name='HAM vs ANT',
                line=dict(color='#FF6B6B', width=3),
                fill='tozeroy',
                fillcolor='rgba(255,107,107,0.12)'
            ))
            fig2.add_hline(y=0, line_dash='dot', line_color='white', opacity=0.5)
            pit_df2 = get_pit_data(laps, ['HAM', 'ANT'])
            for _, row in pit_df2.iterrows():
                fig2.add_vline(
                    x=row['PitLap'],
                    line_dash='dash',
                    line_color=COLORS[row['Driver']],
                    annotation_text=f"{row['Driver']} L{row['PitLap']}"
                )
            fig2.update_layout(
                title="Gap: Hamilton vs Antonelli — Positive = HAM ahead",
                template='plotly_dark',
                paper_bgcolor='#0f0f0f',
                plot_bgcolor='#1a1a1a',
                height=420
            )
            st.plotly_chart(fig2, use_container_width=True)
        except Exception as e:
            st.warning(f"Gap HAM/ANT: {e}")

    with tab3:
        try:
            fig3 = go.Figure()
            for d in [d for d in active if d != 'RUS']:
                gap_d = get_gap_per_lap(laps, d, 'RUS')
                fig3.add_trace(go.Scatter(
                    x=gap_d['LapNumber'], y=gap_d['Gap'],
                    name=f"{d} vs RUS",
                    line=dict(color=COLORS[d], width=2)
                ))
            fig3.add_hline(y=0, line_dash='dot', line_color='white', opacity=0.5,
                           annotation_text="Russell's position")
            fig3.update_layout(
                title="All Drivers Gap to Russell per Lap",
                xaxis_title="Lap", yaxis_title="Gap (s) — Positive = ahead of RUS",
                template='plotly_dark',
                paper_bgcolor='#0f0f0f',
                plot_bgcolor='#1a1a1a',
                height=420
            )
            st.plotly_chart(fig3, use_container_width=True)
        except Exception as e:
            st.warning(f"Multi gap: {e}")

    st.divider()

# ============================================================
# POSITION TRACKER
# ============================================================
if show_position:
    st.subheader("🏁 Position Every Lap — Ferrari Led, Mercedes Won")
    try:
        fig = go.Figure()
        for d in active:
            dl = laps.pick_drivers(d)[['LapNumber','Position']].dropna()
            fig.add_trace(go.Scatter(
                x=dl['LapNumber'], y=dl['Position'],
                name=f"{d} – {FULL_NAMES[d]}",
                line=dict(color=COLORS[d], width=2.5),
                mode='lines+markers',
                marker=dict(size=4)
            ))

        # Highlight Ferrari-led laps
        lec_laps = laps.pick_drivers('LEC')
        lec_p1 = lec_laps[lec_laps['Position'] == 1]['LapNumber']
        if len(lec_p1) > 0:
            fig.add_vrect(
                x0=lec_p1.min(), x1=lec_p1.max(),
                fillcolor='rgba(232,0,45,0.15)',
                line_width=0,
                annotation_text="🔴 Ferrari P1",
                annotation_position="top left",
                annotation_font_color='#E8002D'
            )

        fig.update_yaxes(autorange='reversed', dtick=1, title='Position')
        fig.update_xaxes(title='Lap Number')
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='#0f0f0f',
            plot_bgcolor='#1a1a1a',
            height=480
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Position tracker: {e}")
    st.divider()

# ============================================================
# TYRE DEGRADATION
# ============================================================
if show_deg:
    st.subheader("⏱️ Tyre Degradation — Did Ferrari Stay Out Too Long?")
    try:
        pit_df = get_pit_data(laps, active)
        fig = go.Figure()
        for d in active:
            dl = get_clean_laps(laps, d)
            fig.add_trace(go.Scatter(
                x=dl['LapNumber'], y=dl['LapTime_s'],
                name=f"{d} – {FULL_NAMES[d]}",
                line=dict(color=COLORS[d], width=2),
                mode='lines+markers', marker=dict(size=4),
                text=dl['TyreLife'],
                customdata=dl['Compound'],
                hovertemplate=(
                    f'<b>{d}</b><br>Lap: %{{x}}<br>'
                    'LapTime: %{y:.3f}s<br>'
                    'TyreLife: %{text}<br>'
                    'Compound: %{customdata}<extra></extra>'
                )
            ))

        for _, row in pit_df.iterrows():
            fig.add_vline(
                x=row['PitLap'],
                line_dash='dash',
                line_color=COLORS[row['Driver']],
                opacity=0.8,
                annotation_text=f"{row['Driver']} Pit L{row['PitLap']}",
                annotation_font_color=COLORS[row['Driver']]
            )

        fig.update_layout(
            title="Lap Times per Lap — Pit stops as dashed lines",
            xaxis_title="Lap Number",
            yaxis_title="Lap Time (seconds)",
            template='plotly_dark',
            paper_bgcolor='#0f0f0f',
            plot_bgcolor='#1a1a1a',
            height=480
        )
        st.plotly_chart(fig, use_container_width=True)

        # Degradation rate per driver
        st.markdown("#### 📊 Degradation Rate (seconds/lap per stint)")
        deg_rows = []
        for d in active:
            dl = get_clean_laps(laps, d)
            for comp in dl['Compound'].unique():
                stint = dl[dl['Compound'] == comp].copy()
                if len(stint) > 3:
                    from numpy.polynomial import polynomial as P
                    x = stint['TyreLife'].values
                    y = stint['LapTime_s'].values
                    if len(x) > 1:
                        coef = np.polyfit(x, y, 1)
                        deg_rows.append({
                            'Driver': d, 'Compound': comp,
                            'Deg Rate (s/lap)': round(coef[0], 4),
                            'Laps on Tyre': len(stint)
                        })
        if deg_rows:
            deg_df = pd.DataFrame(deg_rows).sort_values('Deg Rate (s/lap)', ascending=False)
            st.dataframe(
                deg_df.style.background_gradient(
                    subset=['Deg Rate (s/lap)'], cmap='RdYlGn_r'
                ), use_container_width=True
            )
    except Exception as e:
        st.warning(f"Degradation: {e}")
    st.divider()

# ============================================================
# PIT STOP TIMING
# ============================================================
if show_pitstops:
    st.subheader("🔧 Pit Stop Timing — The Smoking Gun")
    try:
        pit_df = get_pit_data(laps, active)
        if not pit_df.empty:
            col1, col2 = st.columns([2, 1])
            with col1:
                fig = px.scatter(
                    pit_df, x='PitLap', y='Driver',
                    color='Driver', color_discrete_map=COLORS,
                    size='TyreLife', text='Compound',
                    title="Pit Stop Laps — Size = Tyre Age at Pit",
                    template='plotly_dark',
                    labels={'PitLap': 'Lap Number', 'Driver': ''}
                )
                fig.update_traces(textposition='top center', marker=dict(opacity=0.9))
                fig.update_layout(
                    paper_bgcolor='#0f0f0f',
                    plot_bgcolor='#1a1a1a',
                    height=350, showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown("#### Pit Summary")
                for _, row in pit_df.iterrows():
                    st.markdown(f"""
                    <div class="metric-card" style="border-color:{COLORS.get(row['Driver'],'#fff')}">
                        <b style="color:{COLORS.get(row['Driver'],'#fff')}">{row['Driver']}</b>
                        <br>Lap: <b>{row['PitLap']}</b>
                        <br>Tyre age: <b>{row['TyreLife']} laps</b>
                        <br>Compound: <b>{row['Compound']}</b>
                        <br>Position at pit: <b>P{row['Position']}</b>
                    </div>
                    """, unsafe_allow_html=True)

            # Strategic verdict
            st.markdown("#### ⚖️ Strategy Verdict")
            if 'LEC' in pit_df['Driver'].values and 'RUS' in pit_df['Driver'].values:
                lec_pit = pit_df[pit_df['Driver']=='LEC']['PitLap'].min()
                rus_pit = pit_df[pit_df['Driver']=='RUS']['PitLap'].min()
                delta = int(lec_pit - rus_pit)
                if delta > 0:
                    st.error(
                        f"🚨 **Undercut confirmed**: Russell pitted {delta} laps "
                        f"BEFORE Leclerc (Lap {int(rus_pit)} vs Lap {int(lec_pit)}). "
                        f"Mercedes built a fresh-tyre gap while Ferrari stayed out on "
                        f"degraded rubber — Leclerc emerged behind and couldn't recover."
                    )
                elif delta < 0:
                    st.warning(
                        f"⚠️ Ferrari pitted {abs(delta)} laps earlier than Russell "
                        f"but lost track position on pit exit."
                    )
                else:
                    st.info("Same-lap pit stops — position lost during pit execution.")
    except Exception as e:
        st.warning(f"Pit stops: {e}")
    st.divider()

# ============================================================
# TELEMETRY COMPARISON
# ============================================================
if show_tel:
    st.subheader("📡 Telemetry — Fresh vs Degraded Tyre")
    driver_tel = st.selectbox(
        "Pick driver for tyre comparison",
        [d for d in active],
        format_func=lambda x: FULL_NAMES[x]
    )
    try:
        pit_df = get_pit_data(laps, [driver_tel])
        pit_lap = int(pit_df['PitLap'].min()) if not pit_df.empty else 20
        dl = laps.pick_drivers(driver_tel)

        lap_fresh = dl[dl['LapNumber'] == 2].iloc[0]
        lap_deg   = dl[dl['LapNumber'] == max(2, pit_lap - 1)].iloc[0]

        tel_f = lap_fresh.get_telemetry().add_distance()
        tel_d = lap_deg.get_telemetry().add_distance()

        fig = make_subplots(
            rows=3, cols=1, shared_xaxes=True,
            subplot_titles=[
                "Speed (km/h)",
                "Throttle (%)",
                "Brake + Gear"
            ]
        )
        for tel, label, opacity in [
            (tel_f, "Lap 2 (Fresh)", 1.0),
            (tel_d, f"Lap {pit_lap-1} (Degraded)", 0.65)
        ]:
            col = COLORS[driver_tel]
            fig.add_trace(go.Scatter(
                x=tel['Distance'], y=tel['Speed'],
                name=label, opacity=opacity,
                line=dict(color=col, width=2,
                          dash='solid' if opacity==1.0 else 'dash')
            ), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=tel['Distance'], y=tel['Throttle'],
                name=label, opacity=opacity,
                line=dict(color=col, width=2,
                          dash='solid' if opacity==1.0 else 'dash'),
                showlegend=False
            ), row=2, col=1)
            fig.add_trace(go.Scatter(
                x=tel['Distance'], y=tel['nGear'],
                name=label, opacity=opacity,
                line=dict(color=col, width=2,
                          dash='solid' if opacity==1.0 else 'dash'),
                showlegend=False
            ), row=3, col=1)

        fig.update_layout(
            title=f"{FULL_NAMES[driver_tel]}: Fresh vs Degraded Tyre Telemetry",
            template='plotly_dark',
            paper_bgcolor='#0f0f0f',
            plot_bgcolor='#1a1a1a',
            height=700
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Telemetry compare: {e}")
    st.divider()

# ============================================================
# ERS PROXY ANALYSIS
# ============================================================
if show_ers:
    st.subheader("⚡ ERS Deployment Proxy — Who Managed Battery Best?")
    try:
        def compute_ers_proxy(tel):
            df = tel.copy().sort_values('Distance').reset_index(drop=True)
            df['Acceleration'] = np.gradient(
                df['Speed'].values,
                df['Time'].dt.total_seconds().values
            )
            from scipy.signal import savgol_filter
            df['AccSmooth'] = savgol_filter(df['Acceleration'], 11, 3) \
                              if len(df) > 11 else df['Acceleration']
            rpm_factor = df['Speed'].mean() / df['RPM'].mean() \
                         if df['RPM'].mean() > 0 else 0.025
            df['SpeedFromRPM'] = df['RPM'] * rpm_factor
            df['ERS_Delta'] = df['Speed'] - df['SpeedFromRPM']
            df['ERS_Deploying']  = (df['ERS_Delta'] > 3) & (df['Throttle'] > 80) & (~df['Brake'])
            df['ERS_Harvesting'] = df['Brake'] | ((df['Throttle'] < 60) & (df['ERS_Delta'] < -2))
            df['SuperClipping']  = (df['Throttle'] > 90) & (df['ERS_Delta'] < -5) & (~df['Brake'])
            df['BoostMode']      = (df['Speed'] > df['Speed'].quantile(0.7)) & \
                                   (df['AccSmooth'] > df['AccSmooth'].quantile(0.85)) & \
                                   (df['Throttle'] > 95)
            return df

        profiles = []
        race_laps = laps.pick_accurate()

        for d in active:
            try:
                lap = race_laps.pick_drivers(d).pick_fastest()
                tel = lap.get_telemetry().add_distance()
                df  = compute_ers_proxy(tel)
                profiles.append({
                    'Driver': d,
                    'Name': FULL_NAMES[d],
                    'Deploy%':    round(df['ERS_Deploying'].mean()*100, 2),
                    'Harvest%':   round(df['ERS_Harvesting'].mean()*100, 2),
                    'SuperClip%': round(df['SuperClipping'].mean()*100, 2),
                    'Boost%':     round(df['BoostMode'].mean()*100, 2),
                    'LapTime_s':  lap['LapTime'].total_seconds()
                })
            except Exception as e:
                st.warning(f"ERS {d}: {e}")

        if profiles:
            prof_df = pd.DataFrame(profiles).sort_values('LapTime_s')

            col1, col2 = st.columns(2)
            with col1:
                fig_bar = px.bar(
                    prof_df.melt(
                        id_vars='Driver',
                        value_vars=['Deploy%','Harvest%','SuperClip%','Boost%']
                    ),
                    x='Driver', y='value', color='variable', barmode='group',
                    color_discrete_sequence=['#27F4D2','#FF8000','#E8002D','#FFFF00'],
                    title="ERS Profile per Driver (Race Best Lap)",
                    template='plotly_dark',
                    labels={'value': 'Time % of Lap', 'variable': ''}
                )
                fig_bar.update_layout(
                    paper_bgcolor='#0f0f0f',
                    plot_bgcolor='#1a1a1a',
                    height=380
                )
                st.plotly_chart(fig_bar, use_container_width=True)

            with col2:
                categories = ['Deploy%','Harvest%','SuperClip%','Boost%']
                fig_radar = go.Figure()
                for _, row in prof_df.iterrows():
                    maxv = prof_df[categories].max()
                    vals = [(row[c]/maxv[c])*10 for c in categories]
                    vals.append(vals[0])
                    fig_radar.add_trace(go.Scatterpolar(
                        r=vals,
                        theta=categories+[categories[0]],
                        fill='toself', name=row['Driver'],
                        line=dict(color=COLORS.get(row['Driver'],'#fff'))
                    ))
                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(range=[0,10])),
                    title="ERS Style Radar",
                    template='plotly_dark',
                    paper_bgcolor='#0f0f0f',
                    height=380
                )
                st.plotly_chart(fig_radar, use_container_width=True)

            st.dataframe(
                prof_df.drop(columns='Name')
                .style.background_gradient(
                    subset=['Deploy%','Harvest%','SuperClip%','Boost%'],
                    cmap='RdYlGn'
                ), use_container_width=True
            )
    except Exception as e:
        st.warning(f"ERS section: {e}")
# ============================================================
# INITIAL SPEED vs TIME — LAP 1 RACE START ANALYSIS
# ============================================================
st.subheader("🚦 Initial Speed vs Time — Race Start & Lap 1 Battle")
st.markdown(
    "The opening seconds of the race define track position. "
    "This shows **who accelerated fastest off the line, "
    "who gained positions and when, and how the ERS boost "
    "played out in the first 60 seconds**."
)

try:
    # ---- LAP 1 TELEMETRY FOR ALL ACTIVE DRIVERS ---------------
    lap1_tels = {}
    for d in active:
        try:
            dl   = laps.pick_drivers(d)
            lap1 = dl[dl['LapNumber'] == 1].iloc[0]
            tel  = lap1.get_telemetry()
            # Time from 0 (relative to session lap start)
            tel['RelTime'] = (
                tel['Time'] - tel['Time'].iloc[0]
            ).dt.total_seconds()
            tel['Distance'] = tel['RelTime'].apply(
                lambda t: tel[tel['RelTime'] <= t]['Speed'].mean() * t / 3.6
            ) if 'Distance' not in tel.columns else tel['Distance']
            tel = tel.add_distance() if 'Distance' not in tel.columns \
                  else tel
            lap1_tels[d] = tel
        except Exception as e:
            st.warning(f"Lap 1 tel {d}: {e}")

    if lap1_tels:

        tab_spd, tab_acc, tab_rpm, tab_full = st.tabs([
            "🚀 Speed vs Time",
            "📈 Acceleration vs Time",
            "🔩 RPM vs Time",
            "📊 Full Panel"
        ])

        # ---- TAB 1: SPEED vs TIME --------------------------------
        with tab_spd:
            fig_sv = go.Figure()
            for d in active:
                if d not in lap1_tels:
                    continue
                df  = lap1_tels[d]
                col = COLORS[d]

                fig_sv.add_trace(go.Scatter(
                    x=df['RelTime'],
                    y=df['Speed'],
                    name=f"{d} – {FULL_NAMES[d]}",
                    line=dict(color=col, width=2.5),
                    hovertemplate=(
                        f'<b>{d}</b><br>'
                        'Time: %{x:.2f}s<br>'
                        'Speed: %{y:.1f} km/h<extra></extra>'
                    )
                ))

            # Annotate key milestones
            for t, label in [(5,'5s'), (10,'10s'), (30,'30s'), (60,'1 min')]:
                fig_sv.add_vline(
                    x=t, line_dash='dot',
                    line_color='#555555', line_width=1,
                    annotation_text=label,
                    annotation_font_color='#888888',
                    annotation_position='top'
                )

            fig_sv.update_layout(
                title="Speed vs Time — Lap 1 (Race Start to End of Lap 1)",
                xaxis_title="Time from Race Start (seconds)",
                yaxis_title="Speed (km/h)",
                template='plotly_dark',
                paper_bgcolor='#0f0f0f',
                plot_bgcolor='#1a1a1a',
                height=480,
                legend=dict(orientation='h', y=1.05)
            )
            st.plotly_chart(fig_sv, use_container_width=True)

            # Speed milestones table
            st.markdown("#### ⏱️ Speed at Key Time Milestones (km/h)")
            milestone_data = []
            for t_mark in [2, 5, 10, 15, 30, 60]:
                row = {'Time (s)': f"{t_mark}s"}
                for d in active:
                    if d not in lap1_tels:
                        row[d] = 'N/A'
                        continue
                    df  = lap1_tels[d]
                    idx = (df['RelTime'] - t_mark).abs().idxmin()
                    row[d] = f"{df.loc[idx,'Speed']:.1f}"
                milestone_data.append(row)

            mile_df = pd.DataFrame(milestone_data).set_index('Time (s)')
            st.dataframe(mile_df, use_container_width=True)

        # ---- TAB 2: ACCELERATION vs TIME -------------------------
        with tab_acc:
            fig_acc = go.Figure()
            for d in active:
                if d not in lap1_tels:
                    continue
                df  = lap1_tels[d].copy()
                col = COLORS[d]

                # Compute acceleration
                df['Accel'] = np.gradient(
                    df['Speed'].values,
                    df['RelTime'].values
                )
                from scipy.signal import savgol_filter
                if len(df) > 11:
                    df['AccelSmooth'] = savgol_filter(df['Accel'], 11, 3)
                else:
                    df['AccelSmooth'] = df['Accel']

                fig_acc.add_trace(go.Scatter(
                    x=df['RelTime'],
                    y=df['AccelSmooth'],
                    name=f"{d} – {FULL_NAMES[d]}",
                    line=dict(color=col, width=2.5),
                    fill='tozeroy',
                    fillcolor=f'rgba({int(col[1:3],16)},{int(col[3:5],16)},{int(col[5:7],16)},0.1)',
                    hovertemplate=(
                        f'<b>{d}</b><br>'
                        'Time: %{x:.2f}s<br>'
                        'Accel: %{y:.2f} m/s²<extra></extra>'
                    )
                ))

            fig_acc.add_hline(
                y=0, line_dash='dash',
                line_color='white', opacity=0.3,
                annotation_text="← Decelerating | Accelerating →"
            )

            # Mark first 10 seconds
            fig_acc.add_vrect(
                x0=0, x1=10,
                fillcolor='rgba(255,255,0,0.05)',
                line_width=0,
                annotation_text="🚦 Launch Phase (0–10s)",
                annotation_position='top left',
                annotation_font_color='#FFFF88'
            )

            fig_acc.update_layout(
                title="Acceleration vs Time — Launch Phase & ERS Boost Bursts",
                xaxis_title="Time from Race Start (seconds)",
                yaxis_title="Acceleration (m/s²)",
                template='plotly_dark',
                paper_bgcolor='#0f0f0f',
                plot_bgcolor='#1a1a1a',
                height=480,
                legend=dict(orientation='h', y=1.05)
            )
            st.plotly_chart(fig_acc, use_container_width=True)

            # Peak acceleration stats
            st.markdown("#### 🏆 Peak Acceleration Stats — Lap 1")
            acc_stats = []
            for d in active:
                if d not in lap1_tels:
                    continue
                df   = lap1_tels[d].copy()
                df['Accel'] = np.gradient(df['Speed'].values, df['RelTime'].values)
                if len(df) > 11:
                    from scipy.signal import savgol_filter
                    df['AccelSmooth'] = savgol_filter(df['Accel'], 11, 3)
                else:
                    df['AccelSmooth'] = df['Accel']

                launch_df = df[df['RelTime'] <= 10]
                acc_stats.append({
                    'Driver':         d,
                    'Name':           FULL_NAMES[d],
                    'Peak Launch (m/s²)': round(launch_df['AccelSmooth'].max(), 3),
                    'Time to 100 km/h (s)': round(
                        df[df['Speed'] >= 100]['RelTime'].min(), 2
                    ) if not df[df['Speed'] >= 100].empty else 'N/A',
                    'Time to 200 km/h (s)': round(
                        df[df['Speed'] >= 200]['RelTime'].min(), 2
                    ) if not df[df['Speed'] >= 200].empty else 'N/A',
                    'Time to 250 km/h (s)': round(
                        df[df['Speed'] >= 250]['RelTime'].min(), 2
                    ) if not df[df['Speed'] >= 250].empty else 'N/A',
                })

            acc_df = pd.DataFrame(acc_stats).set_index('Driver')
            st.dataframe(
                acc_df.style.highlight_min(
                    subset=['Time to 100 km/h (s)',
                            'Time to 200 km/h (s)',
                            'Time to 250 km/h (s)'],
                    color='rgba(39,244,210,0.3)'
                ).highlight_max(
                    subset=['Peak Launch (m/s²)'],
                    color='rgba(232,0,45,0.3)'
                ),
                use_container_width=True
            )

        # ---- TAB 3: RPM vs TIME ----------------------------------
        with tab_rpm:
            fig_rpm = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                subplot_titles=[
                    "RPM vs Time — Gear shift points visible as RPM drops",
                    "Gear vs Time — When each driver upshifted"
                ],
                vertical_spacing=0.1
            )
            for d in active:
                if d not in lap1_tels:
                    continue
                df  = lap1_tels[d]
                col = COLORS[d]

                fig_rpm.add_trace(go.Scatter(
                    x=df['RelTime'], y=df['RPM'],
                    name=f"{d}", line=dict(color=col, width=2),
                    legendgroup=d
                ), row=1, col=1)

                fig_rpm.add_trace(go.Scatter(
                    x=df['RelTime'], y=df['nGear'],
                    name=d, line=dict(color=col, width=2),
                    legendgroup=d, showlegend=False
                ), row=2, col=1)

            fig_rpm.update_layout(
                title="RPM & Gear vs Time — Powertrain Behaviour Off the Line",
                template='plotly_dark',
                paper_bgcolor='#0f0f0f',
                plot_bgcolor='#1a1a1a',
                height=580
            )
            fig_rpm.update_yaxes(title_text="RPM", row=1, col=1)
            fig_rpm.update_yaxes(title_text="Gear", dtick=1, row=2, col=1)
            fig_rpm.update_xaxes(title_text="Time (s)", row=2, col=1)
            st.plotly_chart(fig_rpm, use_container_width=True)

        # ---- TAB 4: FULL PANEL -----------------------------------
        with tab_full:
            fig_full = make_subplots(
                rows=6, cols=1,
                shared_xaxes=True,
                subplot_titles=[
                    "Speed (km/h)",
                    "Acceleration (m/s²) — ERS burst detection",
                    "RPM — Powertrain load",
                    "Throttle (%) — Power application",
                    "Gear — Shift strategy",
                    "🏁 Race Position — How Leclerc jumped to P1"
                ],
                vertical_spacing=0.04,
                row_heights=[0.25, 0.18, 0.15, 0.14, 0.14, 0.14]
            )

            # ---- Build position timeline from lap data ----------------
            # Map each driver's position changes to telemetry time axis
            position_timelines = {}
            for d in active:
                try:
                    dl = laps.pick_drivers(d)
                    # Get first 5 laps to capture early position changes
                    early = dl[dl['LapNumber'] <= 5][
                        ['LapNumber', 'Position', 'LapTime']
                    ].dropna().copy()
                    early['CumTime'] = early['LapTime'].dt.total_seconds().cumsum()
                    # Prepend t=0, position = grid position
                    grid_pos = {
                        'RUS': 1, 'ANT': 2, 'LEC': 4, 'HAM': 7
                    }  # fallback grid positions
                    position_timelines[d] = {
                        'times': [0] + early['CumTime'].tolist(),
                        'positions': [grid_pos.get(d, 10)] + early['Position'].tolist()
                    }
                except Exception as e:
                    st.warning(f"Position timeline {d}: {e}")

            for d in active:
                if d not in lap1_tels:
                    continue
                df  = lap1_tels[d].copy()
                col = COLORS[d]

                df['Accel'] = np.gradient(
                    df['Speed'].values, df['RelTime'].values
                )
                from scipy.signal import savgol_filter
                df['AccelSmooth'] = savgol_filter(df['Accel'], 11, 3) \
                                    if len(df) > 11 else df['Accel']

                # Row 1: Speed
                fig_full.add_trace(go.Scatter(
                    x=df['RelTime'], y=df['Speed'],
                    name=d, line=dict(color=col, width=2.5),
                    legendgroup=d,
                    hovertemplate=(
                        f'<b>{d}</b><br>Time: %{{x:.1f}}s<br>'
                        'Speed: %{y:.1f} km/h<extra></extra>'
                    )
                ), row=1, col=1)

                # Row 2: Acceleration
                fig_full.add_trace(go.Scatter(
                    x=df['RelTime'], y=df['AccelSmooth'],
                    name=d, line=dict(color=col, width=2),
                    fill='tozeroy',
                    fillcolor=f'rgba({int(col[1:3],16)},{int(col[3:5],16)},{int(col[5:7],16)},0.08)',
                    legendgroup=d, showlegend=False
                ), row=2, col=1)

                # Row 3: RPM
                fig_full.add_trace(go.Scatter(
                    x=df['RelTime'], y=df['RPM'],
                    name=d, line=dict(color=col, width=2),
                    legendgroup=d, showlegend=False
                ), row=3, col=1)

                # Row 4: Throttle
                fig_full.add_trace(go.Scatter(
                    x=df['RelTime'], y=df['Throttle'],
                    name=d, line=dict(color=col, width=2),
                    legendgroup=d, showlegend=False
                ), row=4, col=1)

                # Row 5: Gear
                fig_full.add_trace(go.Scatter(
                    x=df['RelTime'], y=df['nGear'],
                    name=d, line=dict(color=col, width=2),
                    legendgroup=d, showlegend=False
                ), row=5, col=1)

                # Row 6: POSITION (step chart)
                if d in position_timelines:
                    pt = position_timelines[d]

                    # Clip to lap 1 time window
                    max_time = df['RelTime'].max()
                    times_clipped = [t for t in pt['times'] if t <= max_time + 30]
                    pos_clipped   = pt['positions'][:len(times_clipped)]

                    fig_full.add_trace(go.Scatter(
                        x=times_clipped,
                        y=pos_clipped,
                        name=d,
                        mode='lines+markers+text',
                        line=dict(color=col, width=3, shape='hv'),  # step shape
                        marker=dict(size=10, color=col,
                                    line=dict(color='white', width=2)),
                        text=[f"P{p}" for p in pos_clipped],
                        textposition='top center',
                        textfont=dict(color=col, size=11, family='Arial Black'),
                        legendgroup=d, showlegend=False,
                        hovertemplate=(
                            f'<b>{d}</b><br>'
                            'Time: %{x:.1f}s<br>'
                            'Position: P%{y}<extra></extra>'
                        )
                    ), row=6, col=1)

                    # Annotate position changes with driver label at start
                    if pos_clipped:
                        fig_full.add_annotation(
                            x=times_clipped[0],
                            y=pos_clipped[0],
                            text=f" {d} P{pos_clipped[0]}",
                            font=dict(color=col, size=10),
                            showarrow=False,
                            xref='x6', yref='y6',
                            xanchor='left'
                        )

            # ---- Highlight T1 position change moment ------------------
            # Ferrari made their move in first ~8–12 seconds
            fig_full.add_vrect(
                x0=0, x1=12,
                fillcolor='rgba(255,255,0,0.04)',
                line_width=0,
                annotation_text="🚦 T1 Battle",
                annotation_position='top left',
                annotation_font_color='#FFFF88',
                row=6, col=1
            )

            # Accent line at Lap 1 end (approx)
            lap1_duration = lap1_tels.get('LEC', pd.DataFrame()).get(
                'RelTime', pd.Series([90])
            ).max()

            fig_full.add_vline(
                x=lap1_duration,
                line_dash='dash', line_color='#555',
                line_width=1,
                annotation_text="Lap 1 ends",
                annotation_font_color='#888'
            )

            # ---- Reference lines --------------------------------------
            fig_full.add_hline(
                y=0, row=2, col=1,
                line_dash='dash', line_color='#333',
                opacity=0.6
            )
            fig_full.add_vrect(
                x0=0, x1=10,
                fillcolor='rgba(255,255,0,0.04)',
                line_width=0,
                annotation_text="🚦 Launch",
                annotation_position='top left',
                annotation_font_color='#FFFF88',
                row=1, col=1
            )

            # ---- Layout -----------------------------------------------
            fig_full.update_yaxes(title_text="km/h",   row=1, col=1)
            fig_full.update_yaxes(title_text="m/s²",   row=2, col=1)
            fig_full.update_yaxes(title_text="RPM",    row=3, col=1)
            fig_full.update_yaxes(title_text="%",      row=4, col=1)
            fig_full.update_yaxes(title_text="Gear",   dtick=1, row=5, col=1)
            fig_full.update_yaxes(
                title_text="Pos",
                autorange='reversed',   # P1 at top
                dtick=1,
                range=[8, 0],           # show P1-P8
                row=6, col=1
            )
            fig_full.update_xaxes(title_text="Time from Race Start (seconds)", row=6, col=1)

            fig_full.update_layout(
                title="🏁 Full Lap 1 Telemetry Panel — All 4 Drivers",
                template='plotly_dark',
                paper_bgcolor='#0f0f0f',
                plot_bgcolor='#1a1a1a',
                height=1100,
                legend=dict(orientation='h', y=1.02)
            )
            st.plotly_chart(fig_full, use_container_width=True)

            # ---- Position narrative callout ---------------------------
            st.markdown("#### 📍 Position Change Narrative")
            col1, col2 = st.columns(2)
            with col1:
                st.error("""
                🔴 **Leclerc (LEC)**
                - **Grid: P4** → T1 → **P1** in ~8 seconds
                - Held P1 for majority of race
                - Dropped to P3 after pit stop sequence
                """)
                st.warning("""
                🟠 **Hamilton (HAM)**
                - **Grid: P7** → gained positions early
                - Finished P4 — blocked by Leclerc
                """)
            with col2:
                st.success("""
                🔵 **Russell (RUS)**
                - **Grid: P1 (Pole)**
                - Lost P1 at T1 to Leclerc
                - Regained lead via undercut pit stop
                - Won the race ✅
                """)
                st.info("""
                🩵 **Antonelli (ANT)**
                - **Grid: P2**
                - Ran clean race in P2 behind Russell
                - Finished P2 — Mercedes 1-2 ✅
                """)


        # ---- SPEED DELTA SCATTER: WHO WAS FASTEST WHEN ----------
        st.markdown("#### 🏆 Speed Advantage — Who Led at Each Time Point?")
        # Find who has highest speed at each 0.5s interval
        time_points = np.arange(0, 60, 0.5)
        leader_data = []
        for t in time_points:
            best_spd  = -1
            best_drv  = None
            for d in active:
                if d not in lap1_tels:
                    continue
                df  = lap1_tels[d]
                idx = (df['RelTime'] - t).abs().idxmin()
                spd = df.loc[idx, 'Speed']
                if spd > best_spd:
                    best_spd = spd
                    best_drv = d
            leader_data.append({'Time': t, 'Leader': best_drv, 'Speed': best_spd})

        lead_df = pd.DataFrame(leader_data)
        fig_lead = px.scatter(
            lead_df, x='Time', y='Speed',
            color='Leader',
            color_discrete_map=COLORS,
            title="Speed Leader at Each 0.5s — Who Had Most Pace on Lap 1?",
            labels={
                'Time': 'Time from Start (s)',
                'Speed': 'Speed (km/h)',
                'Leader': 'Fastest Driver'
            },
            template='plotly_dark',
            height=380
        )
        fig_lead.update_layout(
            paper_bgcolor='#0f0f0f',
            plot_bgcolor='#1a1a1a'
        )
        st.plotly_chart(fig_lead, use_container_width=True)

        # Time led stats
        st.markdown("#### ⏱️ Speed Leadership — % of First 60 Seconds")
        lead_counts = lead_df['Leader'].value_counts(normalize=True) * 100
        c1, c2, c3, c4 = st.columns(4)
        for col_w, d in zip([c1, c2, c3, c4], active):
            pct = lead_counts.get(d, 0)
            col_w.markdown(f"""
            <div class="metric-card" style="border-color:{COLORS[d]}">
                <h4 style="color:{COLORS[d]};margin:0">{d}</h4>
                <p style="color:#aaa;font-size:11px">{FULL_NAMES[d]}</p>
                <p style="font-size:28px;font-weight:bold;margin:4px 0">
                    {pct:.1f}%
                </p>
                <p style="color:#aaa;font-size:11px">of first 60s had highest speed</p>
            </div>
            """, unsafe_allow_html=True)

except Exception as e:
    st.warning(f"Initial speed section: {e}")

st.divider()

# ============================================================
# T1 APPROACH — PACE, POWER & ENERGY
# ============================================================
st.subheader("🏁 Pace, Power & Energy — Approach to Turn 1")
st.markdown(
    "Albert Park Turn 1 is the critical first braking zone after the "
    "start/finish straight — **the highest ERS deployment point of the lap**. "
    "This shows who carried most speed, deployed most battery, and braked latest."
)

try:
    # ---- T1 DISTANCE WINDOW --------------------------------
    # At Albert Park, T1 braking zone starts ~150m into the lap
    # Pit straight (pre-T1) = 0 → ~300m from start line
    T1_START = 0       # Start of lap (after S/F line)
    T1_END   = 400     # Past braking point of T1

    race_best_laps = laps.pick_accurate()

    # Collect telemetry slices for all active drivers
    t1_tels = {}
    for d in active:
        try:
            lap = race_best_laps.pick_drivers(d).pick_fastest()
            tel = lap.get_telemetry().add_distance()
            t1_tels[d] = tel[tel['Distance'].between(T1_START, T1_END)].copy()
        except Exception as e:
            st.warning(f"T1 telemetry {d}: {e}")

    if t1_tels:

        # ---- SUBPLOT: Speed / ERS Delta / Throttle / Brake ----
        fig_t1 = make_subplots(
            rows=4, cols=1,
            shared_xaxes=True,
            subplot_titles=[
                "🚀 Speed (km/h) — Who carries most speed to T1?",
                "⚡ ERS Delta (Speed − RPM proxy) — Battery deployment",
                "🎮 Throttle % — Power application on approach",
                "🛑 Brake — Braking point into T1 (earliest = left of graph)"
            ],
            vertical_spacing=0.07,
            row_heights=[0.35, 0.25, 0.2, 0.2]
        )

        for d in active:
            if d not in t1_tels:
                continue
            df = t1_tels[d].copy()
            col = COLORS[d]

            # ERS proxy
            rpm_factor = df['Speed'].mean() / df['RPM'].mean() \
                         if df['RPM'].mean() > 0 else 0.025
            df['SpeedFromRPM'] = df['RPM'] * rpm_factor
            df['ERS_Delta']    = df['Speed'] - df['SpeedFromRPM']

            # Row 1: Speed
            fig_t1.add_trace(go.Scatter(
                x=df['Distance'], y=df['Speed'],
                name=f"{d}", line=dict(color=col, width=2.5),
                legendgroup=d,
                hovertemplate=f'<b>{d}</b><br>Dist: %{{x:.0f}}m<br>Speed: %{{y:.1f}} km/h<extra></extra>'
            ), row=1, col=1)

            # Row 2: ERS Delta
            fig_t1.add_trace(go.Scatter(
                x=df['Distance'], y=df['ERS_Delta'],
                name=d, line=dict(color=col, width=2),
                fill='tozeroy',
                fillcolor=f'rgba({int(col[1:3],16)},{int(col[3:5],16)},{int(col[5:7],16)},0.1)',
                legendgroup=d, showlegend=False,
                hovertemplate=f'<b>{d}</b><br>ERS Delta: %{{y:.2f}} km/h<extra></extra>'
            ), row=2, col=1)

            # Row 3: Throttle
            fig_t1.add_trace(go.Scatter(
                x=df['Distance'], y=df['Throttle'],
                name=d, line=dict(color=col, width=2),
                legendgroup=d, showlegend=False
            ), row=3, col=1)

            # Row 4: Brake
            fig_t1.add_trace(go.Scatter(
                x=df['Distance'], y=df['Brake'].astype(int) * 100,
                name=d, line=dict(color=col, width=2),
                fill='tozeroy',
                fillcolor=f'rgba({int(col[1:3],16)},{int(col[3:5],16)},{int(col[5:7],16)},0.15)',
                legendgroup=d, showlegend=False
            ), row=4, col=1)

        # Reference lines
        fig_t1.add_hline(
            y=0, row=2, col=1,
            line_dash='dash', line_color='white', opacity=0.3,
            annotation_text="ICE-only baseline",
            annotation_font_color='#888888'
        )

        fig_t1.update_layout(
            title="⚡ T1 Approach: Full Breakdown (0–400m from Start Line)",
            template='plotly_dark',
            paper_bgcolor='#0f0f0f',
            plot_bgcolor='#1a1a1a',
            height=800,
            legend=dict(orientation='h', y=1.03)
        )
        fig_t1.update_yaxes(title_text="km/h",   row=1, col=1)
        fig_t1.update_yaxes(title_text="Δ km/h", row=2, col=1)
        fig_t1.update_yaxes(title_text="%",       row=3, col=1)
        fig_t1.update_yaxes(title_text="On/Off",  row=4, col=1)
        fig_t1.update_xaxes(title_text="Distance from Start Line (m)", row=4, col=1)
        st.plotly_chart(fig_t1, use_container_width=True)

        # ---- METRIC CARDS: T1 KEY STATS -------------------------
        st.markdown("#### 📊 T1 Approach — Key Stats per Driver")
        cols = st.columns(len(active))
        for col_widget, d in zip(cols, active):
            if d not in t1_tels:
                continue
            df = t1_tels[d].copy()
            rpm_factor = df['Speed'].mean() / df['RPM'].mean() \
                         if df['RPM'].mean() > 0 else 0.025
            df['ERS_Delta'] = df['Speed'] - df['RPM'] * rpm_factor

            max_speed   = df['Speed'].max()
            max_ers     = df['ERS_Delta'].max()
            avg_throttle= df['Throttle'].mean()

            # Braking point: first distance where Brake == True
            brake_rows  = df[df['Brake'] == True]
            brake_dist  = brake_rows['Distance'].min() if not brake_rows.empty else None

            # Speed at braking point
            brake_speed = df[df['Brake'] == True]['Speed'].iloc[0] \
                          if not brake_rows.empty else None

            # ERS deployment % of T1 approach
            deploy_pct  = (df['ERS_Delta'] > 3).mean() * 100

            col_widget.markdown(f"""
            <div class="metric-card" style="border-color:{COLORS[d]}">
                <h4 style="color:{COLORS[d]};margin:0">{d}</h4>
                <p style="color:#aaa;font-size:12px;margin:2px 0">{FULL_NAMES[d]}</p>
                <hr style="border-color:#333;margin:6px 0">
                <p style="margin:3px 0">🚀 Max Speed<br>
                   <b style="font-size:18px">{max_speed:.1f} km/h</b></p>
                <p style="margin:3px 0">⚡ Peak ERS Boost<br>
                   <b style="font-size:18px">+{max_ers:.1f} km/h</b></p>
                <p style="margin:3px 0">🎮 Avg Throttle<br>
                   <b style="font-size:18px">{avg_throttle:.1f}%</b></p>
                <p style="margin:3px 0">🛑 Brake Point<br>
                   <b style="font-size:18px">{f'{brake_dist:.0f}m' if brake_dist else 'N/A'}</b></p>
                <p style="margin:3px 0">🏎️ Speed at Brake<br>
                   <b style="font-size:18px">{f'{brake_speed:.1f} km/h' if brake_speed else 'N/A'}</b></p>
                <p style="margin:3px 0">🔋 ERS Active %<br>
                   <b style="font-size:18px">{deploy_pct:.1f}%</b></p>
            </div>
            """, unsafe_allow_html=True)

        # ---- BRAKING COMPARISON BAR CHART -----------------------
        st.markdown("#### 🛑 Latest Braking Point into T1 — Who Brakes Latest?")
        brake_data = []
        for d in active:
            if d not in t1_tels:
                continue
            df = t1_tels[d]
            brake_rows = df[df['Brake'] == True]
            if not brake_rows.empty:
                brake_data.append({
                    'Driver':     d,
                    'Name':       FULL_NAMES[d],
                    'BrakeDist':  brake_rows['Distance'].min(),
                    'BrakeSpeed': brake_rows['Speed'].iloc[0]
                })

        if brake_data:
            brake_df = pd.DataFrame(brake_data).sort_values(
                'BrakeDist', ascending=False
            )
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                fig_brake = px.bar(
                    brake_df, x='Driver', y='BrakeDist',
                    color='Driver',
                    color_discrete_map=COLORS,
                    title="Braking Point Distance (m) — Higher = Later Braking",
                    text='BrakeDist',
                    template='plotly_dark',
                    labels={'BrakeDist': 'Distance (m)', 'Driver': ''}
                )
                fig_brake.update_traces(
                    texttemplate='%{text:.0f}m', textposition='outside'
                )
                fig_brake.update_layout(
                    paper_bgcolor='#0f0f0f',
                    plot_bgcolor='#1a1a1a',
                    height=380, showlegend=False
                )
                st.plotly_chart(fig_brake, use_container_width=True)

            with col_b2:
                fig_speed = px.bar(
                    brake_df, x='Driver', y='BrakeSpeed',
                    color='Driver',
                    color_discrete_map=COLORS,
                    title="Speed at Braking Point (km/h) — Confidence into T1",
                    text='BrakeSpeed',
                    template='plotly_dark',
                    labels={'BrakeSpeed': 'Speed (km/h)', 'Driver': ''}
                )
                fig_speed.update_traces(
                    texttemplate='%{text:.1f}', textposition='outside'
                )
                fig_speed.update_layout(
                    paper_bgcolor='#0f0f0f',
                    plot_bgcolor='#1a1a1a',
                    height=380, showlegend=False
                )
                st.plotly_chart(fig_speed, use_container_width=True)

            # Verdict
            latest_braker = brake_df.iloc[0]['Driver']
            earliest_braker = brake_df.iloc[-1]['Driver']
            gap_m = brake_df.iloc[0]['BrakeDist'] - brake_df.iloc[-1]['BrakeDist']
            st.info(
                f"🏆 **{FULL_NAMES[latest_braker]} brakes latest** into T1 "
                f"({brake_df.iloc[0]['BrakeDist']:.0f}m) — "
                f"{gap_m:.0f}m later than {FULL_NAMES[earliest_braker]} "
                f"({brake_df.iloc[-1]['BrakeDist']:.0f}m). "
                f"Later braking = higher mechanical confidence + Override Mode activation."
            )

        # ---- ERS DEPLOYMENT COMPARISON AREA CHART ---------------
        st.markdown("#### ⚡ ERS Energy Deployed on T1 Straight — Distance-by-Distance")
        fig_ers_area = go.Figure()
        for d in active:
            if d not in t1_tels:
                continue
            df = t1_tels[d].copy()
            rpm_factor  = df['Speed'].mean() / df['RPM'].mean() \
                          if df['RPM'].mean() > 0 else 0.025
            df['ERS_Delta'] = df['Speed'] - df['RPM'] * rpm_factor
            col = COLORS[d]
            fig_ers_area.add_trace(go.Scatter(
                x=df['Distance'], y=df['ERS_Delta'],
                name=f"{d} – {FULL_NAMES[d]}",
                line=dict(color=col, width=2.5),
                fill='tozeroy',
                fillcolor=f'rgba({int(col[1:3],16)},{int(col[3:5],16)},{int(col[5:7],16)},0.12)',
                hovertemplate=(
                    f'<b>{d}</b><br>'
                    'Distance: %{x:.0f}m<br>'
                    'ERS Boost: %{y:.2f} km/h<extra></extra>'
                )
            ))

        fig_ers_area.add_hline(
            y=0, line_dash='dash', line_color='white', opacity=0.4,
            annotation_text="← Harvesting | Deploying →",
            annotation_font_color='#888'
        )
        fig_ers_area.update_layout(
            title="ERS Delta on T1 Approach — Positive = Deploying, Negative = Harvesting/Super-clipping",
            xaxis_title="Distance from Start Line (m)",
            yaxis_title="ERS Speed Boost (km/h)",
            template='plotly_dark',
            paper_bgcolor='#0f0f0f',
            plot_bgcolor='#1a1a1a',
            height=400
        )
        st.plotly_chart(fig_ers_area, use_container_width=True)

except Exception as e:
    st.warning(f"T1 analysis: {e}")

st.divider()


# ============================================================
# FOOTER
# ============================================================
st.divider()
st.markdown("""
<div style='text-align:center;color:#555;font-size:12px'>
    🏎️ Built with FastF1 + Streamlit + Plotly &nbsp;|&nbsp;
    2026 Australian GP Data &nbsp;|&nbsp;
    Analysis by Karthikeyan L
</div>
""", unsafe_allow_html=True)
