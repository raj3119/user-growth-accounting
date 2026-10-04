import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pipeline import (
    load_sets,
    process_growth_accounting,
    cohort_retention,
    single_week_share,
)

st.set_page_config(page_title="User Growth Accounting & PMF", layout="wide")

st.title("User Growth Accounting & PMF Validation")
st.caption("Weekly Active Users (WAU) Decomposition & Quick Ratio Analysis")

# 1. Sidebar Controls
st.sidebar.header("Data Ingestion")
uploaded_file = st.sidebar.file_uploader(
    "Upload Weekly Active Users (.xls / .xlsx)",
    type=["xls", "xlsx"],
)

# Button to control execution explicitly
process_btn = st.sidebar.button("Process & Run Pipeline", type="primary")

# Initialize session state so data persists between tab clicks
if "pipeline_data" not in st.session_state:
    st.session_state.pipeline_data = None

# If user clicks button OR running for the first time with default data
if process_btn or st.session_state.pipeline_data is None:
    data_source = uploaded_file if uploaded_file is not None else "Active Users - Growth Accounting.xls"
    try:
        with st.spinner("Processing growth accounting identities..."):
            weeks, active_sets = load_sets(data_source)
            df_metrics = process_growth_accounting(weeks, active_sets)
            cohort = cohort_retention(weeks, active_sets)
            one_week = single_week_share(weeks, active_sets)
            st.session_state.pipeline_data = {
                "df_metrics": df_metrics,
                "cohort": cohort,
                "one_week": one_week,
                "filename": uploaded_file.name if uploaded_file else "Default (Active Users - Growth Accounting.xls)",
            }
        st.sidebar.success(f"Loaded: {st.session_state.pipeline_data['filename']}")
    except Exception as e:
        st.error(f"Error processing dataset: {e}")
        st.stop()

# Retrieve active pipeline results
df_metrics = st.session_state.pipeline_data["df_metrics"]
cohort = st.session_state.pipeline_data["cohort"]
one_week = st.session_state.pipeline_data["one_week"]

# 2. Executive KPI Summary Cards
latest = df_metrics.iloc[-1]
avg_qr = df_metrics["quick_ratio"].dropna().mean()
avg_ret = df_metrics["retention_rate"].dropna().mean()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(f"Current WAU ({latest['week']})", f"{int(latest['wau']):,}")
with col2:
    qr_val = latest["quick_ratio"] if pd.notnull(latest["quick_ratio"]) else 0.0
    st.metric(
        "Latest Quick Ratio",
        f"{qr_val:.2f}",
        delta=f"{qr_val - 1:+.2f} vs break-even (1.0)",
    )
with col3:
    st.metric(f"Avg Quick Ratio (w2–{latest['week']})", f"{avg_qr:.2f}")
with col4:
    st.metric("Avg Weekly Retention", f"{avg_ret:.1f}%")

st.divider()

# 3. Three-Tab Presentation
tab_chart, tab_data, tab_insights = st.tabs([
    "📈 Growth Accounting Visuals",
    "📋 Accounting Matrix Table",
    "💡 Product & PMF Insights",
])

# ----------------- TAB 1: CHARTS -----------------
with tab_chart:
    st.subheader("Weekly Growth Accounting Decomposition")

    fig, (ax1, ax2) = plt.subplots(
        2, 1,
        figsize=(15, 8),
        sharex=True,
        gridspec_kw={"height_ratios": [2.5, 1]},
    )

    weeks_idx = range(len(df_metrics))
    labels = df_metrics["week"]

    # Positive stack: Retained + New + Resurrected
    ax1.bar(weeks_idx[1:], df_metrics["retained"][1:], label="Retained", color="#2b5c8f", width=0.8)
    ax1.bar(weeks_idx[1:], df_metrics["new"][1:], bottom=df_metrics["retained"][1:], label="New", color="#4caf50", width=0.8)
    ax1.bar(
        weeks_idx[1:],
        df_metrics["resurrected"][1:],
        bottom=(df_metrics["retained"][1:] + df_metrics["new"][1:]),
        label="Resurrected",
        color="#ff9800",
        width=0.8,
    )

    # Negative stack: Churned
    ax1.bar(weeks_idx[1:], -df_metrics["churned"][1:], label="Churned", color="#e53935", width=0.8)

    # WAU line
    ax1.plot(weeks_idx[1:], df_metrics["wau"][1:], color="black", marker="o", linewidth=1.5, markersize=3, label="WAU (Net Active)")
    ax1.axhline(0, color="gray", linewidth=0.8, linestyle="--")
    ax1.set_ylabel("User Volume")
    ax1.legend(loc="upper left", ncol=5)
    ax1.grid(axis="y", alpha=0.3)

    # Bottom subplot: Quick Ratio (+ rolling average)
    qr = df_metrics["quick_ratio"].astype(float)
    ax2.plot(weeks_idx[1:], qr[1:], color="#673ab7", marker="s", linewidth=1.8, markersize=4, label="Quick Ratio")
    
    rolling_window = min(4, max(1, len(df_metrics) // 4))
    ax2.plot(weeks_idx[1:], qr.rolling(rolling_window).mean()[1:], color="#ff9800", linewidth=2.5, label=f"{rolling_window}-week average")
    ax2.axhline(1.0, color="red", linestyle="--", linewidth=1.2, label="Stability Benchmark (QR = 1.0)")
    ax2.set_ylabel("Quick Ratio")
    ax2.set_xlabel("Week")
    ax2.set_xticks(list(weeks_idx[1::2]))
    ax2.set_xticklabels(list(labels[1::2]), rotation=45)
    ax2.legend(loc="upper right")
    ax2.grid(alpha=0.3)

    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # New-user retention curve (safely rendered)
    if cohort:
        st.subheader("New-User Cohort Retention Curve")
        fig2, ax = plt.subplots(figsize=(8, 3.5))
        ax.plot(list(cohort.keys()), list(cohort.values()), color="#2b5c8f", marker="o")
        
        # Only annotate milestones that exist in the active dataset
        for k in (1, 4, 8, 12):
            if k in cohort:
                ax.annotate(f"{cohort[k]:.0f}%", (k, cohort[k]), textcoords="offset points", xytext=(5, 6))
                
        ax.set_ylim(0, 105)
        ax.set_xlabel("Weeks since first seen")
        ax.set_ylabel("% of cohort active")
        ax.grid(alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)

# ----------------- TAB 2: TABLE & DOWNLOAD -----------------
with tab_data:
    st.subheader("Calculated Weekly Growth Accounting Matrix")
    st.dataframe(df_metrics, hide_index=True, use_container_width=True)

    csv_data = df_metrics.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Full Growth Accounting Matrix (CSV)",
        data=csv_data,
        file_name="weekly_growth_accounting_metrics.csv",
        mime="text/csv",
    )

# ----------------- TAB 3: INSIGHTS -----------------
with tab_insights:
    # Safely extract dynamic cohort milestones without crashing on short files
    c1_str = f"{cohort[1]:.0f}%" if 1 in cohort else "N/A"
    c4_str = f"{cohort[4]:.0f}%" if 4 in cohort else "N/A"
    c12_str = f"{cohort[12]:.0f}%" if 12 in cohort else "N/A"

    st.markdown(f"""
    ### Executive PMF Diagnostic & User Growth Insights

    #### 1. Top-Line Trajectory vs. Quality of Growth
    * Total WAU progressed from **{df_metrics.iloc[0]['wau']:,} ({df_metrics.iloc[0]['week']})** to **{latest['wau']:,} ({latest['week']})**.
    * The average weekly Quick Ratio is **{avg_qr:.2f}** (break-even is 1.0). When the Quick Ratio hovers between 1.0 and 1.5, additions are largely offset by recurring weekly churn.

    #### 2. Churn vs. Retention Realities
    * Week-over-week retention averages **{avg_ret:.1f}%**.
    * **Cohort Decay:** New cohorts retain at **{c1_str}** at Week 1, **{c4_str}** at Week 4, and **{c12_str}** at Week 12.
    * **Single-Week Drop-Off:** Approximately **{one_week:.1f}%** of all tracked devices were active in only a single week.

    #### 3. Strategic Recommendations
    * **Prioritize Onboarding and Day-7 Retention:** Because over half of initial joiners lapse quickly, improving the activation funnel will preserve more top-of-funnel acquisition spend.
    * **Systematize Reactivation (Resurrection):** Lapsed users return in high volumes, indicating solid episodic value. Automated re-engagement loops offer a higher ROI than cold acquisition.
    """)