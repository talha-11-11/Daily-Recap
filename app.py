import streamlit as st
import pandas as pd
import sqlite3
from fpdf import FPDF

# Database connection and table creation
def get_db_connection():
    return sqlite3.connect('mts_sourcing.db')

def create_tables():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('DROP TABLE IF EXISTS customers')
        c.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                customer_name TEXT NOT NULL,
                po_number TEXT NOT NULL,
                required_fabric TEXT,
                required_gsm TEXT,
                yarn_detail TEXT,
                req_width TEXT,
                num_shades INTEGER,
                shade_names TEXT,
                shade_requirements TEXT,
                UNIQUE(customer_name, po_number)
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS daily_recaps (
                date TEXT,
                customer_name TEXT,
                po_number TEXT,
                shade_name TEXT,
                yarn_bags_required INTEGER,
                yarn_bags_received INTEGER,
                balance_yarn_bags INTEGER,
                knitting_required INTEGER,
                knitting_processed INTEGER,
                balance_knitting INTEGER,
                dyeing_required INTEGER,
                dyeing_processed INTEGER,
                balance_dyeing INTEGER
            )
        ''')
        conn.commit()

# Adding customer details
def add_customer():
    st.subheader("Add New Customer")
    name = st.text_input("Customer Name")
    po_number = st.text_input("PO Number")
    fabric = st.text_input("Required Fabric")
    gsm = st.text_input("Required GSM")
    yarn_detail = st.text_input("Yarn Detail")
    req_width = st.text_input("Required Width")
    num_shades = st.number_input("Number of Shades", min_value=1)

    shade_names = []
    shade_requirements = []

    for i in range(num_shades):
        shade_name = st.text_input(f"Shade Name {i + 1}", key=f"shade_name_{i}")
        shade_kg = st.number_input(f"Required KG for {shade_name}", min_value=0, key=f"shade_kg_{i}")
        if shade_name and shade_kg >= 0:
            shade_names.append(shade_name)
            shade_requirements.append(str(shade_kg))

    if st.button("Add Customer"):
        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute(
                    "INSERT INTO customers (customer_name, po_number, required_fabric, required_gsm, yarn_detail, req_width, num_shades, shade_names, shade_requirements) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                    (name, po_number, fabric, gsm, yarn_detail, req_width, num_shades, ','.join(shade_names), ','.join(shade_requirements))
                )
                conn.commit()
                st.success("Customer added!")
                st.experimental_rerun()
        except sqlite3.IntegrityError:
            st.error("Customer with this PO number already exists.")

# Handling daily recaps
def daily_recap():
    st.subheader("Daily Recap")
    with get_db_connection() as conn:
        customers = pd.read_sql_query("SELECT customer_name, po_number FROM customers", conn)

    if customers.empty:
        st.warning("No customers found.")
        return

    customer_options = {f"{row.customer_name} - PO: {row.po_number}": (row.customer_name, row.po_number) for row in customers.itertuples()}
    
    customer_selection = st.selectbox("Select Customer and PO Number", list(customer_options.keys()))
    if not customer_selection:
        st.warning("Please select a customer.")
        return

    selected_customer_name, selected_po_number = customer_options[customer_selection]
    date = st.date_input("Date", value=pd.to_datetime("today"))

    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT shade_names, shade_requirements FROM customers WHERE customer_name = ? AND po_number = ?", 
                  (selected_customer_name, selected_po_number))
        shades_info = c.fetchone()

    if shades_info:
        shade_names = shades_info[0].split(',')
        shade_requirements = list(map(int, shades_info[1].split(',')))

        for i, (shade_name, required_kg) in enumerate(zip(shade_names, shade_requirements)):
            st.subheader(f"Shade: {shade_name.strip()}")

            yarn_bags_required = st.number_input(f"Yarn Bags Required for {shade_name.strip()}", value=required_kg, min_value=0, key=f"yarn_req_{i}")
            yarn_bags_received = st.number_input(f"Yarn Bags Received for {shade_name.strip()}", value=0, min_value=0, key=f"yarn_rec_{i}")
            balance_yarn_bags = yarn_bags_required - yarn_bags_received

            knitting_required = st.number_input(f"Knitting Required for {shade_name.strip()}", value=0, min_value=0, key=f"knit_req_{i}")
            knitting_processed = st.number_input(f"Knitting Processed for {shade_name.strip()}", value=0, min_value=0, key=f"knit_proc_{i}")
            balance_knitting = knitting_required - knitting_processed

            dyeing_required = st.number_input(f"Dyeing Required for {shade_name.strip()}", value=0, min_value=0, key=f"dye_req_{i}")
            dyeing_processed = st.number_input(f"Dyeing Processed for {shade_name.strip()}", value=0, min_value=0, key=f"dye_proc_{i}")
            balance_dyeing = dyeing_required - dyeing_processed

            if st.button(f"Add Daily Recap for {shade_name.strip()}", key=f"add_recap_{i}"):
                try:
                    with get_db_connection() as conn:
                        c = conn.cursor()
                        c.execute(
                            """INSERT INTO daily_recaps (date, customer_name, po_number, shade_name, yarn_bags_required, yarn_bags_received, balance_yarn_bags, knitting_required, knitting_processed, balance_knitting, dyeing_required, dyeing_processed, balance_dyeing) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (date, selected_customer_name, selected_po_number, shade_name.strip(), 
                             int(yarn_bags_required), int(yarn_bags_received), balance_yarn_bags, 
                             int(knitting_required), int(knitting_processed), balance_knitting, 
                             int(dyeing_required), int(dyeing_processed), balance_dyeing)
                        )
                        conn.commit()
                    st.success(f"Daily recap added for {shade_name.strip()}!")
                except Exception as e:
                    st.error(f"Error adding daily recap: {e}")
    else:
        st.warning("No shade information found for the selected customer and PO number.")

# Generating PDF reports
def generate_report():
    st.subheader("Generate Report")
    date = st.date_input("Select Date for Report")
    
    with get_db_connection() as conn:
        report_data = pd.read_sql_query(f"SELECT * FROM daily_recaps WHERE date = '{date}'", conn)

    if st.button("Download PDF Report"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, f"Daily Recap - {date}", 0, 1, 'C')

        pdf.set_font("Arial", 'B', 10)
        col_names = ["Customer Name", "PO Number", "Shade Name", "Yarn Bags Required", "Yarn Bags Received", 
                     "Balance Yarn Bags", "Knitting Required", "Processed Knitting", "Balance Knitting", 
                     "Dyeing Required", "Processed Dyeing", "Balance Dyeing"]
        col_widths = [30, 30, 30, 40, 40, 40, 40, 40, 40, 40, 40, 40]

        for col, width in zip(col_names, col_widths):
            pdf.cell(width, 10, col, 1)
        pdf.ln()

        pdf.set_font("Arial", '', 10)
        for row in report_data.itertuples():
            pdf.cell(30, 10, row.customer_name, 1)
            pdf.cell(30, 10, row.po_number, 1)
            pdf.cell(30, 10, row.shade_name, 1)
            pdf.cell(40, 10, str(row.yarn_bags_required), 1)
            pdf.cell(40, 10, str(row.yarn_bags_received), 1)
            pdf.cell(40, 10, str(row.balance_yarn_bags), 1)
            pdf.cell(40, 10, str(row.knitting_required), 1)
            pdf.cell(40, 10, str(row.knitting_processed), 1)
            pdf.cell(40, 10, str(row.balance_knitting), 1)
            pdf.cell(40, 10, str(row.dyeing_required), 1)
            pdf.cell(40, 10, str(row.dyeing_processed), 1)
            pdf.cell(40, 10, str(row.balance_dyeing), 1)
            pdf.ln()

        pdf.output(f"daily_recap_{date}.pdf")
        st.success(f"Report for {date} downloaded!")

# Streamlit UI
st.title("MTS Sourcing Daily Recap App")
create_tables()

menu = st.sidebar.selectbox("Select Option", ["Add Customer", "Daily Recap", "Generate Report"])

if menu == "Add Customer":
    add_customer()
elif menu == "Daily Recap":
    daily_recap()
elif menu == "Generate Report":
    generate_report()
