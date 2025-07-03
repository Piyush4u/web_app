import streamlit as st
import pandas as pd
import altair as alt

# -------------------------
# Dummy user credentials
# -------------------------
CREDENTIALS = {
    "Admin": {"admin": "admin123"},
    "Manager": {"manager": "manager123"},
    "User": {"user": "user123"}
}

# -------------------------
# Sample work requests (for Manager Inbox)
# -------------------------
def init_requests():
    if 'requests' not in st.session_state:
        st.session_state.requests = [
            {'id': 1, 'description': 'PO #1001 needs review', 'status': 'Pending'},
            {'id': 2, 'description': 'Reconcile material batch 2002', 'status': 'Pending'},
            {'id': 3, 'description': 'Approve rate change for vendor X', 'status': 'Pending'}
        ]

# -------------------------
# Authentication Page
# -------------------------
def login_page():
    st.title("🔐 Material Reconciliation App Login")
    st.write("Select your user type and enter credentials to proceed.")

    user_type = st.selectbox("Login as", options=list(CREDENTIALS.keys()))
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in CREDENTIALS[user_type] and CREDENTIALS[user_type][username] == password:
            st.session_state.logged_in = True
            st.session_state.user_type = user_type
            st.success(f"Logged in as **{user_type}**")
            st.rerun()
        else:
            st.error("❌ Invalid username or password.")

# -------------------------
# Master Data Management Page
# -------------------------
def master_data_page():
    st.title("📂 Master Data Management")
    st.write(f"Welcome, **{st.session_state.user_type}**! Manage your master data below.")

    tab_upload, tab_view = st.tabs(["Upload Data", "View Data"])

    # Upload Tab
    with tab_upload:
        st.subheader("Upload Master Files")
        contractor_file = st.file_uploader(
            "Contractor Master Details (CSV/Excel)", type=["csv", "xls", "xlsx"], key="contractor_upload"
        )
        item_file = st.file_uploader(
            "Item Master Data (CSV/Excel)", type=["csv", "xls", "xlsx"], key="item_upload"
        )

        def load_file(uploaded):
            if uploaded:
                fname = uploaded.name.lower()
                if fname.endswith('.csv'):
                    return pd.read_csv(uploaded)
                return pd.read_excel(uploaded)
            return None

        if st.button("Load Files"):
            contractor_df = load_file(contractor_file)
            item_df = load_file(item_file)

            if contractor_df is not None:
                st.session_state.contractor_df = contractor_df
                st.success("✅ Contractor master data loaded!")
            if item_df is not None:
                st.session_state.item_df = item_df
                st.success("✅ Item master data loaded!")

    # View Tab
    with tab_view:
        st.subheader("Current Master Data")
        has_contractor = 'contractor_df' in st.session_state
        has_item = 'item_df' in st.session_state

        if not has_contractor and not has_item:
            st.info("No master data available. Upload files in the 'Upload Data' tab.")
        else:
            if has_contractor:
                df_c = st.session_state.contractor_df
                st.write(f"**Contractor Master:** {len(df_c)} records")
                st.dataframe(df_c)
            if has_item:
                df_i = st.session_state.item_df
                st.write(f"**Item Master:** {len(df_i)} records")
                st.dataframe(df_i)
            # Option to clear data
            if st.button("Clear All Master Data"):
                for key in ['contractor_df', 'item_df']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success("Master data cleared.")

# -------------------------
# Reconciliation Page
# -------------------------
def reconciliation_page():
    st.title("🔍 Material Reconciliation")
    if 'item_df' not in st.session_state or 'contractor_df' not in st.session_state:
        st.error("Please upload both contractor and item master data on the Master Data page.")
        return

    item_df = st.session_state.item_df
    contractor_df = st.session_state.contractor_df

    st.write("## Item Master Data")
    st.dataframe(item_df)
    st.write("## Contractor Master Data")
    st.dataframe(contractor_df)

    st.write("---")
    st.write("### Identify Missing Item Codes")
    if 'AssociatedItemCode' in contractor_df.columns:
        missing_items = item_df[~item_df['ItemCode'].isin(contractor_df['AssociatedItemCode'])]
    else:
        missing_items = pd.DataFrame()

    if not missing_items.empty:
        st.dataframe(missing_items)
    else:
        st.success("No missing item codes detected.")

# -------------------------
# Dashboard Page
# -------------------------
def dashboard_page():
    st.title("📊 Dashboard")
    if 'item_df' not in st.session_state or 'contractor_df' not in st.session_state:
        st.error("Please upload both contractor and item master data on the Master Data page.")
        return

    item_df = st.session_state.item_df
    contractor_df = st.session_state.contractor_df

    total_items = len(item_df)
    total_contractors = len(contractor_df)

    c1, c2 = st.columns(2)
    c1.metric("Total Items", total_items)
    c2.metric("Total Contractors", total_contractors)

    if 'Category' in item_df.columns:
        counts = item_df['Category'].value_counts().reset_index()
        counts.columns = ['Category', 'Count']
        chart = alt.Chart(counts).mark_bar().encode(x='Category', y='Count')
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Add a 'Category' column to the item master for breakdown.")

# -------------------------
# Work Inbox Page (Manager Only)
# -------------------------
def work_inbox_page():
    st.title("📥 Work Inbox")
    init_requests()
    requests = st.session_state.requests

    for req in requests:
        with st.expander(f"Request {req['id']}: {req['description']}"):
            st.write(f"**Status:** {req['status']}")
            if req['status'] == 'Pending':
                col1, col2 = st.columns(2)
                if col1.button("✅ Approve", key=f"approve_{req['id']}"):
                    req['status'] = 'Approved'
                    st.success(f"Request {req['id']} approved.")
                if col2.button("❌ Reject", key=f"reject_{req['id']}"):
                    req['status'] = 'Rejected'
                    st.error(f"Request {req['id']} rejected.")

    st.write("---")
    summary = pd.DataFrame(requests)
    st.write("### Request Summary")
    st.dataframe(summary)

# -------------------------
# Main App
# -------------------------
def main():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_type = None

    if not st.session_state.logged_in:
        login_page()
        return

    pages = {
        "Master Data": master_data_page,
        "Reconciliation": reconciliation_page,
        "Dashboard": dashboard_page
    }
    if st.session_state.user_type == 'Manager':
        pages["Work Inbox"] = work_inbox_page

    st.sidebar.title("Navigation")
    choice = st.sidebar.radio("Go to", list(pages.keys()))
    pages[choice]()

if __name__ == "__main__":
    main()
