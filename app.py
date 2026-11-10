import random
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import streamlit as st

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & CONSTANTS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Personal Expense & Budget Dashboard",
    page_icon="💰",
    layout="wide",
)

# Standard options used across forms and filters
TRANSACTION_TYPES = ["Expense", "Income"]
CATEGORIES = [
    "Food",
    "Transport",
    "Utilities",
    "Education",
    "Shopping",
    "Entertainment",
    "Custom",
]

# Realistic default monthly budgets so the dashboard works out-of-the-box
DEFAULT_CATEGORY_BUDGETS = {
    "Food": 600.0,
    "Transport": 250.0,
    "Utilities": 220.0,
    "Education": 150.0,
    "Shopping": 250.0,
    "Entertainment": 180.0,
    "Custom": 150.0,
}
DEFAULT_TOTAL_BUDGET = 1800.0
NEAR_LIMIT_THRESHOLD = 0.80  # Trigger a warning when spending reaches 80% of budget


# -----------------------------------------------------------------------------
# 2. GENERATE REALISTIC DEMO DATA
# -----------------------------------------------------------------------------
# We use @st.cache_data so the random dataset is generated once and stays
# consistent across page reloads during the user's session.
@st.cache_data
def generate_demo_transactions() -> pd.DataFrame:
    """
    Generates 110+ realistic demonstration transactions spanning the last 3 months.
    """
    rng = random.Random(42)

    today = datetime.now().date()
    start_date = today - timedelta(days=90)

    records = []

    # --- A. Generate Fixed Monthly Income & Bills (3 Months) ---
    for month_offset in range(3):
        cycle_date = today - timedelta(days=30 * month_offset)

        # Monthly Salary (Income)
        records.append({
            "Date": cycle_date.replace(day=1) if cycle_date.day > 1 else cycle_date,
            "Amount": 4200.00,
            "Type": "Income",
            "Category": "Custom",
            "Description/Notes": "Monthly Salary Deposit",
        })

        # Freelance / Side Income (Income)
        records.append({
            "Date": cycle_date - timedelta(days=rng.randint(5, 18)),
            "Amount": round(rng.uniform(250.0, 650.0), 2),
            "Type": "Income",
            "Category": "Custom",
            "Description/Notes": rng.choice([
                "Freelance Web Design Project",
                "Tutoring Session Payout",
                "Sold Old Electronics Online",
                "Quarterly Dividend & Interest",
            ]),
        })

    # --- B. Expense Templates by Category ---
    expense_catalog = {
        "Food": [
            ("Weekly Grocery Run at Supermarket", 55.0, 130.0),
            ("Morning Coffee & Pastry", 4.5, 11.0),
            ("Lunch with Colleagues", 12.0, 26.0),
            ("Dinner Takeout / Food Delivery", 22.0, 50.0),
            ("Fresh Produce at Farmers Market", 18.0, 42.0),
            ("Bakery & Snacks", 6.0, 16.0),
        ],
        "Transport": [
            ("Gas Station Fuel Refill", 38.0, 62.0),
            ("Metro / Bus Transit Pass Reload", 20.0, 45.0),
            ("Ride-Share Trip Downtown", 14.0, 34.0),
            ("City Parking Garage Fee", 5.0, 15.0),
            ("Routine Car Wash & Tire Air", 12.0, 22.0),
        ],
        "Utilities": [
            ("Monthly Electricity Bill", 65.0, 115.0),
            ("High-Speed Home Internet Bill", 59.99, 59.99),
            ("Mobile Phone Plan", 45.00, 45.00),
            ("Water & Trash Municipal Service", 28.0, 44.0),
        ],
        "Education": [
            ("Online Python & Data Science Course", 29.99, 79.99),
            ("Programming & Finance Reference Books", 22.0, 58.0),
            ("Workshop Registration Fee", 35.0, 90.0),
            ("Notebooks, Pens & Desk Supplies", 9.0, 24.0),
            ("Language Learning App Subscription", 12.99, 12.99),
        ],
        "Shopping": [
            ("Casual Clothing & Apparel", 30.0, 95.0),
            ("Household Cleaning & Paper Goods", 16.0, 42.0),
            ("USB-C Cable & Tech Accessories", 14.0, 48.0),
            ("Pharmacy & Personal Care Items", 11.0, 35.0),
            ("Kitchen Utensils & Storage Containers", 19.0, 52.0),
        ],
        "Entertainment": [
            ("Movie Theater Tickets & Popcorn", 18.0, 36.0),
            ("Music & Video Streaming Subscription", 14.99, 19.99),
            ("Weekend Bowling & Arcade Night", 25.0, 50.0),
            ("Concert / Live Comedy Show Ticket", 45.0, 95.0),
            ("Board Game Cafe with Friends", 15.0, 30.0),
        ],
        "Custom": [
            ("Birthday Gift for Friend", 25.0, 60.0),
            ("Monthly Gym & Fitness Membership", 35.0, 35.0),
            ("Charity & Community Donation", 20.0, 50.0),
            ("Haircut & Grooming", 28.0, 45.0),
        ],
    }

    # --- C. Generate Daily / Weekly Expense Transactions ---
    categories = list(expense_catalog.keys())
    category_weights = [32, 20, 8, 9, 13, 11, 7]

    # Generate 105 expense transactions so the total dataset has 111 records (>= 100)
    for _ in range(105):
        random_days = rng.randint(0, 90)
        tx_date = start_date + timedelta(days=random_days)

        category = rng.choices(categories, weights=category_weights, k=1)[0]
        description, min_amt, max_amt = rng.choice(expense_catalog[category])
        amount = round(rng.uniform(min_amt, max_amt), 2)

        records.append({
            "Date": tx_date,
            "Amount": amount,
            "Type": "Expense",
            "Category": category,
            "Description/Notes": description,
        })

    # Convert to a Pandas DataFrame and sort newest-first
    df = pd.DataFrame(records)
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    df = df.sort_values(by="Date", ascending=False).reset_index(drop=True)

    return df


# -----------------------------------------------------------------------------
# 3. INITIALIZE SESSION STATE (TRANSACTIONS & BUDGETS)
# -----------------------------------------------------------------------------
if "transactions_df" not in st.session_state:
    st.session_state.transactions_df = generate_demo_transactions().copy()

if "monthly_total_budget" not in st.session_state:
    st.session_state.monthly_total_budget = DEFAULT_TOTAL_BUDGET

if "category_budgets" not in st.session_state:
    st.session_state.category_budgets = DEFAULT_CATEGORY_BUDGETS.copy()

# Show any queued flash message after a rerun (Create / Update / Delete / Budget feedback)
if "flash_message" in st.session_state:
    msg_type, msg_text = st.session_state.pop("flash_message")
    if msg_type == "success":
        st.toast(msg_text, icon="✅")
    elif msg_type == "warning":
        st.toast(msg_text, icon="🗑️")


def sort_and_clean_df():
    """Keeps the session DataFrame sorted newest-first with a clean 0..N-1 index."""
    df_current = st.session_state.transactions_df
    if not df_current.empty:
        df_current["Date"] = pd.to_datetime(df_current["Date"]).dt.date
        st.session_state.transactions_df = (
            df_current.sort_values(by="Date", ascending=False)
            .reset_index(drop=True)
        )


# Reference the full session DataFrame before building sidebar filters
df = st.session_state.transactions_df

# Determine min and max dates in the dataset for the sidebar date filters
if not df.empty:
    min_dataset_date = pd.to_datetime(df["Date"]).min().date()
    max_dataset_date = pd.to_datetime(df["Date"]).max().date()
else:
    min_dataset_date = datetime.now().date() - timedelta(days=90)
    max_dataset_date = datetime.now().date()


# -----------------------------------------------------------------------------
# 4. SIDEBAR: FILTERS, ADD TRANSACTION & BUDGET SETTINGS
# -----------------------------------------------------------------------------
with st.sidebar:
    # --- A. Sidebar Filters (Date Range & Categories) ---
    st.header("🔍 Filter Transactions")
    st.caption("Filter the dashboard metrics, charts, and transaction table.")

    date_col1, date_col2 = st.columns(2)
    with date_col1:
        filter_start_date = st.date_input(
            "Start Date",
            value=min_dataset_date,
            help="Include transactions on or after this date.",
        )
    with date_col2:
        filter_end_date = st.date_input(
            "End Date",
            value=max_dataset_date,
            help="Include transactions on or before this date.",
        )

    if filter_start_date > filter_end_date:
        st.warning("⚠️ Start Date is after End Date. Please adjust the range.")

    selected_categories = st.multiselect(
        "Categories",
        options=CATEGORIES,
        default=CATEGORIES,
        help="Choose one or more categories to analyze.",
    )

    selected_types = st.multiselect(
        "Transaction Types",
        options=TRANSACTION_TYPES,
        default=TRANSACTION_TYPES,
        help="Filter by Income, Expense, or both.",
    )

    st.divider()

    # --- B. Add New Transaction (Create) ---
    st.header("➕ Add New Transaction")
    st.caption("Record a new income or expense item.")

    with st.form("add_transaction_form", clear_on_submit=True):
        new_date = st.date_input(
            "Date",
            value=datetime.now().date(),
            help="When did this transaction take place?",
        )
        new_type = st.selectbox(
            "Type",
            options=TRANSACTION_TYPES,
            help="Select 'Expense' for money spent or 'Income' for money received.",
        )
        new_category = st.selectbox(
            "Category",
            options=CATEGORIES,
            help="Choose the category that best fits this transaction.",
        )
        new_amount = st.number_input(
            "Amount ($)",
            min_value=0.00,
            step=1.00,
            format="%.2f",
            help="Enter an amount greater than 0.00.",
        )
        new_description = st.text_input(
            "Description / Notes",
            placeholder="e.g., Weekly groceries, Coffee, Freelance payout...",
        )

        submit_add = st.form_submit_button(
            "Add Transaction",
            use_container_width=True,
            type="primary",
        )

        if submit_add:
            if new_amount <= 0:
                st.error("⚠️ Amount must be greater than $0.00.")
            else:
                clean_desc = new_description.strip() or f"{new_category} ({new_type})"
                new_row = pd.DataFrame([{
                    "Date": new_date,
                    "Amount": round(float(new_amount), 2),
                    "Type": new_type,
                    "Category": new_category,
                    "Description/Notes": clean_desc,
                }])

                st.session_state.transactions_df = pd.concat(
                    [new_row, st.session_state.transactions_df],
                    ignore_index=True,
                )
                sort_and_clean_df()
                st.session_state.flash_message = (
                    "success",
                    f"Added {new_type}: {clean_desc} (${new_amount:,.2f})",
                )
                st.rerun()

    st.divider()

    # --- C. Monthly & Category-wise Budget Settings ---
    with st.expander("🎯 Monthly Budget Settings", expanded=False):
        st.caption("Set your target monthly total limit and category-specific budgets.")

        with st.form("budget_settings_form"):
            updated_total_budget = st.number_input(
                "Monthly Total Budget ($)",
                min_value=0.0,
                value=float(st.session_state.monthly_total_budget),
                step=50.0,
                format="%.2f",
                help="Your overall monthly spending limit across all categories.",
            )

            st.markdown("**Category-wise Monthly Budgets ($)**")
            updated_cat_budgets = {}
            for cat in CATEGORIES:
                updated_cat_budgets[cat] = st.number_input(
                    f"{cat} Budget ($)",
                    min_value=0.0,
                    value=float(st.session_state.category_budgets.get(cat, 150.0)),
                    step=25.0,
                    format="%.2f",
                    key=f"budget_input_{cat}",
                )

            save_budgets = st.form_submit_button(
                "💾 Save Budget Settings",
                use_container_width=True,
                type="primary",
            )

            if save_budgets:
                st.session_state.monthly_total_budget = round(float(updated_total_budget), 2)
                for cat, val in updated_cat_budgets.items():
                    st.session_state.category_budgets[cat] = round(float(val), 2)
                st.session_state.flash_message = (
                    "success",
                    "Monthly and category budgets updated!",
                )
                st.rerun()

    st.divider()
    if st.button("🔄 Reset Demo Data & Budgets", use_container_width=True):
        st.session_state.transactions_df = generate_demo_transactions().copy()
        st.session_state.monthly_total_budget = DEFAULT_TOTAL_BUDGET
        st.session_state.category_budgets = DEFAULT_CATEGORY_BUDGETS.copy()
        st.session_state.flash_message = ("success", "Demo data and default budgets restored!")
        st.rerun()


# -----------------------------------------------------------------------------
# 5. APPLY SIDEBAR FILTERS & PERIOD SELECTION
# -----------------------------------------------------------------------------
# Apply Date Range, Category, and Type filters from the sidebar
if not df.empty:
    tx_dates = pd.to_datetime(df["Date"]).dt.date
    sidebar_mask = (
        (tx_dates >= filter_start_date)
        & (tx_dates <= filter_end_date)
        & (df["Category"].isin(selected_categories))
        & (df["Type"].isin(selected_types))
    )
    filtered_df = df.loc[sidebar_mask].copy()
else:
    filtered_df = df.copy()

# Main Dashboard Header
st.title("💰 Personal Expense and Budget Dashboard")
st.markdown(
    "Track your income, visualize spending trends, monitor custom budgets, and export "
    "your financial reports."
)

# Build available Year-Month periods from the filtered dataset
if not filtered_df.empty:
    month_series = pd.to_datetime(filtered_df["Date"]).dt.strftime("%Y-%m")
    available_months = sorted(month_series.unique().tolist(), reverse=True)
else:
    available_months = [datetime.now().strftime("%Y-%m")]


def format_period_label(period_key: str) -> str:
    if period_key == "ALL_FILTERED":
        return f"All Filtered Dates ({filter_start_date} to {filter_end_date})"
    dt_obj = datetime.strptime(period_key, "%Y-%m")
    return f"{dt_obj.strftime('%B %Y')} ({period_key})"


period_col1, period_col2 = st.columns([2, 3])
with period_col1:
    selected_period = st.selectbox(
        "📅 Focus Period (Single Month or Full Filtered Range)",
        options=["ALL_FILTERED"] + available_months,
        index=0,
        format_func=format_period_label,
        help="Choose 'All Filtered Dates' to analyze the entire sidebar date range, or focus on one specific month.",
    )

# Narrow down to the active period DataFrame used by cards, alerts, and table
if not filtered_df.empty:
    if selected_period == "ALL_FILTERED":
        period_df = filtered_df.copy()
        active_months_count = max(
            pd.to_datetime(period_df["Date"]).dt.strftime("%Y-%m").nunique(), 1
        )
        budget_multiplier = active_months_count
        period_display_name = (
            f"Filtered Range ({active_months_count} "
            f"{'Month' if active_months_count == 1 else 'Months'})"
        )
    else:
        mask = pd.to_datetime(filtered_df["Date"]).dt.strftime("%Y-%m") == selected_period
        period_df = filtered_df.loc[mask].copy()
        budget_multiplier = 1
        period_display_name = datetime.strptime(selected_period, "%Y-%m").strftime("%B %Y")
else:
    period_df = filtered_df.copy()
    budget_multiplier = 1
    period_display_name = "Selected Filters"


# -----------------------------------------------------------------------------
# 6. CALCULATIONS & SUMMARY METRICS FOR ACTIVE PERIOD
# -----------------------------------------------------------------------------
if not period_df.empty:
    period_income = float(period_df.loc[period_df["Type"] == "Income", "Amount"].sum())
    period_expenses = float(period_df.loc[period_df["Type"] == "Expense", "Amount"].sum())
    income_count = int((period_df["Type"] == "Income").sum())
    expense_count = int((period_df["Type"] == "Expense").sum())
else:
    period_income = 0.0
    period_expenses = 0.0
    income_count = 0
    expense_count = 0

period_net_savings = period_income - period_expenses
period_savings_rate = (
    (period_net_savings / period_income * 100) if period_income > 0 else 0.0
)

# Effective budget scaled by number of months in the selected period
effective_total_budget = st.session_state.monthly_total_budget * budget_multiplier
budget_remaining = effective_total_budget - period_expenses

# Calculate spending by category for the selected period
expense_only_df = period_df[period_df["Type"] == "Expense"]
category_spending_series = (
    expense_only_df.groupby("Category")["Amount"].sum()
    if not expense_only_df.empty
    else pd.Series(dtype=float)
)

# Identify the Highest Spending Category
if not category_spending_series.empty and category_spending_series.max() > 0:
    highest_cat_name = category_spending_series.idxmax()
    highest_cat_amount = float(category_spending_series.max())
    highest_cat_share = (
        (highest_cat_amount / period_expenses * 100) if period_expenses > 0 else 0.0
    )
else:
    highest_cat_name = "None"
    highest_cat_amount = 0.0
    highest_cat_share = 0.0

st.subheader(f"📊 Financial Summary — {period_display_name}")

m_col1, m_col2, m_col3, m_col4 = st.columns(4)

with m_col1:
    st.metric(
        label="Total Income",
        value=f"${period_income:,.2f}",
        delta=f"{income_count} deposits",
        delta_color="normal",
    )

with m_col2:
    budget_pct_used = (
        (period_expenses / effective_total_budget * 100)
        if effective_total_budget > 0
        else 0.0
    )
    st.metric(
        label="Total Expenses",
        value=f"${period_expenses:,.2f}",
        delta=f"{budget_pct_used:.1f}% of ${effective_total_budget:,.0f} budget",
        delta_color="inverse" if period_expenses > effective_total_budget else "off",
    )

with m_col3:
    st.metric(
        label="Net Savings",
        value=f"${period_net_savings:,.2f}",
        delta=f"{period_savings_rate:.1f}% of income saved",
        delta_color="normal" if period_net_savings >= 0 else "inverse",
    )

with m_col4:
    st.metric(
        label="🔥 Highest Spending Category",
        value=highest_cat_name,
        delta=(
            f"${highest_cat_amount:,.2f} ({highest_cat_share:.1f}% of expenses)"
            if highest_cat_amount > 0
            else "No expenses recorded"
        ),
        delta_color="off",
    )


# -----------------------------------------------------------------------------
# 7. BUDGET WARNINGS & ALERTS
# -----------------------------------------------------------------------------
st.subheader(f"🚨 Budget Status & Alerts ({period_display_name})")

alerts_triggered = False

# A. Check Total Budget
if effective_total_budget > 0:
    total_usage_ratio = period_expenses / effective_total_budget
    if total_usage_ratio > 1.0:
        over_amt = period_expenses - effective_total_budget
        st.error(
            f"**Total Budget Exceeded!** You have spent **${period_expenses:,.2f}** "
            f"against your budget of **${effective_total_budget:,.2f}** "
            f"(**${over_amt:,.2f}** over limit / **{total_usage_ratio * 100:.1f}%** used)."
        )
        alerts_triggered = True
    elif total_usage_ratio >= NEAR_LIMIT_THRESHOLD:
        st.warning(
            f"**Approaching Total Budget Limit:** You have used **{total_usage_ratio * 100:.1f}%** "
            f"of your **${effective_total_budget:,.2f}** budget "
            f"(**${budget_remaining:,.2f}** remaining)."
        )
        alerts_triggered = True

# B. Check Category-wise Budgets (for selected categories in filter)
exceeded_categories = []
nearing_categories = []

for cat in selected_categories:
    cat_spent = float(category_spending_series.get(cat, 0.0))
    cat_budget = float(st.session_state.category_budgets.get(cat, 0.0)) * budget_multiplier

    if cat_budget > 0:
        cat_ratio = cat_spent / cat_budget
        if cat_ratio > 1.0:
            exceeded_categories.append(
                f"**{cat}**: spent **${cat_spent:,.2f}** / **${cat_budget:,.2f}** "
                f"(+${cat_spent - cat_budget:,.2f} over, {cat_ratio * 100:.1f}%)"
            )
        elif cat_ratio >= NEAR_LIMIT_THRESHOLD:
            nearing_categories.append(
                f"**{cat}**: spent **${cat_spent:,.2f}** / **${cat_budget:,.2f}** "
                f"({cat_ratio * 100:.1f}% used, ${cat_budget - cat_spent:,.2f} left)"
            )
    elif cat_spent > 0:
        exceeded_categories.append(
            f"**{cat}**: spent **${cat_spent:,.2f}** with a **$0.00** budget set"
        )

if exceeded_categories:
    alerts_triggered = True
    st.error(
        "**Category Budget Exceeded:**\n\n"
        + "\n".join(f"- {item}" for item in exceeded_categories)
    )

if nearing_categories:
    alerts_triggered = True
    st.warning(
        "**Categories Nearing Budget Limit (≥ 80%):**\n\n"
        + "\n".join(f"- {item}" for item in nearing_categories)
    )

if not alerts_triggered:
    st.success(
        f"✅ Great job! All total and category-wise expenses for **{period_display_name}** "
        "are comfortably within your set budgets."
    )

st.divider()


# -----------------------------------------------------------------------------
# 8. INTERACTIVE CHARTS & VISUALIZATIONS
# -----------------------------------------------------------------------------
st.subheader("📊 Interactive Charts & Visualizations")

chart_col1, chart_col2 = st.columns(2)

# --- Chart 1: Multi-Month Income vs. Expense Trend ---
with chart_col1:
    st.markdown("##### 📅 Monthly Income vs. Expenses Trend")
    # Use filtered_df so users see all months within their selected sidebar date range
    if not filtered_df.empty:
        trend_source = filtered_df.copy()
        trend_source["Month"] = pd.to_datetime(trend_source["Date"]).dt.strftime("%Y-%m")
        monthly_grouped = (
            trend_source.groupby(["Month", "Type"])["Amount"]
            .sum()
            .unstack(fill_value=0.0)
            .reset_index()
        )
        # Ensure both Income and Expense columns exist even if one type is filtered out
        for col_name in ["Income", "Expense"]:
            if col_name not in monthly_grouped.columns:
                monthly_grouped[col_name] = 0.0

        monthly_grouped["Net Savings"] = (
            monthly_grouped["Income"] - monthly_grouped["Expense"]
        )
        monthly_grouped = monthly_grouped.sort_values("Month")

        trend_long = monthly_grouped.melt(
            id_vars="Month",
            value_vars=["Income", "Expense", "Net Savings"],
            var_name="Metric",
            value_name="Amount ($)",
        )

        fig_trend = px.line(
            trend_long,
            x="Month",
            y="Amount ($)",
            color="Metric",
            markers=True,
            color_discrete_map={
                "Income": "#16a34a",
                "Expense": "#dc2626",
                "Net Savings": "#2563eb",
            },
            labels={"Month": "Month (YYYY-MM)", "Amount ($)": "Amount ($)"},
        )
        fig_trend.update_traces(line=dict(width=3), marker=dict(size=9))
        fig_trend.update_layout(
            margin=dict(l=10, r=10, t=20, b=10),
            legend_title_text="",
            hovermode="x unified",
            xaxis=dict(type="category"),
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("No transactions match the current filters to plot a monthly trend.")

# --- Chart 2: Category-wise Spending Comparison (Bar vs. Pie Toggle) ---
with chart_col2:
    header_c1, header_c2 = st.columns([3, 2])
    with header_c1:
        st.markdown(f"##### 🏷️ Category Spending ({period_display_name})")
    with header_c2:
        chart_style = st.radio(
            "Chart Type",
            options=["Bar (vs Budget)", "Donut Pie"],
            horizontal=True,
            label_visibility="collapsed",
        )

    if not expense_only_df.empty and period_expenses > 0:
        cat_chart_rows = []
        for cat in selected_categories:
            spent_val = float(category_spending_series.get(cat, 0.0))
            budget_val = (
                float(st.session_state.category_budgets.get(cat, 0.0)) * budget_multiplier
            )
            cat_chart_rows.append({
                "Category": cat,
                "Spent ($)": round(spent_val, 2),
                "Budget ($)": round(budget_val, 2),
            })
        cat_chart_df = pd.DataFrame(cat_chart_rows).sort_values(
            by="Spent ($)", ascending=False
        )

        if chart_style == "Bar (vs Budget)":
            cat_bar_long = cat_chart_df.melt(
                id_vars="Category",
                value_vars=["Spent ($)", "Budget ($)"],
                var_name="Measure",
                value_name="Amount ($)",
            )
            fig_cat = px.bar(
                cat_bar_long,
                x="Category",
                y="Amount ($)",
                color="Measure",
                barmode="group",
                color_discrete_map={
                    "Spent ($)": "#f97316",
                    "Budget ($)": "#94a3b8",
                },
                text_auto="$.0f",
            )
            fig_cat.update_layout(
                margin=dict(l=10, r=10, t=20, b=10),
                legend_title_text="",
            )
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            pie_df = cat_chart_df[cat_chart_df["Spent ($)"] > 0]
            fig_pie = px.pie(
                pie_df,
                names="Category",
                values="Spent ($)",
                hole=0.42,
            )
            fig_pie.update_traces(textposition="inside", textinfo="percent+label")
            fig_pie.update_layout(
                margin=dict(l=10, r=10, t=20, b=10),
                showlegend=True,
            )
            st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No expense transactions in the selected period to display category charts.")


# -----------------------------------------------------------------------------
# 9. CATEGORY SPENDING BREAKDOWN TABLE
# -----------------------------------------------------------------------------
st.subheader(f"📈 Category Spending & Budget Breakdown ({period_display_name})")

breakdown_rows = []
for cat in selected_categories:
    cat_spent = float(category_spending_series.get(cat, 0.0))
    cat_tx_count = (
        int((expense_only_df["Category"] == cat).sum())
        if not expense_only_df.empty
        else 0
    )
    share_of_expenses = (cat_spent / period_expenses * 100) if period_expenses > 0 else 0.0
    cat_budget = float(st.session_state.category_budgets.get(cat, 0.0)) * budget_multiplier
    cat_remaining = cat_budget - cat_spent
    budget_used_pct = (cat_spent / cat_budget * 100) if cat_budget > 0 else 0.0

    if cat_budget > 0 and cat_spent > cat_budget:
        status_label = "🔴 Over Budget"
    elif cat_budget > 0 and (cat_spent / cat_budget) >= NEAR_LIMIT_THRESHOLD:
        status_label = "🟡 Near Limit"
    else:
        status_label = "🟢 On Track"

    breakdown_rows.append({
        "Category": f"⭐ {cat}" if cat == highest_cat_name and cat_spent > 0 else cat,
        "Transactions": cat_tx_count,
        "Spent ($)": round(cat_spent, 2),
        "% of Total Expenses": round(share_of_expenses, 1),
        "Budget ($)": round(cat_budget, 2),
        "Remaining ($)": round(cat_remaining, 2),
        "Budget Used (%)": min(round(budget_used_pct, 1), 100.0),
        "Status": status_label,
    })

breakdown_df = (
    pd.DataFrame(breakdown_rows)
    .sort_values(by="Spent ($)", ascending=False)
    .reset_index(drop=True)
    if breakdown_rows
    else pd.DataFrame()
)

if not breakdown_df.empty:
    st.dataframe(
        breakdown_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Category": st.column_config.TextColumn(
                "Category (⭐ = Highest)",
                width="medium",
            ),
            "Transactions": st.column_config.NumberColumn(
                "Tx Count",
                format="%d",
                width="small",
            ),
            "Spent ($)": st.column_config.NumberColumn(
                "Spent ($)",
                format="$%.2f",
            ),
            "% of Total Expenses": st.column_config.ProgressColumn(
                "Share of Total Expenses",
                format="%.1f%%",
                min_value=0,
                max_value=100,
                help="Percentage share of this category relative to total expenses",
            ),
            "Budget ($)": st.column_config.NumberColumn(
                "Budget ($)",
                format="$%.2f",
            ),
            "Remaining ($)": st.column_config.NumberColumn(
                "Remaining ($)",
                format="$%.2f",
                help="Positive means under budget; negative means over budget",
            ),
            "Budget Used (%)": st.column_config.ProgressColumn(
                "Budget Progress",
                format="%.1f%%",
                min_value=0,
                max_value=100,
                help="How much of this category's budget has been used",
            ),
            "Status": st.column_config.TextColumn(
                "Status",
                width="small",
            ),
        },
    )

st.divider()


# -----------------------------------------------------------------------------
# 10. DATA EXPORT SECTION (CSV & PRINTABLE HTML/REPORT)
# -----------------------------------------------------------------------------
st.subheader("📥 Export Financial Data & Reports")
st.caption(
    "Download your currently filtered transactions, category budget breakdown, or a "
    "formatted summary report."
)

export_col1, export_col2, export_col3 = st.columns(3)

# 1. Filtered Transactions CSV
with export_col1:
    transactions_csv = period_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=f"📄 Download Filtered Transactions (CSV) [{len(period_df)} rows]",
        data=transactions_csv,
        file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

# 2. Category & Monthly Summary CSV
with export_col2:
    summary_header_df = pd.DataFrame([
        {"Metric": "Report Period", "Value": period_display_name},
        {"Metric": "Date Filter Range", "Value": f"{filter_start_date} to {filter_end_date}"},
        {"Metric": "Total Income ($)", "Value": f"{period_income:.2f}"},
        {"Metric": "Total Expenses ($)", "Value": f"{period_expenses:.2f}"},
        {"Metric": "Net Savings ($)", "Value": f"{period_net_savings:.2f}"},
        {"Metric": "Effective Budget ($)", "Value": f"{effective_total_budget:.2f}"},
        {"Metric": "Highest Spending Category", "Value": f"{highest_cat_name} (${highest_cat_amount:.2f})"},
    ])
    combined_csv_text = (
        "--- FINANCIAL SUMMARY ---\n"
        + summary_header_df.to_csv(index=False)
        + "\n--- CATEGORY BREAKDOWN ---\n"
        + (breakdown_df.to_csv(index=False) if not breakdown_df.empty else "No categories selected\n")
    )
    st.download_button(
        label="📊 Download Monthly & Category Summary (CSV)",
        data=combined_csv_text.encode("utf-8"),
        file_name=f"budget_summary_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

# 3. Printable HTML Summary Report (can be saved as PDF directly in any browser)
with export_col3:
    html_report = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Financial Report - {period_display_name}</title>
<style>
  body {{ font-family: Arial, sans-serif; margin: 32px; color: #1e293b; }}
  h1, h2 {{ color: #0f172a; }}
  .metrics {{ display: flex; gap: 16px; margin-bottom: 24px; }}
  .card {{ border: 1px solid #cbd5e1; border-radius: 8px; padding: 14px 18px; flex: 1; }}
  .card-title {{ font-size: 13px; color: #64748b; text-transform: uppercase; }}
  .card-value {{ font-size: 22px; font-weight: bold; margin-top: 4px; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 12px; margin-bottom: 28px; }}
  th, td {{ border: 1px solid #cbd5e1; padding: 8px 12px; text-align: left; font-size: 14px; }}
  th {{ background-color: #f1f5f9; }}
</style>
</head>
<body>
  <h1>Personal Expense & Budget Report</h1>
  <p><strong>Period:</strong> {period_display_name} &nbsp;|&nbsp;
     <strong>Filter Range:</strong> {filter_start_date} to {filter_end_date} &nbsp;|&nbsp;
     <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
  <div class="metrics">
    <div class="card"><div class="card-title">Total Income</div><div class="card-value">${period_income:,.2f}</div></div>
    <div class="card"><div class="card-title">Total Expenses</div><div class="card-value">${period_expenses:,.2f}</div></div>
    <div class="card"><div class="card-title">Net Savings</div><div class="card-value">${period_net_savings:,.2f}</div></div>
    <div class="card"><div class="card-title">Highest Category</div><div class="card-value">{highest_cat_name} (${highest_cat_amount:,.2f})</div></div>
  </div>
  <h2>Category Budget Breakdown</h2>
  {breakdown_df.to_html(index=False) if not breakdown_df.empty else "<p>No category data.</p>"}
  <h2>Filtered Transactions ({len(period_df)} records)</h2>
  {period_df.to_html(index=False) if not period_df.empty else "<p>No transactions.</p>"}
</body>
</html>"""
    st.download_button(
        label="🖨️ Download Printable Report (HTML / Print to PDF)",
        data=html_report.encode("utf-8"),
        file_name=f"financial_report_{datetime.now().strftime('%Y%m%d')}.html",
        mime="text/html",
        use_container_width=True,
    )

st.divider()


# -----------------------------------------------------------------------------
# 11. EDIT OR DELETE EXISTING TRANSACTIONS (UPDATE & DELETE)
# -----------------------------------------------------------------------------
with st.expander("✏️ Edit or Delete an Existing Transaction", expanded=False):
    if df.empty:
        st.info("No transactions available to edit or delete. Add one using the sidebar!")
    else:
        st.caption(
            "Select any transaction from the dropdown below to modify its details or delete it."
        )

        def format_tx_option(idx: int) -> str:
            row = df.loc[idx]
            sign = "+" if row["Type"] == "Income" else "-"
            return (
                f"#{idx} | {row['Date']} | {row['Category']} | "
                f"{sign}${row['Amount']:,.2f} — {row['Description/Notes']}"
            )

        # Offer the currently visible transactions first, or all transactions if filtered is empty
        editable_indices = (
            period_df.index.tolist() if not period_df.empty else df.index.tolist()
        )

        selected_idx = st.selectbox(
            "Select Transaction to Edit or Delete",
            options=editable_indices,
            format_func=format_tx_option,
            key="crud_selected_idx",
        )

        selected_row = df.loc[selected_idx]

        default_type_idx = (
            TRANSACTION_TYPES.index(selected_row["Type"])
            if selected_row["Type"] in TRANSACTION_TYPES
            else 0
        )
        default_cat_idx = (
            CATEGORIES.index(selected_row["Category"])
            if selected_row["Category"] in CATEGORIES
            else CATEGORIES.index("Custom")
        )

        with st.form("edit_delete_transaction_form"):
            edit_col1, edit_col2, edit_col3 = st.columns(3)

            with edit_col1:
                edit_date = st.date_input(
                    "Date",
                    value=pd.to_datetime(selected_row["Date"]).date(),
                )
            with edit_col2:
                edit_type = st.selectbox(
                    "Type",
                    options=TRANSACTION_TYPES,
                    index=default_type_idx,
                )
            with edit_col3:
                edit_category = st.selectbox(
                    "Category",
                    options=CATEGORIES,
                    index=default_cat_idx,
                )

            edit_col4, edit_col5 = st.columns([1, 2])
            with edit_col4:
                edit_amount = st.number_input(
                    "Amount ($)",
                    min_value=0.00,
                    value=float(selected_row["Amount"]),
                    step=1.00,
                    format="%.2f",
                )
            with edit_col5:
                edit_description = st.text_input(
                    "Description / Notes",
                    value=str(selected_row["Description/Notes"]),
                )

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                save_changes = st.form_submit_button(
                    "💾 Save Changes",
                    use_container_width=True,
                    type="primary",
                )
            with btn_col2:
                delete_tx = st.form_submit_button(
                    "🗑️ Delete Transaction",
                    use_container_width=True,
                )

            if save_changes:
                if edit_amount <= 0:
                    st.error("⚠️ Amount must be greater than $0.00.")
                else:
                    clean_edit_desc = (
                        edit_description.strip() or f"{edit_category} ({edit_type})"
                    )
                    st.session_state.transactions_df.loc[
                        selected_idx,
                        ["Date", "Amount", "Type", "Category", "Description/Notes"],
                    ] = [
                        edit_date,
                        round(float(edit_amount), 2),
                        edit_type,
                        edit_category,
                        clean_edit_desc,
                    ]
                    sort_and_clean_df()
                    st.session_state.flash_message = (
                        "success",
                        f"Updated transaction #{selected_idx}: {clean_edit_desc}",
                    )
                    st.rerun()

            if delete_tx:
                deleted_desc = selected_row["Description/Notes"]
                st.session_state.transactions_df = (
                    st.session_state.transactions_df.drop(index=selected_idx)
                    .reset_index(drop=True)
                )
                st.session_state.flash_message = (
                    "warning",
                    f"Deleted transaction #{selected_idx}: {deleted_desc}",
                )
                st.rerun()


# -----------------------------------------------------------------------------
# 12. TRANSACTIONS DATA TABLE (READ)
# -----------------------------------------------------------------------------
st.subheader(f"📋 Transactions Table ({period_display_name})")
st.caption(
    f"Showing **{len(period_df)}** filtered transactions "
    f"(out of **{len(df)}** total records). The **#** column matches the ID in the "
    "'Edit or Delete' selector above."
)

# Preserve original DataFrame index as the 'ID' column so it matches the Edit/Delete selector
display_df = period_df.copy()
display_df.insert(0, "ID", display_df.index)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    height=480,
    column_config={
        "ID": st.column_config.NumberColumn(
            "#",
            format="%d",
            width="small",
            help="Transaction ID (matches the # in Edit or Delete)",
        ),
        "Date": st.column_config.DateColumn(
            "Date",
            format="YYYY-MM-DD",
            help="Date of the transaction",
        ),
        "Amount": st.column_config.NumberColumn(
            "Amount ($)",
            format="$%.2f",
            help="Transaction amount in USD",
        ),
        "Type": st.column_config.TextColumn(
            "Type",
            help="Income or Expense",
        ),
        "Category": st.column_config.TextColumn(
            "Category",
            help="Spending or income category",
        ),
        "Description/Notes": st.column_config.TextColumn(
            "Description / Notes",
            width="large",
            help="Brief note describing the transaction",
        ),
    },
)
