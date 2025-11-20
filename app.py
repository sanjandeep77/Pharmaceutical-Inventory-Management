# app.py — PharmaDB Dashboard
#
# Major Refactoring v5:
# - Added secondary graph to Analytics page for more variance.
# - Added Role-Based Views page.
# - Implemented full CRUD for Sales and Purchases with a cart-based system.
# - Decoupled database instantiation from the app layer to solve caching issues.
# - Abstracted CRUD UI generation to reduce code duplication and improve maintainability.
# ------------------------------------------------------------
import streamlit as st
import pandas as pd
import plotly.express as px
from backend import get_db # Use the new singleton DB instance
import io
import time
from datetime import datetime
from typing import List, Dict, Callable, Any

# -------------------------------------------------------------
# 🌈 Theme + Page Config
# -------------------------------------------------------------
st.set_page_config(
    page_title="PharmaDB Dashboard",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

TEAL = "#12A89D"
DARK = "#043834"

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif;
    background-color: #F9FDFC;
    color: #043834;
}
.block-container { padding-top: 1rem; padding-bottom: 2rem; }
.header {
    background: linear-gradient(90deg, #E7FFFC, #F7FFFE);
    border-radius: 16px;
    padding: 18px 22px;
    display: flex; align-items: center; gap: 14px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.header-icon {
    width: 48px; height: 48px; border-radius: 14px;
    background: #12A89D; color: white; display: flex;
    align-items: center; justify-content: center;
    font-size: 22px; font-weight: 700;
}
.stTabs [data-baseweb="tab-list"] { gap: 1rem; }
.stTabs [data-baseweb="tab"] {
    background: rgba(18,168,157,0.08);
    border-radius: 10px; color: #094944;
    font-weight: 500; padding: 0.5rem 1rem;
}
.stTabs [aria-selected="true"] {
    background: #12A89D !important;
    color: white !important;
}
.kpi {
    border-radius: 16px; background: white;
    padding: 18px; box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    text-align: center; transition: all 0.2s ease;
}
.kpi:hover { box-shadow: 0 3px 8px rgba(0,0,0,0.08); transform: translateY(-2px); }
.kpi h3 { margin: 0; font-size: 22px; color: #093f3a; }
.kpi p { margin: 4px 0 0 0; font-size: 13px; color: #5f7371; }
.footer { text-align:center; font-size:12px; color:#607673; margin-top:30px; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 🧠 App Initialization
# -------------------------------------------------------------
db = get_db() # Get the single, shared database instance

# Initialize session state for carts
if 'sales_cart' not in st.session_state:
    st.session_state.sales_cart = []
if 'purchase_cart' not in st.session_state:
    st.session_state.purchase_cart = []

def q_df(query: str, params=None):
    """Helper to run a query and return a DataFrame."""
    try:
        data = db.fetch(query, params)
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"❌ Query failed: {e}")
        return pd.DataFrame()

def exec_query(query: str, params=None, msg="Success!"):
    """Helper to execute a query and show a success message before rerunning."""
    try:
        db.execute(query, params)
        st.success(msg)
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"⚠️ Operation failed: {e}")

# -------------------------------------------------------------
# 🔗 Sidebar & Header
# -------------------------------------------------------------
try:
    db.fetch("SELECT 1")
    st.sidebar.success("Connected to MySQL ✅")
except Exception as e:
    st.sidebar.error(f"DB connection failed: {e}")
    st.stop()

st.sidebar.title("PharmaDB Navigation")
page = st.sidebar.radio("Go to", [
    "📈 Analytics",
    "📦 Medicines",
    "🚚 Suppliers",
    "👥 Customers",
    "🧾 Purchases",
    "💳 Sales",
    "🔬 Trigger Sandbox",
    "🔧 Stored Procedures",
    "👤 Role-Based Views"
])

st.markdown(f"""
<div class="header">
    <div class="header-icon">Rx</div>
    <div>
        <h2 style="margin:0;color:{DARK};">PharmaDB</h2>
        <p style="margin:0;font-size:13px;color:#14786f;">Inventory • Sales • Prescriptions</p>
    </div>
</div>
<br/>
""", unsafe_allow_html=True)

# =============================================================
# 🧱 GENERIC CRUD PAGE GENERATOR
# =============================================================
def create_crud_page(
    page_title: str, table_name: str, pk_col: str, display_col: str, view_query: str,
    form_fields: Dict[str, Callable], insert_query: str, update_fields: Dict[str, Callable],
    update_query_template: str, add_msg: str, update_msg: str, delete_msg: str
):
    st.subheader(page_title)
    view_tab, add_tab, manage_tab = st.tabs(["View All", "Add New", "Edit & Delete"])
    with view_tab:
        df_view = q_df(view_query)
        st.dataframe(df_view, use_container_width=True)
    with add_tab:
        st.markdown(f"### ➕ Add New {table_name}")
        with st.form(f"add_{table_name}_form", clear_on_submit=True):
            form_data = {field: widget() for field, widget in form_fields.items()}
            if st.form_submit_button(f"Add {table_name}", type="primary"):
                exec_query(insert_query, tuple(form_data.values()), add_msg)
    with manage_tab:
        st.markdown(f"### ✏️ Edit / Delete {table_name}")
        df_manage = q_df(f"SELECT {pk_col}, {display_col} FROM {table_name} ORDER BY {display_col}")
        if not df_manage.empty:
            item_map = pd.Series(df_manage[pk_col].values, index=df_manage[display_col]).to_dict()
            selected_item_name = st.selectbox(f"Select {table_name}", item_map.keys(), key=f"sel_{table_name}")
            selected_pk = item_map[selected_item_name]
            df_full_row = q_df(f"SELECT * FROM {table_name} WHERE {pk_col}={selected_pk}")
            if not df_full_row.empty:
                row = df_full_row.iloc[0]
                st.markdown("#### Update Details")
                update_data = {field: widget(row) for field, widget in update_fields.items()}
                if st.button(f"Update {table_name}", key=f"upd_{table_name}"):
                    exec_query(update_query_template, tuple(list(update_data.values()) + [selected_pk]), update_msg)
                st.divider()
                st.markdown("#### Delete Record")
                st.warning(f"This will permanently delete **{row[display_col]}**. This action cannot be undone.", icon="⚠️")
                if st.button(f"Delete {table_name}", type="primary", key=f"del_{table_name}"):
                    exec_query(f"DELETE FROM {table_name} WHERE {pk_col}=%s", (selected_pk,), delete_msg)
        else:
            st.info(f"No {page_title.lower()} available to manage.")

# =============================================================
# 💰 ORDER (SALES/PURCHASE) PAGE GENERATOR
# =============================================================
def create_order_page(order_type: str):
    is_sales = order_type == "Sales"
    
    title, table_name, item_table, pk_col, date_col, amount_col, party_col, party_table, party_pk_col, cart_name, price_col = (
        ("Sales Orders", "Sales_Order", "Sales_Item", "SOID", "SODate", "TotalAmount", "Customer", "Customer", "CustomerID", "sales_cart", "SellingPrice") if is_sales
        else ("Purchase Orders", "Purchase_Order", "Purchase_Item", "POID", "PODate", "TotalCost", "Supplier", "Supplier", "SupplierID", "purchase_cart", "CostPrice")
    )

    st.subheader(title)
    view_tab, create_tab, delete_tab = st.tabs([f"View {order_type}", f"Create New {order_type}", f"Delete {order_type}"])

    with view_tab:
        st.markdown(f"### All {title}")
        df_orders = q_df(f"SELECT o.{pk_col}, o.{date_col}, p.Name AS {party_col}, o.{amount_col}, o.Status FROM {table_name} o JOIN {party_table} p ON o.{party_pk_col} = p.{party_pk_col} ORDER BY o.{date_col} DESC")
        if df_orders.empty: st.info(f"No {order_type.lower()} orders found.")
        else:
            st.dataframe(df_orders, use_container_width=True)
            with st.expander("View Order Items"):
                order_id = st.selectbox(f"Select {order_type} ID", df_orders[pk_col], key=f"view_{pk_col}")
                if order_id:
                    df_items = q_df(f"SELECT m.Name, si.Quantity, si.{price_col}, si.LineTotal FROM {item_table} si JOIN Medicine m ON si.MedicineID = m.MedicineID WHERE si.{pk_col} = %s", (order_id,))
                    st.dataframe(df_items, use_container_width=True)

    with create_tab:
        st.markdown(f"### Create New {order_type} Order")
        with st.form(f"add_to_{cart_name}_form"):
            medicines = q_df("SELECT MedicineID, Name, Price FROM Medicine ORDER BY Name")
            med_map = pd.Series(medicines.MedicineID.values, index=medicines.Name).to_dict()
            med_price_map = pd.Series(medicines.Price.values, index=medicines.MedicineID).to_dict()
            sel_med_name = st.selectbox("Medicine", med_map.keys())
            sel_qty = st.number_input("Quantity", min_value=1, step=1)
            if st.form_submit_button("Add to Order"):
                med_id = med_map[sel_med_name]
                price = med_price_map[med_id]
                st.session_state[cart_name].append({"MedicineID": med_id, "Name": sel_med_name, "Quantity": sel_qty, "Price": price, "Total": sel_qty * price})
                st.success(f"Added {sel_qty} x {sel_med_name} to the order.")
                st.rerun()

        if st.session_state[cart_name]:
            st.markdown("#### Current Order")
            cart_df = pd.DataFrame(st.session_state[cart_name])
            st.dataframe(cart_df, use_container_width=True)
            if st.button(f"Clear Order", key=f"clear_{cart_name}"):
                st.session_state[cart_name] = []
                st.rerun()
            with st.form(f"submit_{cart_name}_form"):
                parties = q_df(f"SELECT {party_pk_col}, Name FROM {party_table} ORDER BY Name")
                party_map = pd.Series(parties[party_pk_col].values, index=parties.Name).to_dict()
                sel_party_name = st.selectbox(f"Select {party_col}", party_map.keys())
                if st.form_submit_button(f"Submit Full Order", type="primary"):
                    party_id = party_map[sel_party_name]
                    order_query = f"INSERT INTO {table_name} ({date_col}, {party_pk_col}, Status) VALUES (%s, %s, %s)"
                    order_id = db.execute_and_get_id(order_query, (datetime.now().date(), party_id, 'Completed'))
                    if order_id:
                        for item in st.session_state[cart_name]:
                            item_query = f"INSERT INTO {item_table} ({pk_col}, MedicineID, Quantity, {price_col}) VALUES (%s, %s, %s, %s)"
                            db.execute(item_query, (order_id, item["MedicineID"], item["Quantity"], item["Price"]))
                        st.session_state[cart_name] = []
                        st.success(f"{order_type} Order #{order_id} created successfully!")
                        time.sleep(1)
                        st.rerun()
                    else: st.error(f"Failed to create {order_type} order.")

    with delete_tab:
        st.markdown(f"### Delete {order_type} Order")
        df_orders = q_df(f"SELECT {pk_col} FROM {table_name} ORDER BY {pk_col} DESC")
        if df_orders.empty: st.info(f"No {order_type.lower()} orders to delete.")
        else:
            order_id_to_del = st.selectbox(f"Select {order_type} ID to delete", df_orders[pk_col], key=f"del_{pk_col}")
            st.warning(f"This will permanently delete {order_type} Order #{order_id_to_del} and all its items. This action cannot be undone and will adjust stock levels accordingly.", icon="⚠️")
            if st.button(f"Delete Order #{order_id_to_del}", type="primary"):
                exec_query(f"DELETE FROM {table_name} WHERE {pk_col}=%s", (order_id_to_del,), f"🗑️ {order_type} Order #{order_id_to_del} deleted!")

# =============================================================
# RENDER SELECTED PAGE
# =============================================================
if page == "📈 Analytics":
    st.subheader("Dashboard & Analytics")
    df_meds, df_sup, df_cust = q_df("SELECT MedicineID FROM Medicine"), q_df("SELECT SupplierID FROM Supplier"), q_df("SELECT CustomerID FROM Customer")
    df_sales, stock_val_df = q_df("SELECT TotalAmount FROM Sales_Order"), q_df("SELECT GetStockValue() AS Total")
    k1,k2,k3,k4,k5 = st.columns(5)
    with k1: st.markdown(f"<div class='kpi'><h3>{len(df_meds)}</h3><p>Medicines</p></div>", unsafe_allow_html=True)
    with k2: st.markdown(f"<div class='kpi'><h3>{len(df_sup)}</h3><p>Suppliers</p></div>", unsafe_allow_html=True)
    with k3: st.markdown(f"<div class='kpi'><h3>{len(df_cust)}</h3><p>Customers</p></div>", unsafe_allow_html=True)
    total_sales = df_sales['TotalAmount'].sum() if not df_sales.empty else 0
    with k4: st.markdown(f"<div class='kpi'><h3>{total_sales:,.2f}</h3><p>Total Sales (₹)</p></div>", unsafe_allow_html=True)
    stock_val = stock_val_df["Total"].sum() if not stock_val_df.empty else 0
    with k5: st.markdown(f"<div class='kpi'><h3>{stock_val:,.2f}</h3><p>Stock Value (₹)</p></div>", unsafe_allow_html=True)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Daily Revenue")
        df_rev = q_df("SELECT SODate AS Day, SUM(TotalAmount) AS Revenue FROM Sales_Order WHERE Status = 'Completed' GROUP BY SODate ORDER BY SODate")
        if not df_rev.empty:
            figR = px.line(df_rev, x="Day", y="Revenue", title="Daily Revenue Trend", markers=True, color_discrete_sequence=[TEAL])
            figR.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color=DARK))
            st.plotly_chart(figR, use_container_width=True)
        else: 
            st.info("No revenue data yet to display a trend.")
    
    with col2:
        st.markdown("### Revenue by Category")
        df_cat_rev = q_df("""
            SELECT c.Name AS Category, SUM(si.LineTotal) AS Revenue
            FROM Sales_Item si
            JOIN Medicine m ON si.MedicineID = m.MedicineID
            JOIN Category c ON m.CategoryID = c.CategoryID
            GROUP BY c.Name
            ORDER BY Revenue DESC
        """)
        if not df_cat_rev.empty:
            figC = px.bar(df_cat_rev, x="Category", y="Revenue", title="Revenue by Medicine Category", color_discrete_sequence=[TEAL])
            figC.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color=DARK))
            st.plotly_chart(figC, use_container_width=True)
        else:
            st.info("No category revenue data yet.")


elif page == "📦 Medicines":
    df_cats = q_df("SELECT CategoryID, Name FROM Category ORDER BY Name")
    cat_map = pd.Series(df_cats.CategoryID.values, index=df_cats.Name).to_dict()
    create_crud_page("Medicines Inventory", "Medicine", "MedicineID", "Name",
        "SELECT m.MedicineID, m.Name, m.Manufacturer, m.Price, m.StockQty, m.ReorderLevel, c.Name AS Category FROM Medicine m LEFT JOIN Category c ON m.CategoryID = c.CategoryID ORDER BY m.Name",
        {"Name": lambda: st.text_input("Name"), "Manufacturer": lambda: st.text_input("Manufacturer"), "Price": lambda: st.number_input("Price", min_value=0.0, format="%.2f"),
         "StockQty": lambda: st.number_input("Stock Quantity", min_value=0, step=1), "ReorderLevel": lambda: st.number_input("Reorder Level", min_value=0, step=1),
         "CategoryID": lambda: cat_map.get(st.selectbox("Category (optional)", [""] + list(cat_map.keys())))},
        "INSERT INTO Medicine (Name, Manufacturer, Price, StockQty, ReorderLevel, CategoryID) VALUES (%s, %s, %s, %s, %s, %s)",
        {"Price": lambda r: st.number_input("Update Price", value=float(r["Price"]), format="%.2f"), "StockQty": lambda r: st.number_input("Update Stock Qty", value=int(r["StockQty"]), step=1)},
        "UPDATE Medicine SET Price=%s, StockQty=%s WHERE MedicineID=%s", "💊 Medicine added!", "✅ Medicine updated!", "🗑️ Medicine deleted!")

elif page == "🚚 Suppliers":
    create_crud_page("Suppliers", "Supplier", "SupplierID", "Name", "SELECT * FROM Supplier ORDER BY Name",
        {"Name": lambda: st.text_input("Supplier Name"), "Contact": lambda: st.text_input("Contact"), "Address": lambda: st.text_area("Address"), "Email": lambda: st.text_input("Email"), "Phone": lambda: st.text_input("Phone")},
        "INSERT INTO Supplier (Name, Contact, Address, Email, Phone) VALUES (%s, %s, %s, %s, %s)",
        {"Contact": lambda r: st.text_input("Edit Contact", r["Contact"] or ""), "Phone": lambda r: st.text_input("Edit Phone", r["Phone"] or "")},
        "UPDATE Supplier SET Contact=%s, Phone=%s WHERE SupplierID=%s", "🚚 Supplier added!", "✅ Supplier updated!", "🗑️ Supplier deleted!")

elif page == "👥 Customers":
    create_crud_page("Customers", "Customer", "CustomerID", "Name", "SELECT * FROM Customer ORDER BY Name",
        {"Name": lambda: st.text_input("Customer Name"), "Email": lambda: st.text_input("Email"), "Phone": lambda: st.text_input("Phone"), "Address": lambda: st.text_area("Address")},
        "INSERT INTO Customer (Name, Email, Phone, Address) VALUES (%s, %s, %s, %s)",
        {"Phone": lambda r: st.text_input("Edit Phone", r["Phone"] or ""), "Address": lambda r: st.text_input("Edit Address", r["Address"] or "")},
        "UPDATE Customer SET Phone=%s, Address=%s WHERE CustomerID=%s", "👤 Customer added!", "✅ Customer updated!", "🗑️ Customer deleted!")

elif page == "🧾 Purchases":
    create_order_page("Purchase")

elif page == "💳 Sales":
    create_order_page("Sales")

elif page == "🔧 Stored Procedures":
    st.subheader("Stored Procedures — Demo")

    st.markdown("This page demonstrates calling the stored procedure `GetMedicineDetailsByCategory` from the database.")

    # load categories for dropdown
    df_cats = q_df("SELECT Name FROM Category ORDER BY Name")
    if df_cats.empty:
        st.info("No categories available in the database.")
    else:
        cat_list = df_cats["Name"].tolist()
        selected_cat = st.selectbox("Select Category", cat_list)

        st.markdown("#### Execute stored procedure")
        st.write("Procedure: `CALL GetMedicineDetailsByCategory(<category_name>)`")

        col_run, col_hint = st.columns([1, 3])
        with col_run:
            if st.button("Run Procedure", key="run_proc_get_by_cat"):
                try:
                    proc_df = q_df("CALL GetMedicineDetailsByCategory(%s)", (selected_cat,))
                    if proc_df.empty:
                        st.info(f"No medicines returned for category '{selected_cat}'.")
                    else:
                        st.success(f"Procedure returned {len(proc_df)} row(s).")
                        st.dataframe(proc_df, use_container_width=True)
                except Exception as e:
                    st.error(f"Failed to call procedure: {e}")

        with col_hint:
            st.markdown(
                """
                **Notes**
                - This runs the stored procedure on the database server and shows the resulting rows.
                - Use this to validate server-side logic and ensure centralized business rules.
                """
            )

elif page == "🔬 Trigger Sandbox":
    st.subheader("Stock & Alert Trigger Sandbox")
    st.info("This page demonstrates the automated triggers for stock management. When you simulate a sale, the system will automatically decrease the medicine's stock. If the stock falls below the reorder level, a new alert will be generated.", icon="🔬")
    df_meds = q_df("SELECT MedicineID, Name, StockQty, ReorderLevel, Price FROM Medicine ORDER BY Name")
    if df_meds.empty: st.warning("No medicines in the database to test."); st.stop()
    med_map = pd.Series(df_meds.MedicineID.values, index=df_meds.Name).to_dict()
    med_name = st.selectbox("Select a Medicine to test", df_meds["Name"])
    selected_med = df_meds[df_meds["Name"] == med_name].iloc[0]
    med_id = int(selected_med["MedicineID"])
    c1, c2 = st.columns(2)
    c1.metric("Current Stock", selected_med["StockQty"]); c2.metric("Reorder Level", selected_med["ReorderLevel"])
    st.divider()
    st.markdown("### Simulate a Sale")
    qty_to_sell = st.number_input("Quantity to Sell", min_value=1, value=1, key="sell_qty")
    if st.button("Process Sale", type="primary"):
        customers = q_df("SELECT CustomerID FROM Customer LIMIT 1")
        if customers.empty: st.error("Cannot simulate sale: No customers in the database."); st.stop()
        customer_id = int(customers.iloc[0]["CustomerID"])
        so_query = "INSERT INTO Sales_Order (SODate, Status, CustomerID) VALUES (%s, %s, %s)"
        soid = db.execute_and_get_id(so_query, (datetime.now().date(), "Completed", customer_id))
        if not soid: st.error("Failed to create a dummy sales order and retrieve its ID."); st.stop()
        med_price = float(selected_med['Price'])
        si_query = "INSERT INTO Sales_Item (SOID, MedicineID, Quantity, SellingPrice) VALUES (%s, %s, %s, %s)"
        exec_query(si_query, (soid, med_id, qty_to_sell, med_price), msg=f"✅ Sale of {qty_to_sell} unit(s) of {med_name} simulated!")
    st.divider()
    st.markdown("### Trigger Results")
    st.markdown("#### 📦 Updated Stock Level")
    updated_med_df = q_df(f"SELECT Name, StockQty, ReorderLevel FROM Medicine WHERE MedicineID = {med_id}")
    st.dataframe(updated_med_df, use_container_width=True)
    st.markdown("#### 🔔 Stock Alerts")
    alerts_df = q_df(f"SELECT AlertType, Notes, DateInitiated, Resolved FROM Stock_Alert WHERE MedicineID = {med_id} ORDER BY AlertID DESC")
    st.dataframe(alerts_df, use_container_width=True)

elif page == "👤 Role-Based Views":
    st.subheader("Role-Based Views")
    role = st.selectbox("Select a Role to View As:", ["Pharmacist", "Customer", "Supplier"])

    if role == "Pharmacist":
        st.markdown("### Pharmacist Dashboard")
        st.markdown("#### Full Inventory Status")
        st.dataframe(q_df("SELECT Name, Manufacturer, Price, StockQty, ReorderLevel FROM Medicine ORDER BY Name"), use_container_width=True)
        st.markdown("#### All Sales Orders")
        st.dataframe(q_df("SELECT * FROM Customer_Order_History_View ORDER BY OrderDate DESC"), use_container_width=True)

    elif role == "Customer":
        st.markdown("### Customer Portal")
        customers = q_df("SELECT CustomerID, Name FROM Customer ORDER BY Name")
        if customers.empty: st.warning("No customers in the database."); st.stop()
        cust_map = pd.Series(customers.CustomerID.values, index=customers.Name).to_dict()
        sel_cust_name = st.selectbox("Select a Customer", cust_map.keys())
        if sel_cust_name:
            sel_cust_id = cust_map[sel_cust_name]
            st.markdown(f"#### Available Medicines for Purchase")
            st.dataframe(q_df("SELECT * FROM Available_Medicines_View"), use_container_width=True)
            st.markdown(f"#### Order History for {sel_cust_name}")
            history_df = q_df("SELECT OrderID, OrderDate, MedicineName, Quantity, SellingPrice, LineTotal FROM Customer_Order_History_View WHERE CustomerID = %s ORDER BY OrderDate DESC", (sel_cust_id,))
            st.dataframe(history_df, use_container_width=True)

    elif role == "Supplier":
        st.markdown("### Supplier Portal")
        suppliers = q_df("SELECT SupplierID, Name FROM Supplier ORDER BY Name")
        if suppliers.empty: st.warning("No suppliers in the database."); st.stop()
        sup_map = pd.Series(suppliers.SupplierID.values, index=suppliers.Name).to_dict()
        sel_sup_name = st.selectbox("Select a Supplier", sup_map.keys())
        if sel_sup_name:
            sel_sup_id = sup_map[sel_sup_name]
            st.markdown(f"#### Purchase Order History for {sel_sup_name}")
            history_df = q_df("SELECT OrderID, OrderDate, MedicineName, Quantity, CostPrice, LineTotal FROM Supplier_Purchase_History_View WHERE SupplierID = %s ORDER BY OrderDate DESC", (sel_sup_id,))
            st.dataframe(history_df, use_container_width=True)

# =============================================================
# ⚙️ FOOTER
# =============================================================
st.markdown("<div class='footer'>💊 PharmaDB — CRUD-Enabled Dashboard • Streamlit + MySQL © 2025</div>", unsafe_allow_html=True)
