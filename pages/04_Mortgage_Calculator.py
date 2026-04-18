"""Mortgage Calculator Page — EMI, amortization schedule, and loan breakdown charts."""
import streamlit as st
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="Mortgage Calculator — PropAI", page_icon="🏦", layout="wide")

from utils.ui_helpers import page_header
page_header("🏦", "Mortgage Calculator", "Calculate EMI, view amortization schedule & plan your home loan", ROOT)

for key, default in [
    ("agent", None), ("selected_properties", []), ("thread_id", "session_001"),
    ("chat_history", []),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Pre-fill from saved properties ───────────────────────────────────────────
saved_props = st.session_state.selected_properties
prefill_options = ["Enter manually"] + [p["name"] for p in saved_props]
selected_prefill = st.selectbox("Load property price from saved list", prefill_options)
prefill_price = 0.0
if selected_prefill != "Enter manually":
    prop = next((p for p in saved_props if p["name"] == selected_prefill), {})
    prefill_price = prop.get("price", 0) / 100000

# ── Input Sliders ─────────────────────────────────────────────────────────────
st.markdown("### ⚙️ Loan Parameters")

col1, col2 = st.columns(2)
with col1:
    property_price = st.slider(
        "🏠 Property Price (₹ Lakhs)",
        min_value=10.0, max_value=500.0,
        value=float(prefill_price) if prefill_price else 75.0,
        step=1.0,
    )
    down_payment_pct = st.slider("💰 Down Payment (%)", min_value=5, max_value=50, value=20, step=1)
    loan_term = st.slider("📅 Loan Term (Years)", min_value=5, max_value=30, value=20, step=1)

with col2:
    interest_rate = st.slider("📈 Interest Rate (% p.a.)", min_value=5.0, max_value=15.0, value=8.5, step=0.1)

    from utils.calculators import mortgage_estimate, amortization_schedule
    result = mortgage_estimate(property_price * 100000, down_payment_pct, loan_term, interest_rate)

    st.markdown(f"""
    <div style="background:#fff;border:1px solid #e5e7eb;border-radius:12px;
                padding:18px;box-shadow:0 2px 8px rgba(0,0,0,0.04);margin-top:8px;">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
                <div style="font-size:0.75rem;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;">Down Payment</div>
                <div style="font-size:1.3rem;font-weight:800;color:#e63946;">₹{result['down_payment']/100000:.1f}L</div>
            </div>
            <div>
                <div style="font-size:0.75rem;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;">Loan Amount</div>
                <div style="font-size:1.3rem;font-weight:800;color:#e63946;">₹{result['loan_amount']/100000:.1f}L</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='border:none;border-top:1px solid #e5e7eb;margin:20px 0;'>", unsafe_allow_html=True)

# ── EMI Summary ───────────────────────────────────────────────────────────────
st.markdown("### 💳 EMI Summary")

col_a, col_b, col_c, col_d = st.columns(4)
with col_a:
    st.metric("Monthly EMI", f"₹{result['monthly_emi']:,.0f}")
with col_b:
    st.metric("Total Payment", f"₹{result['total_payment']/100000:.1f}L")
with col_c:
    st.metric("Total Interest", f"₹{result['total_interest']/100000:.1f}L")
with col_d:
    interest_pct = (result['total_interest'] / result['total_payment'] * 100) if result['total_payment'] else 0
    st.metric("Interest %", f"{interest_pct:.1f}%")

st.markdown("<hr style='border:none;border-top:1px solid #e5e7eb;margin:20px 0;'>", unsafe_allow_html=True)

# ── Charts ────────────────────────────────────────────────────────────────────
import plotly.graph_objects as go
import pandas as pd

schedule = amortization_schedule(result["loan_amount"], interest_rate, loan_term)

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.markdown("#### 🥧 Principal vs Interest")
    fig_pie = go.Figure(go.Pie(
        labels=["Principal", "Total Interest"],
        values=[result["principal"], result["total_interest"]],
        hole=0.5,
        marker=dict(colors=["#0077b6", "#e63946"]),
        textinfo="label+percent",
        textfont=dict(color="#1a1a2e"),
    ))
    fig_pie.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#1a1a2e"),
        margin=dict(t=20, b=20),
        showlegend=True,
        legend=dict(font=dict(color="#1a1a2e")),
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col_chart2:
    st.markdown("#### 📉 Outstanding Balance Over Time")
    if schedule:
        years_list   = [s["month"] / 12 for s in schedule]
        balance_list = [s["balance"] / 100000 for s in schedule]
        fig_balance  = go.Figure(go.Scatter(
            x=years_list, y=balance_list,
            fill="tozeroy",
            line=dict(color="#0077b6", width=2),
            fillcolor="rgba(0,119,182,0.08)",
        ))
        fig_balance.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#1a1a2e"), margin=dict(t=20, b=20),
            xaxis=dict(title="Years", gridcolor="#f0f0f0"),
            yaxis=dict(title="Balance (₹L)", gridcolor="#f0f0f0"),
        )
        st.plotly_chart(fig_balance, use_container_width=True)

# ── Monthly Breakdown Bar ─────────────────────────────────────────────────────
if schedule:
    st.markdown("#### 📊 Principal vs Interest Breakdown by Year")
    sampled = schedule[::12]
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        name="Principal",
        x=[f"Yr {s['month']//12}" for s in sampled],
        y=[s["principal"] for s in sampled],
        marker_color="#0077b6",
    ))
    fig_bar.add_trace(go.Bar(
        name="Interest",
        x=[f"Yr {s['month']//12}" for s in sampled],
        y=[s["interest"] for s in sampled],
        marker_color="#e63946",
    ))
    fig_bar.update_layout(
        barmode="stack",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#1a1a2e"), margin=dict(t=20, b=20),
        xaxis=dict(gridcolor="#f0f0f0"),
        yaxis=dict(title="Amount (₹)", gridcolor="#f0f0f0"),
        legend=dict(font=dict(color="#1a1a2e")),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("<hr style='border:none;border-top:1px solid #e5e7eb;margin:20px 0;'>", unsafe_allow_html=True)

# ── Amortization Table ────────────────────────────────────────────────────────
with st.expander("📋 Full Amortization Schedule"):
    if schedule:
        df_sched = pd.DataFrame(schedule)
        df_sched["balance"]   = df_sched["balance"].apply(lambda x: f"₹{x:,.0f}")
        df_sched["emi"]       = df_sched["emi"].apply(lambda x: f"₹{x:,.0f}")
        df_sched["principal"] = df_sched["principal"].apply(lambda x: f"₹{x:,.0f}")
        df_sched["interest"]  = df_sched["interest"].apply(lambda x: f"₹{x:,.0f}")
        df_sched.columns = ["Month", "EMI", "Principal", "Interest", "Balance"]
        st.dataframe(df_sched, use_container_width=True, hide_index=True)

# ── Rate Comparison ───────────────────────────────────────────────────────────
st.markdown("### 📊 Interest Rate Comparison")
rates        = [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0]
loan_amt     = result["loan_amount"]
comparison_data = []
for r in rates:
    from utils.calculators import compute_emi
    emi_data = compute_emi(loan_amt, r, loan_term)
    comparison_data.append({
        "Rate (%)":           r,
        "Monthly EMI (₹)":    f"₹{emi_data['monthly_emi']:,.0f}",
        "Total Interest (₹L)": f"₹{emi_data['total_interest']/100000:.1f}L",
        "Total Payment (₹L)":  f"₹{emi_data['total_payment']/100000:.1f}L",
    })
st.dataframe(pd.DataFrame(comparison_data), use_container_width=True, hide_index=True)
