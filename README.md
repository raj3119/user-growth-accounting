# 📊 User Growth Accounting & PMF Validation Engine

An end-to-end data analytics and product intelligence platform that decomposes Weekly Active Users (WAU) into first-principles growth accounting components: **Retained**, **New**, **Resurrected**, and **Churned** users. Built with Python, Pandas, and Streamlit, based on Social Capital's PMF validation methodology.

---

## 🚀 Key Features

- **Set-Theoretic Data Processing ($O(1)$ Hash Lookups):** Implements growth accounting identities using set theory to track user state transitions across arbitrary weekly cohorts.
- **Defensive Ingestion & Normalization:** Automatically sanitizes inconsistent column headers, trailing/leading whitespace, casing variations (`FD7C...` vs `fd7c...`), and internal dummy test tokens (`alex_device`, QA accounts).
- **Executive KPI Dashboard:** Real-time metrics for current WAU, 4-week rolling Quick Ratio, and average weekly retention.
- **Visual Growth Accounting Decomposition:** Dual-axis chart visualizing net user expansion versus churn volume alongside the stability benchmark ($QR = 1.0$).
- **New-User Cohort Decay Analysis:** Measures true new-user retention curves ($k = 0 \dots 12$ weeks) and calculates single-week visit drop-off share.
- **Interactive File Upload:** Evaluators can upload and stress-test custom multi-week user logs.

---

## 📐 Mathematical Identities & Definitions

$$\text{WAU}_t = \text{Retained}_t + \text{New}_t + \text{Resurrected}_t$$

$$\text{WAU}_{t-1} = \text{Retained}_t + \text{Churned}_t$$

$$\text{Net Growth}_t = \text{New}_t + \text{Resurrected}_t - \text{Churned}_t$$

$$\text{Quick Ratio}_t = \frac{\text{New}_t + \text{Resurrected}_t}{\text{Churned}_t}$$

- **$\text{Quick Ratio} > 1.0$:** Expansion phase (gross additions exceed customer churn).
- **$\text{Quick Ratio} < 1.0$:** Contraction phase ("leaky bucket" dynamics).
- **$\text{Quick Ratio} \ge 1.5 - 2.0$:** Benchmark for healthy, self-sustaining Product-Market Fit (PMF).

---

## 🛠️ Project Structure

```text
├── pipeline.py               # Data cleaning, set-theory transformations, and cohort logic
├── app.py                    # Streamlit dashboard interface, visual charts, and insights
├── requirements.txt          # Production dependencies
├── Active Users - Growth Accounting.xls  # Baseline 56-week device dataset
└── README.md                 # Project documentation