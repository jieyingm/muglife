import streamlit as st
import pandas as pd
import random
import io
from datetime import datetime
import sqlite3
import hashlib

# Fixed branches for the business
FIXED_BRANCHES = ["KLCC", "TRX", "Seri Iskandar"]

# Coffee Menu Prices
coffee_menu = {
    'Americano': {'small': 3.75, 'medium': 5.00, 'large': 7.50},
    'Cappuccino': {'small': 5.00, 'medium': 6.50, 'large': 8.00},
    'Latte': {'small': 5.25, 'medium': 6.75, 'large': 8.25},
    'Caramel Macchiato': {'small': 4.50, 'medium': 7.00, 'large': 9.50}
}

# Prices for add-ons
add_on_prices = {
    'Extra sugar': 0.70,  # Extra 5g of sugar
    'Extra milk': 0.90,   # Extra 30ml of milk
}

# Ingredient usage per coffee type and size
ingredient_usage = {
    'Americano': {
        'small': {'coffee_beans': 9, 'milk': 10, 'sugar': 5},
        'medium': {'coffee_beans': 12, 'milk': 10, 'sugar': 5},
        'large': {'coffee_beans': 15, 'milk': 10, 'sugar': 5}
    },
    'Cappuccino': {
        'small': {'coffee_beans': 9, 'milk': 60, 'sugar': 5},
        'medium': {'coffee_beans': 12, 'milk': 80, 'sugar': 5},
        'large': {'coffee_beans': 15, 'milk': 100, 'sugar': 5}
    },
    'Latte': {
        'small': {'coffee_beans': 9, 'milk': 100, 'sugar': 5},
        'medium': {'coffee_beans': 12, 'milk': 150, 'sugar': 5},
        'large': {'coffee_beans': 15, 'milk': 200, 'sugar': 5}
    },
    'Caramel Macchiato': {
        'small': {'coffee_beans': 9, 'milk': 90, 'sugar': 5},
        'medium': {'coffee_beans': 12, 'milk': 130, 'sugar': 5},
        'large': {'coffee_beans': 15, 'milk': 180, 'sugar': 5}
    }
}

# Extra usage for additional sugar and milk
extra_usage = {
    'milk': 30,   # Extra 30ml of milk for "Extra milk"
    'sugar': 5    # Extra 5g of sugar for "Extra sugar"
}

if 'loyalty_points' not in st.session_state:
    st.session_state['loyalty_points'] = 0  # Track customer loyalty points



# Database connection and setup
conn = sqlite3.connect('coffee_shop.db')
c = conn.cursor()

# Create tables for customers and admins if they don't exist
c.execute('''CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT,
                favorite_order TEXT
            )''')
c.execute('''CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT
            )''')
conn.commit()

# Function to hash passwords for security
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Sign-up function for new users
def signup(username, password, is_admin=False):
    password_hashed = hash_password(password)
    table = 'admins' if is_admin else 'customers'
    try:
        c.execute(f"INSERT INTO {table} (username, password) VALUES (?, ?)", (username, password_hashed))
        conn.commit()
        st.success(f"Account created successfully for {'admin' if is_admin else 'customer'}!")
    except sqlite3.IntegrityError:
        st.error("Username already exists.")

# Login function for existing users
def login(username, password, is_admin=False):
    password_hashed = hash_password(password)
    table = 'admins' if is_admin else 'customers'
    c.execute(f"SELECT * FROM {table} WHERE username=? AND password=?", (username, password_hashed))
    user = c.fetchone()
    return user

# Session management (added logout functionality)
def logout():
    # Clear session state to logout
    if 'user' in st.session_state:
        del st.session_state['user']
        del st.session_state['is_admin']
        st.success("You have been logged out.")
        st.rerun()  # Refresh to go back to the login page

# Streamlit UI for user authentication
# Authentication and user login/signup logic

def display_about_page():
    st.markdown("<h3 style='color: #3D3D3D;'>☕ About Mug Life</h3>", unsafe_allow_html=True)
    st.write(
        """
        Mug Life, located in Seri Iskandar, is a coffee shop designed to cater to the needs of busy students at 
        Universiti Teknologi PETRONAS (UTP). The goal of Mug Life is to offer good coffee and a friendly ambiance 
        for students to grab a drink, get some work done, or just hang out.
        """
    )

    st.markdown("<h4 style='color: #3D3D3D;'>📋 Team Members</h4>", unsafe_allow_html=True)

    # Display team member details in a clean table format
    team_data = {
        "Name": ["Melson Jens", "Chin Yi Han", "Moong Jie Ying", "Muhammad Farhan Bin Anuar"],
        "Student ID": ["21000536", "21002463", "20001884", "21002286"],
        "Program": ["Computer Science", "Computer Science", "Information Technology", "Information Technology"]
    }
    team_df = pd.DataFrame(team_data)
    st.table(team_df)

    # Add a button to proceed to login/signup
    if st.button("Proceed to Login or Sign Up"):
        st.session_state.show_about = False  # Move to the login/signup screen

def authenticate_user():
    # Show About page by default
    if 'show_about' not in st.session_state:
        st.session_state.show_about = True

    if st.session_state.show_about:
        display_about_page()
    else:
        if 'user' in st.session_state:
            st.write(f"Welcome back, {st.session_state['user']}!")

            if st.session_state.get('is_admin'):
                if 'admin_branch' not in st.session_state:
                    st.session_state['admin_branch'] = None

                if not st.session_state['admin_branch']:
                    selected_branch = st.selectbox("Select your branch:", FIXED_BRANCHES)
                    if st.button("Confirm Branch"):
                        st.session_state['admin_branch'] = selected_branch
                        st.success(f"Branch selected: {selected_branch}")
                        st.experimental_rerun()  # Reload to apply changes

            # Logout option
            if st.button('Logout'):
                logout()
        else:
            # Login/Signup logic
            choice = st.sidebar.selectbox("Login/Signup", ["Login", "Sign up"])
            is_admin = st.sidebar.checkbox("Admin")

            username = st.sidebar.text_input("Username")
            password = st.sidebar.text_input("Password", type="password")

            if choice == "Sign up":
                if st.sidebar.button("Create Account"):
                    signup(username, password, is_admin)
            elif choice == "Login":
                if st.sidebar.button("Login"):
                    user = login(username, password, is_admin)
                    if user:
                        st.session_state['user'] = username
                        st.session_state['is_admin'] = is_admin
                        st.success(f"Welcome {'Admin' if is_admin else 'Customer'} {username}!")
                        if is_admin:
                            st.rerun()  # Refresh to unlock admin features
                    else:
                        st.error("Incorrect username or password.")



# Initialize Streamlit Session State to retain data across app interactions
if 'branch_inventory' not in st.session_state:
    st.session_state.branch_inventory = {branch: {
        "coffee_beans": 1000,
        "milk": 1000,
        "sugar": 1000,
        "cups": 500
    } for branch in FIXED_BRANCHES}



if 'sales_data' not in st.session_state:
    st.session_state.sales_data = pd.DataFrame(columns=[
        'Order Number', 'Customer Name', 'Coffee Type', 'Quantity',
        'Size', 'Add-ons', 'Price', 'Time', 'Status', 'Branch'
    ])
    
if 'order_history' not in st.session_state:
    st.session_state.order_history = {}

# Initialize order_numbers set in session state
if 'order_numbers' not in st.session_state:
    st.session_state.order_numbers = set()

# Initialize restock_history in session state
if 'restock_history' not in st.session_state:
    st.session_state.restock_history = []

# Initialize session state for coupons if not already initialized
if 'coupons' not in st.session_state:
    st.session_state.coupons = []

if 'feedback' not in st.session_state:
    st.session_state.feedback = []

# Function to generate unique 4-digit order number
def generate_unique_order_number():
    existing_numbers = st.session_state.get('order_numbers', set())  # Get existing order numbers from session state

    # Generate a unique order number
    while True:
        new_number = random.randint(1000, 9999)
        if new_number not in existing_numbers:
            st.session_state.order_numbers.add(new_number)
            return new_number

# JavaScript function to refresh the page
def js_refresh():
    st.markdown("""<script>window.location.reload()</script>""", unsafe_allow_html=True)

# Kitchen Orders Interface with box-styled layout
def display_kitchen_orders():
    st.markdown("<h3>👨‍🍳 Kitchen Orders</h3>", unsafe_allow_html=True)

    if 'admin_branch' in st.session_state and st.session_state['admin_branch']:
        branch = st.session_state['admin_branch']

        # Validate if the Branch column exists in sales data
        if 'Branch' not in st.session_state.sales_data.columns:
            st.error("Branch column is missing in sales data.")
            return

        # Filter orders for the selected branch
        branch_orders = st.session_state.sales_data[
            st.session_state.sales_data['Branch'] == branch
        ]
        kitchen_orders = branch_orders[branch_orders['Status'] == 'Being Processed']

        if not kitchen_orders.empty:
            st.markdown(f"### Orders in Progress for {branch} Branch")

            for idx, order in kitchen_orders.iterrows():
                st.markdown(
                    f"""
                    <div style='border: 1px solid #d9d9d9; border-radius: 10px; padding: 15px; margin-bottom: 10px; background-color: #f9f9f9;'>
                        <strong>Order #{order['Order Number']}</strong><br>
                        <strong>Customer:</strong> {order['Customer Name']}<br>
                        <strong>Coffee:</strong> {order['Coffee Type']} ({order['Size']})<br>
                        <strong>Add-ons:</strong> {order['Add-ons']}<br>
                        <strong>Order Time:</strong> {order['Time']}<br>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # Button to mark the order as ready
                if st.button(f"Mark Order #{order['Order Number']} as Ready", key=f"ready_{order['Order Number']}"):
                    st.session_state.sales_data.at[idx, 'Status'] = 'Ready'
                    st.success(f"Order #{order['Order Number']} marked as ready.")
        else:
            st.info(f"No active orders for the branch: {branch}.")
    else:
        st.error("Please select a branch to view kitchen orders.")


# Front Page Coffee Menu Display with clean, professional, and bright formatting
from datetime import datetime
import streamlit as st

# Define daily special offers
def get_daily_special():
    # Define daily special offers
    daily_offers = {
        "Monday": {"offer": "20% off on all Americano!", "coffee": "Americano", "discount": 0.20},
        "Tuesday": {"offer": "30% off on all Cappuccino!", "coffee": "Cappuccino", "discount": 0.30},
        "Wednesday": {"offer": "40% off on all Latte!", "coffee": "Latte", "discount": 0.40},
        "Thursday": {"offer": "50% off on all Caramel Macchiato!", "coffee": "Caramel Macchiato", "discount": 0.50},
        "Friday": {"offer": "15% off on all coffees!", "coffee": None, "discount": 0.15},
        "Saturday": {"offer": "15% off on all coffees!", "coffee": None, "discount": 0.15},
        "Sunday": {"offer": "15% off on all coffees!", "coffee": None, "discount": 0.15},
    }

    # Get today's special based on the current day
    today = datetime.now().strftime("%A")
    return daily_offers.get(today, {})


# Coffee menu display with the daily special offer
def display_menu():
    # Display the daily special offer
    daily_special = get_daily_special()
    offer_text = daily_special.get("offer", "No special offer today!")
    st.markdown(f"<h3 style='color: #3D3D3D;'>🎉 Today's Special Offer: {offer_text}</h3>", unsafe_allow_html=True)
    

    st.markdown("""
        <style>
            .menu-container {
                background-color: #ffffff;
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
                margin-bottom: 40px;
            }
            .menu-title {
                color: #2C3E50;
                font-size: 28px;
                font-weight: bold;
                margin-bottom: 25px;
                text-align: center;
            }
            .menu-item-box {
                background-color: #f9f9f9;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.05);
                margin-bottom: 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .item-title {
                font-size: 22px;
                font-weight: bold;
                color: #34495E;
            }
            .item-prices {
                font-size: 18px;
                color: #3498DB;
                text-align: right;
            }
            .addon-section {
                margin-top: 30px;
                background-color: #f9f9f9;
                padding: 15px;
                border-radius: 10px;
                box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.05);
            }
            .addon-title {
                font-size: 20px;
                font-weight: bold;
                color: #27AE60;
                margin-bottom: 10px;
            }
            .addon-item {
                font-size: 16px;
                color: #2C3E50;
                margin-top: 5px;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='menu-title'>📋 Our Coffee Menu</div>", unsafe_allow_html=True)

    # Main menu container
    st.markdown("<div class='menu-container'>", unsafe_allow_html=True)

    # Styling each coffee item with box-style layout
    for coffee, sizes in coffee_menu.items():
        st.markdown(
            f"""
            <div class="menu-item-box">
                <div class="item-title">{coffee}</div>
                <div class="item-prices">
                    Small: RM{sizes['small']:.2f} <br>
                    Medium: RM{sizes['medium']:.2f} <br>
                    Large: RM{sizes['large']:.2f}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # Clean Add-ons section in a box
    st.markdown(
        f"""
        <div class="addon-section">
            <div class="addon-title">Add-ons</div>
            <div class="addon-item">Extra sugar: RM{add_on_prices['Extra sugar']:.2f}</div>
            <div class="addon-item">Extra milk: RM{add_on_prices['Extra milk']:.2f}</div>
        </div>
        """, unsafe_allow_html=True
    )

    # Divider line to keep the layout neat and clean
    st.markdown("<hr style='margin-top: 30px; border: none; border-top: 2px solid #3498DB;'>", unsafe_allow_html=True)




# Prices for restock items
restock_prices = {
    'coffee_beans': 1.20,  # RM per 100g
    'milk': 0.70,          # RM per 100ml
    'sugar': 0.20,         # RM per 100g
    'cups': 0.02           # RM per cup
}



def display_inventory():
    st.markdown("<h3 style='color: #3D3D3D;'>📦 Inventory Management</h3>", unsafe_allow_html=True)
    st.write("Here's a summary of the current inventory levels for essential items:")

    # Display current inventory in a clean, modern, and professional table
    st.markdown("### Current Stock Levels:")
    st.markdown(
        f"""
        <style>
            .inventory-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                font-size: 18px;
                text-align: left;
            }}
            .inventory-table th, .inventory-table td {{
                padding: 12px 15px;
                border: 1px solid #ddd;
            }}
            .inventory-table th {{
                background-color: #f4f4f4;
                font-weight: bold;
                color: #333;
            }}
            .inventory-table td {{
                background-color: #ffffff;
                color: #555;
            }}
            .inventory-table tbody tr:nth-child(even) td {{
                background-color: #f9f9f9;
            }}
        </style>

        <table class="inventory-table">
            <thead>
                <tr>
                    <th>Item</th>
                    <th>Current Quantity</th>
                    <th>Unit</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Coffee Beans</td>
                    <td>{st.session_state.inventory['coffee_beans']}</td>
                    <td>grams</td>
                </tr>
                <tr>
                    <td>Milk</td>
                    <td>{st.session_state.inventory['milk']}</td>
                    <td>milliliters</td>
                </tr>
                <tr>
                    <td>Sugar</td>
                    <td>{st.session_state.inventory['sugar']}</td>
                    <td>grams</td>
                </tr>
                <tr>
                    <td>Cups</td>
                    <td>{st.session_state.inventory['cups']}</td>
                    <td>units</td>
                </tr>
            </tbody>
        </table>
        """,
        unsafe_allow_html=True
    )


    # Display restock prices under current stock levels in a modern and clean style
    st.markdown("### 🛒 Restock Price Menu:")
    st.markdown(
        f"""
        <style>
            .restock-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                font-size: 18px;
                text-align: left;
            }}
            .restock-table th, .restock-table td {{
                padding: 12px 15px;
                border: 1px solid #ddd;
            }}
            .restock-table th {{
                background-color: #f4f4f4;
                font-weight: bold;
            }}
            .restock-table td {{
                background-color: #ffffff;
            }}
            .restock-table tbody tr:nth-child(even) td {{
                background-color: #f9f9f9;
            }}
        </style>

        <table class="restock-table">
            <thead>
                <tr>
                    <th>Item</th>
                    <th>Price</th>
                    <th>Unit</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Coffee Beans</td>
                    <td>RM{restock_prices['coffee_beans']:.2f}</td>
                    <td>per 100g</td>
                </tr>
                <tr>
                    <td>Milk</td>
                    <td>RM{restock_prices['milk']:.2f}</td>
                    <td>per 100ml</td>
                </tr>
                <tr>
                    <td>Sugar</td>
                    <td>RM{restock_prices['sugar']:.2f}</td>
                    <td>per 100g</td>
                </tr>
                <tr>
                    <td>Cups</td>
                    <td>RM{restock_prices['cups']:.2f}</td>
                    <td>per cup</td>
                </tr>
            </tbody>
        </table>
        """, 
        unsafe_allow_html=True
    )

    # Manual Restock Section
    st.markdown("### 🔄 Manual Restock:")
    item_to_restock = st.selectbox("Select item to restock", list(st.session_state.inventory.keys()))
    restock_amount = st.number_input("Enter restock amount", min_value=0, step=10)

    # Calculate restock cost
    cost = 0
    if item_to_restock == "coffee_beans":
        cost = (restock_amount / 100) * restock_prices['coffee_beans']
    elif item_to_restock == "milk":
        cost = (restock_amount / 100) * restock_prices['milk']
    elif item_to_restock == "sugar":
        cost = (restock_amount / 100) * restock_prices['sugar']
    elif item_to_restock == "cups":
        cost = restock_amount * restock_prices['cups']

    # Display restock cost
    if restock_amount > 0:
        st.write(f"💵 **Restock Cost:** RM{cost:.2f}")

    # Restock and update history
    if st.button("Restock", key="restock"):
        if restock_amount > 0:
            st.session_state.inventory[item_to_restock] += restock_amount
            st.success(f"Restocked **{item_to_restock}** by **{restock_amount}**. New total: **{st.session_state.inventory[item_to_restock]}**")
            st.write(f"💵 Total Restock Cost: RM{cost:.2f}")
            # Save restock history
            st.session_state.restock_history.append({
                'Item': item_to_restock,
                'Amount': restock_amount,
                'Cost': cost,
                'Time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        else:
            st.warning("Please enter a valid restock amount.")

    # Display restock history
    display_restock_history()

def display_restock_history():
    st.markdown("<h3 style='color: #3D3D3D;'>📦 Restock History</h3>", unsafe_allow_html=True)

    # Ensure there is restock history to display
    if 'restock_history' in st.session_state and st.session_state.restock_history:
        # Convert restock history to a DataFrame for table display
        df = pd.DataFrame(st.session_state.restock_history)

        # Display restock history in a table format using Streamlit's data frame display
        st.markdown("<h4 style='color: #2C3E50;'>Restock History Table</h4>", unsafe_allow_html=True)

        # Display the table with headers and professional formatting
        st.dataframe(df.style.format({"Amount": "{:.0f}", "Cost": "RM{:.2f}", "Time": "{:%Y-%m-%d %H:%M:%S}"}))
    else:
        st.write("No restock history available.")



# Function to display and download restock history in text file format (invoice)
def display_restock_history():
    st.markdown("<h3 style='color: #3D3D3D;'>📦 Restock History</h3>", unsafe_allow_html=True)

    # Ensure there is restock history to display
    if 'restock_history' in st.session_state and st.session_state.restock_history:
        # Convert restock history to a DataFrame for table display
        df = pd.DataFrame(st.session_state.restock_history)

        # Display restock history in a table format using Streamlit's data frame display
        st.write(df)

        # Generate invoice button
        if st.button("Generate Invoice"):
            generate_invoice()
    else:
        st.write("No restock history available.")




# Function to generate and download invoice as a text file
def generate_invoice():
    if 'restock_history' in st.session_state and st.session_state.restock_history:
        # Create invoice text
        invoice_text = "Coffee Shop Restock Invoice\n"
        invoice_text += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        invoice_text += "-------------------------------------------------\n"
        invoice_text += "| Item              | Amount    | Cost (RM) | Time           |\n"
        invoice_text += "-------------------------------------------------\n"
        
        total_cost = 0
        for restock in st.session_state.restock_history:
            total_cost += restock['Cost']
            invoice_text += f"| {restock['Item']:<17} | {restock['Amount']:<8} | RM{restock['Cost']:<9.2f} | {restock['Time']:<15} |\n"

        invoice_text += "-------------------------------------------------\n"
        invoice_text += f"Total Cost: RM{total_cost:.2f}\n"

        # Create a downloadable text file
        invoice_bytes = io.BytesIO(invoice_text.encode('utf-8'))

        # Add download button
        st.download_button(
            label="Download Invoice",
            data=invoice_bytes,
            file_name=f"restock_invoice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
    else:
        st.write("No restock history available to generate an invoice.")

import matplotlib.pyplot as plt

# Update the sales report to include the actual final price after discount (which is the price customer pays)
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime


def sales_report():
    st.markdown("<h3 style='color: #3D3D3D; text-align: center;'>📊 Sales Report</h3>", unsafe_allow_html=True)

    if 'admin_branch' not in st.session_state or not st.session_state['admin_branch']:
        st.error("Please select a branch to view the sales report.")
        return

    branch = st.session_state['admin_branch']
    branch_sales_data = st.session_state.sales_data[st.session_state.sales_data['Branch'] == branch]

    # Choose report period
    report_period = st.radio("Select Report Period:", ["Daily", "Weekly", "Monthly"], index=0, key="report_period")

    # Filter sales data based on the selected period
    if report_period == "Daily":
        filtered_data = branch_sales_data[branch_sales_data['Time'].str.contains(datetime.now().strftime("%Y-%m-%d"))]
    elif report_period == "Weekly":
        filtered_data = branch_sales_data[pd.to_datetime(branch_sales_data['Time']) >= pd.Timestamp(datetime.now()) - pd.Timedelta(days=7)]
    else:  # Monthly report
        filtered_data = branch_sales_data[pd.to_datetime(branch_sales_data['Time']).dt.to_period('M') == pd.Timestamp(datetime.now()).to_period('M')]

    # Exclude orders with RM0.00 from revenue calculations
    filtered_data = filtered_data[filtered_data['Price'] > 0]

    if not filtered_data.empty:
        # Total Sales Report
        total_revenue = filtered_data['Price'].sum()
        total_quantity = filtered_data['Quantity'].sum()
        st.markdown(f"<strong style='font-size:18px;'>Total Revenue for {branch}:</strong> RM{total_revenue:.2f}", unsafe_allow_html=True)
        st.markdown(f"<strong style='font-size:18px;'>Total Quantity Sold:</strong> {total_quantity} cups", unsafe_allow_html=True)

        # Sales Breakdown by Coffee Type
        coffee_sales = filtered_data.groupby('Coffee Type')['Quantity'].sum().reset_index()
        st.markdown(f"### Sales Breakdown by Coffee Type ({branch})")
        st.bar_chart(coffee_sales.set_index('Coffee Type'))

        # Best and Worst Sellers
        best_selling = coffee_sales.loc[coffee_sales['Quantity'].idxmax()]['Coffee Type']
        least_popular = coffee_sales.loc[coffee_sales['Quantity'].idxmin()]['Coffee Type']
        st.write(f"**Best-Selling Coffee Type:** {best_selling}")
        st.write(f"**Least Popular Coffee Type:** {least_popular}")

        # Coffee Sales Distribution Pie Chart
        st.markdown(f"<h4 style='text-align: center;'>Coffee Sales Distribution ({branch})</h4>", unsafe_allow_html=True)
        fig1, ax1 = plt.subplots()
        ax1.pie(coffee_sales['Quantity'], labels=coffee_sales['Coffee Type'], autopct='%1.1f%%', startangle=90)
        ax1.axis('equal')
        st.pyplot(fig1)

        # Ingredient usage calculation based on sales
        total_beans_used = total_milk_used = total_sugar_used = total_cups_used = 0

        for idx, order in filtered_data.iterrows():
            coffee_type = order['Coffee Type']
            size = order['Size']

            # Check if the coffee type and size exist in ingredient_usage
            if coffee_type in ingredient_usage and size in ingredient_usage[coffee_type]:
                beans_used = ingredient_usage[coffee_type][size]['coffee_beans'] * order['Quantity']
                milk_used = ingredient_usage[coffee_type][size]['milk'] * order['Quantity']
                sugar_used = ingredient_usage[coffee_type][size]['sugar'] * order['Quantity']

                total_beans_used += beans_used
                total_milk_used += milk_used
                total_sugar_used += sugar_used

                # Add extra ingredient usage for add-ons
                if 'Extra sugar' in order['Add-ons']:
                    total_sugar_used += extra_usage['sugar'] * order['Quantity']
                if 'Extra milk' in order['Add-ons']:
                    total_milk_used += extra_usage['milk'] * order['Quantity']

        total_cups_used = filtered_data['Quantity'].sum()

        # Inventory cost calculations based on the usage of ingredients
        branch_inventory = st.session_state['current_inventory']
        branch_inventory_cost = (
            (total_beans_used / 100) * restock_prices['coffee_beans'] +
            (total_milk_used / 100) * restock_prices['milk'] +
            (total_sugar_used / 100) * restock_prices['sugar'] +
            total_cups_used * restock_prices['cups']
        )

        # Calculate total profit
        total_profit = total_revenue - branch_inventory_cost
        total_profit = max(0, total_profit)  # Prevent negative profit

        # Ingredient Usage Summary
        ingredient_usage_summary = {
            'Ingredient': ['Coffee Beans (g)', 'Milk (ml)', 'Sugar (g)', 'Cups'],
            'Amount Used': [total_beans_used, total_milk_used, total_sugar_used, total_cups_used],
        }
        ingredient_df = pd.DataFrame(ingredient_usage_summary)
        st.markdown(f"<h4 style='text-align: center;'>Ingredient Usage Summary ({branch})</h4>", unsafe_allow_html=True)
        st.dataframe(ingredient_df)

        # Stacked Bar Chart for Total Revenue, Inventory Cost, and Profit
        st.markdown(f"<h4 style='text-align: center;'>Revenue, Inventory Cost, and Profit Breakdown ({branch})</h4>", unsafe_allow_html=True)
        fig, ax = plt.subplots()
        categories = ['Total Revenue', 'Inventory Cost', 'Profit']
        values = [total_revenue, branch_inventory_cost, total_profit]

        ax.bar(categories, values, color=['#66B3FF', '#FF9999', '#99FF99'])
        ax.set_ylabel('Amount (RM)')
        ax.set_title(f'Financial Overview ({branch})')
        st.pyplot(fig)

        # Display Total Inventory Cost and Profit
        # Correct HTML rendering with calculated data
        st.markdown(f"<strong style='font-size:18px;'>Total Inventory Cost (Including Restocking):</strong> RM{branch_inventory_cost:.2f}", unsafe_allow_html=True)
        st.markdown(f"<strong style='font-size:18px;'>Total Profit:</strong> RM{total_profit:.2f}", unsafe_allow_html=True)

    else:
        st.write(f"No sales data available for the selected period at {branch}.")


#Order History
def display_order_history():
    st.markdown("<h3>📜 Order History</h3>", unsafe_allow_html=True)

    if 'admin_branch' not in st.session_state or not st.session_state['admin_branch']:
        st.error("Please select a branch to view the order history.")
        return

    branch = st.session_state['admin_branch']
    if 'Branch' not in st.session_state.sales_data.columns:
        st.error("Branch column is missing in sales data.")
        return

    branch_orders = st.session_state.sales_data[
        st.session_state.sales_data['Branch'] == branch
    ]

    if not branch_orders.empty:
        st.dataframe(branch_orders[['Order Number', 'Customer Name', 'Coffee Type', 'Size', 'Add-ons', 'Price', 'Time', 'Status']])
    else:
        st.info(f"No orders have been placed for the branch: {branch}.")




# Customer Feedback Form
def feedback_form():
    st.markdown("<h3 style='color: #3D3D3D;'>💬 Submit Your Feedback</h3>", unsafe_allow_html=True)

    name = st.text_input("Name")
    coffee_purchased = st.selectbox("Select Coffee Purchased", list(coffee_menu.keys()))
    coffee_rating = st.slider("Rate the Coffee (1-5)", 1, 5, 3)
    service_rating = st.slider("Rate the Service (1-5)", 1, 5, 3)
    additional_feedback = st.text_area("Any additional comments?")
    branch = st.selectbox("Select Branch", FIXED_BRANCHES)  # New branch selection

    if st.button("Submit Feedback"):
        # Ensure feedback is tied to a branch
        feedback_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_feedback = {
            'Name': name,
            'Coffee Purchased': coffee_purchased,
            'Coffee Rating': coffee_rating,
            'Service Rating': service_rating,
            'Additional Feedback': additional_feedback,
            'Branch': branch,  # New branch data
            'Time': feedback_time
        }
        st.session_state.feedback.append(new_feedback)
        st.success("Thank you for your feedback!")


def analytics_dashboard():
    st.markdown("<h3 style='color: #3D3D3D;'>📈 Analytics Dashboard</h3>", unsafe_allow_html=True)
    st.write("Real-time stats on orders, inventory, and sales.")

    # Check if a branch has been selected
    if 'admin_branch' not in st.session_state or not st.session_state['admin_branch']:
        st.error("Please select a branch to view the analytics.")
        return

    branch = st.session_state['admin_branch']
    branch_inventory = st.session_state.branch_inventory.get(branch)

    if branch_inventory:
        # Display the order count and total revenue for the selected branch
        branch_sales_data = st.session_state.sales_data[st.session_state.sales_data['Branch'] == branch]
        total_revenue = branch_sales_data['Price'].sum()
        st.metric(label="Total Orders", value=len(branch_sales_data))
        st.metric(label="Total Revenue", value=f"RM{total_revenue:.2f}")

        # Display inventory for the selected branch
        st.markdown(f"### {branch} Branch Inventory")
        st.markdown(
            f"""
            <div style='display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 20px;'>
                <div style='flex: 1; border: 1px solid #d9d9d9; border-radius: 10px; padding: 20px; background-color: #f9f9f9;'>
                    <strong>Coffee Beans:</strong> {branch_inventory['coffee_beans']} g
                </div>
                <div style='flex: 1; border: 1px solid #d9d9d9; border-radius: 10px; padding: 20px; background-color: #f9f9f9;'>
                    <strong>Milk:</strong> {branch_inventory['milk']} ml
                </div>
                <div style='flex: 1; border: 1px solid #d9d9d9; border-radius: 10px; padding: 20px; background-color: #f9f9f9;'>
                    <strong>Sugar:</strong> {branch_inventory['sugar']} g
                </div>
                <div style='flex: 1; border: 1px solid #d9d9d9; border-radius: 10px; padding: 20px; background-color: #f9f9f9;'>
                    <strong>Cups:</strong> {branch_inventory['cups']} units
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Estimate how many cups can be made with the current inventory for the selected branch
        average_beans_per_cup = 12  # g
        average_milk_per_cup = 80   # ml
        average_sugar_per_cup = 5   # g

        max_cups_beans = branch_inventory['coffee_beans'] // average_beans_per_cup
        max_cups_milk = branch_inventory['milk'] // average_milk_per_cup
        max_cups_sugar = branch_inventory['sugar'] // average_sugar_per_cup
        max_cups = min(max_cups_beans, max_cups_milk, max_cups_sugar, branch_inventory['cups'])

        st.markdown(f"☕ **Estimated Cups You Can Make at {branch}**: {max_cups} cups")
        st.write(f"- Based on current inventory, you can make approximately **{max_cups}** more cups of coffee at {branch}.")

        # Inventory Health Alerts for the selected branch
        st.markdown("<h5 style='color: #FF4136;'>⚠️ Inventory Health Alerts</h5>", unsafe_allow_html=True)
        low_stock_items = []
        if branch_inventory['coffee_beans'] < 200:
            low_stock_items.append(("Coffee Beans", branch_inventory['coffee_beans'], 'g'))
        if branch_inventory['milk'] < 200:
            low_stock_items.append(("Milk", branch_inventory['milk'], 'ml'))
        if branch_inventory['sugar'] < 200:
            low_stock_items.append(("Sugar", branch_inventory['sugar'], 'g'))
        if branch_inventory['cups'] < 20:
            low_stock_items.append(("Cups", branch_inventory['cups'], 'units'))

        if low_stock_items:
            for item, quantity, unit in low_stock_items:
                st.markdown(
                    f"""
                    <div style='border: 1px solid #FF4136; border-radius: 10px; padding: 20px; margin-bottom: 20px; background-color: #ffe6e6;'>
                        <strong style="color: #FF4136;">{item} is low on stock!</strong><br>
                        <span>Current Quantity: <strong>{quantity} {unit}</strong></span>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
        else:
            st.success(f"✔️ All inventory levels at {branch} are sufficient.")
    else:
        st.error(f"No inventory data available for the branch: {branch}.")


# Customer-facing section (Coffee Menu, Order Coffee, and Feedback)
def customer_interface():
    st.sidebar.title("Customer Menu")
    selection = st.sidebar.radio("Choose a page:", ["Coffee Menu", "Order Coffee", "Order Status Dashboard", "Feedback", "Loyalty Program",])

    if selection == "Coffee Menu":
        display_menu()
    elif selection == "Order Coffee":
        take_order()
    elif selection == "Order Status Dashboard":
        display_order_status()
    elif selection == "Feedback":
        feedback_form()
    elif selection == "Loyalty Program":
        loyalty_program()




# Display order status for customers with a box-styled layout for each order and the pickup button
def display_order_status():
    st.markdown("<h3 style='color: #3D3D3D;'>📊 Order Status Dashboard</h3>", unsafe_allow_html=True)
    
    # Display orders that are being processed
    processing_orders = st.session_state.sales_data[st.session_state.sales_data['Status'] == 'Being Processed']
    ready_orders = st.session_state.sales_data[st.session_state.sales_data['Status'] == 'Ready']

    # Orders being processed
    st.subheader("Orders Being Processed")
    if not processing_orders.empty:
        st.write(processing_orders[['Order Number', 'Customer Name', 'Coffee Type', 'Time']])
    else:
        st.write("No orders are being processed.")

    # Orders ready for pickup with formatted boxes
    st.subheader("Orders Ready for Pickup")
    if not ready_orders.empty:
        for idx, order in ready_orders.iterrows():
            st.markdown(
                f"""
                <div style='border: 1px solid #d9d9d9; border-radius: 10px; padding: 15px; margin-bottom: 10px; background-color: #f9f9f9;'>
                    <strong>Order #{order['Order Number']}</strong><br>
                    <strong>Customer:</strong> {order['Customer Name']}<br>
                    <strong>Coffee:</strong> {order['Coffee Type']} ({order['Size']})<br>
                    <strong>Add-ons:</strong> {order['Add-ons']}<br>
                    <strong>Order Time:</strong> {order['Time']}<br>
                </div>
                """, unsafe_allow_html=True
            )
            if st.button(f"Picked Up #{order['Order Number']}", key=f"pickup_{order['Order Number']}"):
                # Remove the order from the sales data by updating the status
                st.session_state.sales_data.drop(idx, inplace=True)
                st.success(f"Order #{order['Order Number']} has been picked up!")
    else:
        st.write("No orders are ready for pickup.")

# Function to manage coupon codes in the admin interface
def manage_coupons():
    st.markdown("<h3 style='color: #3D3D3D;'>💳 Manage Coupon Codes</h3>", unsafe_allow_html=True)

    # Create a new coupon
    coupon_code = st.text_input("Enter Coupon Code")
    discount_amount = st.number_input("Discount Amount (in RM)", min_value=0.0, format="%.2f")
    expiration_date = st.date_input("Expiration Date")

    if st.button("Create Coupon"):
        if coupon_code and discount_amount > 0:
            new_coupon = {
                'Code': coupon_code,
                'Discount': discount_amount,
                'Expiration Date': expiration_date
            }
            st.session_state.coupons.append(new_coupon)
            st.success(f"Coupon '{coupon_code}' created successfully!")
        else:
            st.error("Please enter a valid coupon code and discount amount.")

    # Display existing coupons
    if st.session_state.coupons:
        st.markdown("<h4>Existing Coupons</h4>", unsafe_allow_html=True)
        for coupon in st.session_state.coupons:
            st.markdown(f"- **{coupon['Code']}**: RM{coupon['Discount']} (Expires on {coupon['Expiration Date']})")
    else:
        st.write("No coupons available.")

    # Display coupon usage history in admin panel
    st.markdown("<h4>Coupon Usage History</h4>", unsafe_allow_html=True)

    # Display usage history table
    if 'coupon_usage_history' in st.session_state and st.session_state.coupon_usage_history:
        usage_df = pd.DataFrame(st.session_state.coupon_usage_history)
        st.dataframe(usage_df)
    else:
        st.write("No coupons have been used yet.")

# Taking Order
from datetime import datetime

def take_order():
    st.markdown("<h3 style='color: #3D3D3D;'>📋 Place Your Coffee Order</h3>", unsafe_allow_html=True)

    customer_name = st.text_input("Enter your name:")

    if customer_name:
        # Initialize a session state to store multiple orders
        if "temp_orders" not in st.session_state:
            st.session_state["temp_orders"] = []

        # Dynamic form for adding coffee items
        with st.form(key="add_coffee_form"):
            coffee_type = st.selectbox("Select Coffee", list(coffee_menu.keys()))
            branch = st.selectbox("Select Branch", FIXED_BRANCHES)

            if coffee_type:
                # Show sizes with the price difference in a radio button
                size_options = {
                    'small': f"Small (RM{coffee_menu[coffee_type]['small']:.2f})",
                    'medium': f"Medium (+RM{coffee_menu[coffee_type]['medium'] - coffee_menu[coffee_type]['small']:.2f})",
                    'large': f"Large (+RM{coffee_menu[coffee_type]['large'] - coffee_menu[coffee_type]['small']:.2f})"
                }
                size = st.radio(f"Select size for {coffee_type}", list(size_options.keys()), format_func=lambda x: size_options[x])

                quantity = st.number_input("Quantity", min_value=1, value=1, step=1)

                # Add-ons selection with displayed prices
                add_ons = st.multiselect(
                    f"Add-ons for {coffee_type} (Extra sugar RM{add_on_prices['Extra sugar']}, Extra milk RM{add_on_prices['Extra milk']})",
                    ['Extra sugar', 'Extra milk'], key=f"addons_{coffee_type}"
                )

                # Real-time calculation of price
                base_price = coffee_menu[coffee_type][size] * quantity
                add_on_price = sum(add_on_prices[add_on] for add_on in add_ons) * quantity
                total_price = base_price + add_on_price
                final_price = total_price

                # Apply daily special offer
                #daily_special = get_daily_special()
                #daily_offer = 0
                #if daily_special.get("coffee") is None or daily_special["coffee"] == coffee_type:
                #    daily_offer = daily_special["discount"] * base_price

                # Calculate final price with daily special
                #final_price = total_price

                # Calculate preparation time based on size and add-ons
                base_prep_time = {'small': 120, 'medium': 180, 'large': 300}[size]  # Time in seconds
                total_prep_time = base_prep_time + (len(add_ons) * 30)

                # Add Coffee Button
                if st.form_submit_button("Add Coffee"):
                    # Add the coffee order to the temp_orders list
                    st.session_state["temp_orders"].append({
                        "Coffee Type": coffee_type,
                        "Size": size,
                        "Quantity": quantity,
                        "Add-ons": ', '.join(add_ons) if add_ons else "None",
                        "Price": final_price,
                        "Branch": branch,
                        "Prep Time": total_prep_time  # Store preparation time
                    })
                    st.success(f"Added {quantity} x {size} {coffee_type}(s) to your order!")

        # Display all added coffees
        if st.session_state["temp_orders"]:
            st.markdown("<h4 style='color: #3D3D3D;'>🛒 Your Order</h4>", unsafe_allow_html=True)
            for i, order in enumerate(st.session_state["temp_orders"]):
                st.write(
                    f"{i + 1}. {order['Quantity']} x {order['Size'].capitalize()} {order['Coffee Type']} "
                    f"(Add-ons: {order['Add-ons']}) - RM{order['Price']:.2f} "
                    f"(Prep Time: {order['Prep Time']} seconds)"
                )

            # Calculate the total for all items
            total_order_price = sum(order["Price"] for order in st.session_state["temp_orders"])
            st.markdown(f"**Total Price Before Discounts:** RM{total_order_price:.2f}")

            # Apply daily special offer
            daily_special = get_daily_special()
            daily_offer = 0
            if daily_special.get("coffee") is None or daily_special["coffee"] == coffee_type:
                daily_offer = daily_special["discount"] * final_price

            # Coupon code input (Optional)
            coupon_code = st.text_input("Enter Coupon Code (optional):")

            discount = 0  # Default discount value
            if coupon_code:
                coupon_found = False
                for coupon in st.session_state.coupons:
                    if coupon['Code'] == coupon_code:
                        if datetime.strptime(coupon['Expiration Date'].strftime('%Y-%m-%d'), '%Y-%m-%d') >= datetime.now():
                            discount = coupon['Discount']
                            st.success(f"RM{discount:.2f} discount applied!")  # Show success message for coupon application
                            coupon_found = True
                            break
                if not coupon_found:
                    st.error("Invalid coupon or coupon has expired.")

            # Redeem Loyalty Points: Customer can enter how many points to redeem
            points_to_redeem = st.number_input(
                "Enter Loyalty Points to Redeem (1 point = RM0.50 discount)",
                min_value=0, max_value=st.session_state['loyalty_points'],
                step=1, key="redeem_points"
            )

            # Calculate the discount for loyalty points redemption
            loyalty_discount = points_to_redeem * 0.50

            # Final total price after all discounts
            total_price_after_discounts = max(0.00, total_order_price - daily_offer - discount - loyalty_discount)
            st.markdown(f"**Total Price After Discounts:** RM{total_price_after_discounts:.2f}")

            # Calculate waiting time based on orders ahead
            orders_ahead = len(st.session_state.sales_data[st.session_state.sales_data['Status'] == 'Being Processed'])
            total_waiting_time = 0

            for _, order in st.session_state.sales_data[st.session_state.sales_data['Status'] == 'Being Processed'].iterrows():
                order_size = order['Size']
                order_add_ons = order['Add-ons'].split(", ")

                prep_time = {'small': 120, 'medium': 180, 'large': 300}[order_size]
                total_waiting_time += prep_time + (len(order_add_ons) * 30)

            # Add the preparation time for the current order
            total_waiting_time += sum(order["Prep Time"] for order in st.session_state["temp_orders"])
            minutes, seconds = divmod(total_waiting_time, 60)

            st.markdown(f"**Estimated Waiting Time:** {minutes} minutes and {seconds} seconds")

            # Payment Method Section
            st.markdown("<h4 style='color: #3D3D3D;'>Secure Payment</h4>", unsafe_allow_html=True)
            payment_method = st.radio("Select Payment Method", ["Credit Card", "Debit Card", "Cash"])

            valid_payment = True
            if payment_method in ["Credit Card", "Debit Card"]:
                card_number = st.text_input("Card Number", max_chars=16, type="password")
                cardholder_name = st.text_input("Cardholder Name")
                expiry_date = st.text_input("Expiry Date (MM/YY)", max_chars=5)
                cvv = st.text_input("CVV", max_chars=3, type="password")

                if expiry_date:
                    try:
                        exp_month, exp_year = map(int, expiry_date.split("/"))
                        exp_year += 2000  # Convert YY to YYYY
                        now = datetime.now()
                        if exp_year < now.year or (exp_year == now.year and exp_month < now.month):
                            st.error("Card expiry date is invalid or expired!")
                            valid_payment = False
                    except ValueError:
                        st.error("Invalid expiry date format! Please enter in MM/YY format.")
                        valid_payment = False
                else:
                    st.error("Please enter the expiry date.")
                    valid_payment = False

            # Confirm Order Button
            if st.button("Confirm Order and Pay"):
                if valid_payment:
                    order_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    for order in st.session_state["temp_orders"]:
                        # Update inventory for the selected branch
                        coffee_type = order["Coffee Type"]
                        size = order["Size"]
                        quantity = order["Quantity"]
                        branch = order["Branch"]
                        add_ons = order["Add-ons"].split(', ')
                        ingredients = ingredient_usage[coffee_type][size]

                        if check_inventory(branch, coffee_type, size, quantity, add_ons):
                            # Store the new order details
                            new_order = {
                                'Order Number': generate_unique_order_number(),
                                'Customer Name': customer_name,
                                'Coffee Type': coffee_type,
                                'Quantity': quantity,
                                'Size': size,
                                'Add-ons': ', '.join(add_ons),
                                'Price': order["Price"],
                                'Time': order_time,
                                'Status': 'Being Processed',
                                'Branch': branch
                            }

                            st.session_state.sales_data = pd.concat(
                                [st.session_state.sales_data, pd.DataFrame([new_order])],
                                ignore_index=True
                            )

                            # Deduct inventory
                            st.session_state.branch_inventory[branch]['coffee_beans'] -= ingredients['coffee_beans'] * quantity
                            st.session_state.branch_inventory[branch]['milk'] -= ingredients['milk'] * quantity + (
                                extra_usage['milk'] if 'Extra milk' in add_ons else 0
                            )
                            st.session_state.branch_inventory[branch]['sugar'] -= ingredients['sugar'] * quantity + (
                                extra_usage['sugar'] if 'Extra sugar' in add_ons else 0
                            )
                            st.session_state.branch_inventory[branch]['cups'] -= quantity

                    st.success("Order placed successfully!")
                    st.session_state["temp_orders"] = []  # Clear temporary orders
                else:
                    st.error("Payment could not be processed due to invalid payment details. Please try again.")
    else:
        st.warning("Please enter your name to proceed.")


def loyalty_program():
    st.markdown("<h3 style='color: #3D3D3D;'>🎁 Loyalty Program</h3>", unsafe_allow_html=True)
    
    # Display current loyalty points
    st.write(f"**Your current loyalty points: {st.session_state['loyalty_points']}**")
    
    # Display loyalty points earning history
    if 'loyalty_points_history' in st.session_state and st.session_state['loyalty_points_history']:
        st.markdown("<h4 style='color: #3D3D3D;'>Loyalty Points Earned History</h4>", unsafe_allow_html=True)
        
        # Convert the earned points history into a DataFrame for display
        earned_df = pd.DataFrame(st.session_state['loyalty_points_history'])
        st.dataframe(earned_df)
    else:
        st.write("No loyalty points earned history available.")
    
    # Display loyalty points redemption history
    if 'loyalty_redemptions' in st.session_state and st.session_state['loyalty_redemptions']:
        st.markdown("<h4 style='color: #3D3D3D;'>Loyalty Points Redemption History</h4>", unsafe_allow_html=True)

        # Convert the redemption history into a DataFrame for display
        redemption_df = pd.DataFrame(st.session_state['loyalty_redemptions'])
        st.dataframe(redemption_df)
    else:
        st.write("No loyalty points redemption history available.")

# Function to generate and download an invoice as a text file
def generate_invoice(order_number, customer_name, coffee_type, size, add_ons, final_price, order_time):
    invoice_text = f"""
    ==========================
    ☕ Coffee Shop Invoice ☕
    ==========================
    Order Number: {order_number}
    Customer Name: {customer_name}
    Coffee Type: {coffee_type}
    Size: {size.capitalize()}
    Add-ons: {', '.join(add_ons) if add_ons else 'None'}
    Total Price: RM{final_price:.2f}
    Order Time: {order_time}
    ==========================
    Thank you for your purchase!
    """

    # Create a downloadable text file
    invoice_bytes = io.BytesIO(invoice_text.encode('utf-8'))

    # Add download button
    st.download_button(
        label="Download Invoice",
        data=invoice_bytes,
        file_name=f"invoice_{order_number}.txt",
        mime="text/plain"
    )





# Check Inventory Based on Coffee Type, Size, and Quantity
def check_inventory(branch, coffee_type, size, quantity, add_ons):
    ingredients = ingredient_usage[coffee_type][size]  # Retrieve ingredients here
    branch_inventory = st.session_state.branch_inventory[branch]

    if branch_inventory['coffee_beans'] < ingredients['coffee_beans'] * quantity:
        st.error(f"Sorry, {coffee_type} ({size}) is currently out of stock due to insufficient coffee beans.")
        return False
    if branch_inventory['milk'] < (ingredients['milk'] * quantity + (extra_usage['milk'] * quantity if 'Extra milk' in add_ons else 0)):
        st.error(f"Sorry, {coffee_type} ({size}) is currently out of stock due to insufficient milk.")
        return False
    if branch_inventory['sugar'] < (ingredients['sugar'] * quantity + (extra_usage['sugar'] * quantity if 'Extra sugar' in add_ons else 0)):
        st.error(f"Sorry, {coffee_type} ({size}) is currently out of stock due to insufficient sugar.")
        return False
    if branch_inventory['cups'] < quantity:
        st.error(f"Sorry, we are out of cups to serve {coffee_type} ({size}).")
        return False
    return True



# Update Inventory After Successful Order
def update_inventory(branch, coffee_type, size, quantity, add_ons):
    ingredients = ingredient_usage[coffee_type][size]
    branch_inventory = st.session_state.branch_inventory[branch]

    branch_inventory['coffee_beans'] -= ingredients['coffee_beans'] * quantity
    branch_inventory['milk'] -= ingredients['milk'] * quantity
    if 'Extra milk' in add_ons:
        branch_inventory['milk'] -= extra_usage['milk'] * quantity  # Deduct extra milk
    if 'Extra sugar' in add_ons:
        branch_inventory['sugar'] -= (ingredients['sugar'] * quantity + extra_usage['sugar'] * quantity)  # Deduct extra sugar
    else:
        branch_inventory['sugar'] -= ingredients['sugar'] * quantity  # Deduct regular sugar
    branch_inventory['cups'] -= quantity
    st.write("📊 Inventory updated.")


if 'feedback' not in st.session_state:
    st.session_state.feedback = []

# Function to display customer feedback in the admin section
def display_feedback():
    st.markdown("<h3 style='color: #3D3D3D;'>📋 Customer Feedback</h3>", unsafe_allow_html=True)

    if 'admin_branch' in st.session_state and st.session_state['admin_branch']:
        branch_feedback = [
            fb for fb in st.session_state.feedback if fb['Branch'] == st.session_state['admin_branch']
        ]

        if branch_feedback:
            for fb in branch_feedback:
                st.markdown(
                    f"""
                    <div style='border: 1px solid #d9d9d9; border-radius: 10px; padding: 15px; margin-bottom: 15px; background-color: #f9f9f9;'>
                        <h4 style='color: #333;'>Customer Name: {fb['Name']}</h4>
                        <p><strong>Coffee Purchased:</strong> {fb['Coffee Purchased']}</p>
                        <p><strong>Coffee Rating:</strong> {'⭐' * fb['Coffee Rating']} ({fb['Coffee Rating']}/5)</p>
                        <p><strong>Service Rating:</strong> {'⭐' * fb['Service Rating']} ({fb['Service Rating']}/5)</p>
                        <p><strong>Comments:</strong> <span style='color: #666;'>{fb['Additional Feedback']}</span></p>
                        <p style='color: #999; font-size: 0.85em;'>Submitted on {fb['Time']}</p>
                    </div>
                    """, unsafe_allow_html=True
                )
        else:
            st.write(f"No feedback available for {st.session_state['admin_branch']} branch.")
    else:
        st.error("Please select a branch to view feedback.")

# Maintain the current branch inventory
if 'current_inventory' not in st.session_state:
    st.session_state['current_inventory'] = None

# Ensure branch selection updates the current inventory dynamically
def update_current_inventory(branch):
    st.session_state['current_inventory'] = st.session_state.branch_inventory[branch]

# Branch Inventory Display
def display_branch_inventory():
    st.markdown("<h3 style='color: #3D3D3D;'>📦 Branch Inventory</h3>", unsafe_allow_html=True)
    
    if 'admin_branch' in st.session_state and st.session_state['admin_branch']:
        branch = st.session_state['admin_branch']
        update_current_inventory(branch)  # Sync with the current branch

        inventory = st.session_state['current_inventory']
        st.markdown(f"### Inventory for {branch} Branch")
        
        # Display current inventory levels
        for item, qty in inventory.items():
            st.write(f"{item.capitalize()}: {qty}")

        # Restocking options
        item_to_restock = st.selectbox(f"Select item to restock for {branch}", inventory.keys(), key="restock_item")
        restock_amount = st.number_input(f"Enter restock amount for {item_to_restock}", min_value=0, step=10, key="restock_amount")

        # Calculate and display the live restock price
        if restock_amount > 0:
            restock_cost = calculate_restock_cost(item_to_restock, restock_amount)
            st.markdown(f"💵 **Live Restock Price:** RM{restock_cost:.2f}")
        else:
            st.markdown("💵 **Live Restock Price:** RM0.00")

        # Restock button
        if st.button(f"Restock {item_to_restock}"):
            if restock_amount > 0:
                inventory[item_to_restock] += restock_amount
                st.session_state.restock_history.append({
                    'Branch': branch,
                    'Item': item_to_restock,
                    'Amount': restock_amount,
                    'Cost': restock_cost,
                    'Time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                st.success(f"Restocked {item_to_restock} for {branch} with {restock_amount} units.")
            else:
                st.error("Please enter a valid restock amount.")
    else:
        st.error("Please select a branch to view the inventory.")

# Calculate the cost of restocking
def calculate_restock_cost(item, amount):
    cost_per_unit = restock_prices[item]
    if item in ['coffee_beans', 'milk', 'sugar']:
        return (amount / 100) * cost_per_unit
    return amount * cost_per_unit

# Update inventory usage dynamically
def update_inventory_usage(coffee_type, size, quantity, add_ons):
    branch = st.session_state['admin_branch']
    inventory = st.session_state.branch_inventory[branch]
    usage = ingredient_usage[coffee_type][size]

    inventory['coffee_beans'] -= usage['coffee_beans'] * quantity
    inventory['milk'] -= usage['milk'] * quantity + (extra_usage['milk'] * quantity if 'Extra milk' in add_ons else 0)
    inventory['sugar'] -= usage['sugar'] * quantity + (extra_usage['sugar'] * quantity if 'Extra sugar' in add_ons else 0)
    inventory['cups'] -= quantity



def admin_interface():
    st.sidebar.title("Administration")

    # Branch Selection
    branch_options = FIXED_BRANCHES  # List of fixed branches

    # Safeguard for valid branch selection
    current_branch = st.session_state.get('admin_branch', branch_options[0])  # Default to the first branch if None
    if current_branch not in branch_options:
        current_branch = branch_options[0]  # Ensure valid branch fallback

    # Display the branch selection dropdown
    selected_branch = st.sidebar.selectbox("Select Branch", branch_options, index=branch_options.index(current_branch))
    st.session_state['admin_branch'] = selected_branch  # Update session state with the selected branch

    st.sidebar.markdown(f"**Selected Branch:** {st.session_state['admin_branch']}")

    # Admin Page Selection
    selection = st.sidebar.radio("Choose a page:", [
        "Branch Inventory", 
        "Sales Report", 
        "Analytics Dashboard", 
        "Feedback", 
        "Kitchen Orders", 
        "Manage Coupons", 
        "Order History"
    ])

    # Page Navigation
    if selection == "Branch Inventory":
        display_branch_inventory()
    elif selection == "Sales Report":
        sales_report()
    elif selection == "Analytics Dashboard":
        analytics_dashboard()
    elif selection == "Feedback":
        display_feedback()
    elif selection == "Kitchen Orders":
        display_kitchen_orders()
    elif selection == "Manage Coupons":
        manage_coupons()
    elif selection == "Order History":
        display_order_history()



# Main content function
def main_content():
    if 'user' in st.session_state:
        if st.session_state.get('is_admin'):
            st.subheader("Admin Dashboard")
            admin_interface()  # Show admin features
        else:
            st.subheader("Customer Dashboard")
            customer_interface()  # Show customer features
    else:
        st.write("Please log in or sign up to access the app.")

# Call the authentication and main content functions
if __name__ == "__main__":
    authenticate_user()
    main_content()


