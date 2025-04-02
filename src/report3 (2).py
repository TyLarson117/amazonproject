# Consolidated Company Task Management App (Capitalized Table Names)

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import mysql.connector
from mysql.connector import Error
from datetime import date, datetime
from decimal import Decimal
from collections import defaultdict
import io
import sys

# --- 1. Database Configuration ---
# !!! IMPORTANT: Replace with your actual MySQL credentials !!!
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',      # Replace with your MySQL username
    'password': 'admin', # Replace with your MySQL password
    'database': 'AmazonProject'     # Should match your database name
}

# --- 2. Database Utility ---
def get_db_connection():
    """Establishes a connection to the MySQL database."""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

# --- 3. Backend Task Functions (Using Capitalized Table Names) ---

# == Task 1: Add Customer ==
def add_customer(name: str, dob: str, email: str, address: str, phone: str):
    """Adds a new customer to the database."""
    conn = get_db_connection()
    if not conn:
        print("Database connection failed for add_customer.")
        return None

    cursor = conn.cursor()
    new_customer_id = None
    try:
        # Find the next available CustomerID
        cursor.execute("SELECT MAX(CustomerID) FROM Customer") # Capitalized
        max_id_result = cursor.fetchone()
        next_id = (max_id_result[0] or 0) + 1

        # Prepare the INSERT statement
        query = """
        INSERT INTO Customer (CustomerID, Name, DoB, Email, Address, PhoneNumber)
        VALUES (%s, %s, %s, %s, %s, %s)
        """ # Capitalized
        # Validate and format date
        try:
            dob_date = date.fromisoformat(dob) # Expects YYYY-MM-DD
        except ValueError:
            print(f"Invalid date format for DoB: {dob}. Please use YYYY-MM-DD.")
            return None

        customer_data = (next_id, name, dob_date, email, address, phone)
        cursor.execute(query, customer_data)
        conn.commit()
        new_customer_id = next_id
        print(f"Successfully added customer '{name}' with ID {new_customer_id}.")

    except Error as e:
        print(f"Error adding customer: {e}")
        conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
    return new_customer_id

# == Task 2: Check Inventory ==
def check_inventory(product_id: int = None, sku: str = None):
    """Checks inventory for products. Shows all if no ID/SKU provided."""
    conn = get_db_connection()
    if not conn:
        print("Database connection failed for check_inventory.")
        return [], "Database connection failed."

    cursor = conn.cursor(dictionary=True)
    results = []
    output_message = ""
    try:
        query = "SELECT ProductID, Name, Brand, Stock, Price FROM Product" # Capitalized
        params = []

        if product_id:
            query += " WHERE ProductID = %s"
            params.append(product_id)
        elif sku:
            query += " WHERE SKU = %s"
            params.append(sku)

        query += " ORDER BY ProductID"

        cursor.execute(query, params)
        results = cursor.fetchall()

        if not results:
            output_message = "No products found matching the criteria."
            print(output_message)
        else:
            header = "\n--- Inventory Report ---\n"
            header += f"{'ID':<5} {'Name':<30} {'Brand':<15} {'Stock':<7} {'Price':<10}\n"
            header += "-" * 70 + "\n"
            output_message += header
            print(header.strip())

            for product in results:
                line = f"{product['ProductID']:<5} {product['Name']:<30} {product['Brand']:<15} {product['Stock']:<7} {product['Price']:<10.2f}\n"
                output_message += line
                print(line.strip())

            footer = "-" * 70 + "\n"
            output_message += footer
            print(footer.strip())

    except Error as e:
        error_msg = f"Error checking inventory: {e}"
        print(error_msg)
        output_message = error_msg
        results = []
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
    return results, output_message

# == Task 3: Place Order ==
def place_order(customer_id: int, product_ids: list[int]):
    """Places a new order for a customer, updating stock levels."""
    conn = get_db_connection()
    if not conn:
        print("Database connection failed for place_order.")
        return None, "Database connection failed."

    cursor = conn.cursor()
    new_order_id = None
    message = ""

    try:
        conn.start_transaction()

        # 1. Verify Customer Exists
        cursor.execute("SELECT CustomerID FROM Customer WHERE CustomerID = %s", (customer_id,)) # Capitalized
        if not cursor.fetchone():
            raise ValueError(f"Customer with ID {customer_id} not found.")

        # 2. Verify Products and Stock
        product_prices = {}
        for pid in product_ids:
            cursor.execute("SELECT Name, Price, Stock FROM Product WHERE ProductID = %s", (pid,)) # Capitalized
            product_info = cursor.fetchone()
            if not product_info:
                raise ValueError(f"Product with ID {pid} not found.")
            p_name, price, stock = product_info
            if stock <= 0:
                raise ValueError(f"Product '{p_name}' (ID: {pid}) is out of stock.")
            product_prices[pid] = price

        # 3. Create Order Header
        cursor.execute("SELECT MAX(OrderID) FROM `Order`") # Capitalized + Backticks
        max_order_id_result = cursor.fetchone()
        next_order_id = (max_order_id_result[0] or 200) + 1

        order_date = date.today()
        order_query = "INSERT INTO `Order` (OrderID, CustomerID, OrderDate) VALUES (%s, %s, %s)" # Capitalized + Backticks
        cursor.execute(order_query, (next_order_id, customer_id, order_date))
        new_order_id = next_order_id

        # 4. Create Order Details and Update Stock
        order_details_query = "INSERT INTO OrderDetails (OrderID, ProductID, TotalPrice) VALUES (%s, %s, %s)" # Capitalized
        update_stock_query = "UPDATE Product SET Stock = Stock - 1 WHERE ProductID = %s" # Capitalized

        for pid in product_ids:
            total_price_for_item = product_prices[pid]
            cursor.execute(order_details_query, (new_order_id, pid, total_price_for_item))
            cursor.execute(update_stock_query, (pid,))

        conn.commit()
        message = f"Order {new_order_id} placed successfully for customer {customer_id}."
        print(message)

    except (Error, ValueError) as e:
        error_msg = f"Error placing order: {e}"
        print(error_msg)
        message = error_msg
        if conn: conn.rollback()
        new_order_id = None
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
    return new_order_id, message

# == Extra Task 1: Daily Sales ==
def get_daily_sales(target_date: str):
    """Calculates total sales for a given date."""
    conn = get_db_connection()
    if not conn:
        print("Database connection failed for get_daily_sales.")
        return None, "Database connection failed."

    cursor = conn.cursor()
    total_sales = Decimal('0.00')
    message = ""
    try:
        try:
            valid_date = date.fromisoformat(target_date)
        except ValueError:
            message = f"Invalid date format: {target_date}. Please use YYYY-MM-DD."
            print(message)
            return None, message

        query = """
        SELECT SUM(od.TotalPrice)
        FROM OrderDetails od
        JOIN `Order` o ON od.OrderID = o.OrderID
        WHERE o.OrderDate = %s
        """ # Capitalized OrderDetails and Order (with backticks)
        cursor.execute(query, (valid_date,))
        result = cursor.fetchone()

        if result and result[0] is not None:
            total_sales = result[0]
            message = f"Total sales for {target_date}: ${total_sales:.2f}"
            print(message)
        else:
            message = f"No sales recorded for {target_date}."
            print(message)
            total_sales = Decimal('0.00')

    except Error as e:
        error_msg = f"Error retrieving daily sales: {e}"
        print(error_msg)
        message = error_msg
        total_sales = None
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
    return total_sales, message

# == Extra Task 2: Customer Order History ==
def get_customer_order_history(customer_id: int):
    """Retrieves and displays the order history for a specific customer."""
    conn = get_db_connection()
    if not conn:
        print("Database connection failed for get_customer_order_history.")
        return None, "Database connection failed."

    cursor = conn.cursor(dictionary=True)
    order_history = None
    output_message = ""
    try:
        # Check if customer exists
        cursor.execute("SELECT Name FROM Customer WHERE CustomerID = %s", (customer_id,)) # Capitalized
        customer_result = cursor.fetchone()
        if not customer_result:
            output_message = f"Customer with ID {customer_id} not found."
            print(output_message)
            return None, output_message
        customer_name = customer_result['Name']
        header = f"\n--- Order History for Customer {customer_id} ({customer_name}) ---\n"
        output_message += header
        print(header.strip())

        # Query order details
        query = """
        SELECT o.OrderID, o.OrderDate, p.Name AS ProductName, p.Brand, od.TotalPrice
        FROM `Order` o
        JOIN OrderDetails od ON o.OrderID = od.OrderID
        JOIN Product p ON od.ProductID = p.ProductID
        WHERE o.CustomerID = %s
        ORDER BY o.OrderDate DESC, o.OrderID ASC, p.Name ASC
        """ # Capitalized Order, OrderDetails, Product
        cursor.execute(query, (customer_id,))
        results = cursor.fetchall()

        if not results:
            no_orders_msg = "No orders found for this customer."
            output_message += no_orders_msg + "\n"
            print(no_orders_msg)
            return {}, output_message

        # Group results by OrderID
        grouped_orders = defaultdict(list)
        order_dates = {}
        for row in results:
            order_id = row['OrderID']
            order_dates[order_id] = row['OrderDate'].strftime('%Y-%m-%d')
            grouped_orders[order_id].append({
                'Product': row['ProductName'],
                'Brand': row['Brand'],
                'Price': row['TotalPrice']
            })

        # Print grouped results
        for order_id, items in grouped_orders.items():
            order_header = f"\nOrder ID: {order_id} (Date: {order_dates[order_id]})\n"
            order_header += f"  {'Product Name':<30} {'Brand':<15} {'Price':<10}\n"
            order_header += "  " + "-" * 60 + "\n"
            output_message += order_header
            print(order_header.strip())

            for item in items:
                item_line = f"  {item['Product']:<30} {item['Brand']:<15} ${item['Price']:<10.2f}\n"
                output_message += item_line
                print(item_line.strip())

        footer = "\n" + "="*70 + "\n"
        output_message += footer
        print(footer.strip())
        order_history = grouped_orders

    except Error as e:
        error_msg = f"Error retrieving order history: {e}"
        print(error_msg)
        output_message = error_msg
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
    return order_history, output_message


# --- 4. GUI Implementation (Tkinter) ---
# (GUI Code remains unchanged as it calls the backend functions)
class CompanyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Company Task Manager")
        self.geometry("850x650")

        style = ttk.Style(self)
        style.theme_use('clam')

        self.output_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, height=20, font=("Consolas", 9))
        self.output_area.pack(pady=10, padx=10, fill="both", expand=True)
        self.output_area.configure(state='disabled')

        control_frame = ttk.Frame(self)
        control_frame.pack(pady=5, padx=10, fill="x", expand=False)

        self.notebook = ttk.Notebook(control_frame)
        self.notebook.pack(fill="x", expand=True)

        self.create_customer_tab()
        self.create_inventory_tab()
        self.create_order_tab()
        self.create_sales_tab()
        self.create_history_tab()

        clear_button = ttk.Button(self, text="Clear Output Log", command=self.clear_output)
        clear_button.pack(pady=(0, 10))


    def log_output(self, message):
        if not isinstance(message, str):
             message = str(message)
        self.output_area.configure(state='normal')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.output_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.output_area.see(tk.END)
        self.output_area.configure(state='disabled')

    def clear_output(self):
        self.output_area.configure(state='normal')
        self.output_area.delete('1.0', tk.END)
        self.output_area.configure(state='disabled')

    # --- Tab Creation Methods ---
    def create_customer_tab(self):
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text=" Add Customer ")
        ttk.Label(tab, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.cust_name_entry = ttk.Entry(tab, width=40)
        self.cust_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(tab, text="DoB (YYYY-MM-DD):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.cust_dob_entry = ttk.Entry(tab, width=40)
        self.cust_dob_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(tab, text="Email:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.cust_email_entry = ttk.Entry(tab, width=40)
        self.cust_email_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(tab, text="Address:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.cust_address_entry = ttk.Entry(tab, width=40)
        self.cust_address_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(tab, text="Phone:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.cust_phone_entry = ttk.Entry(tab, width=40)
        self.cust_phone_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        add_button = ttk.Button(tab, text="Add Customer", command=self.handle_add_customer)
        add_button.grid(row=5, column=0, columnspan=2, pady=15)
        tab.columnconfigure(1, weight=1)

    def create_inventory_tab(self):
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text=" Check Inventory ")
        ttk.Label(tab, text="Product ID (Optional):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.inv_pid_entry = ttk.Entry(tab, width=30)
        self.inv_pid_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(tab, text="SKU (Optional):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.inv_sku_entry = ttk.Entry(tab, width=30)
        self.inv_sku_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        check_button = ttk.Button(tab, text="Check Stock", command=self.handle_check_inventory)
        check_button.grid(row=2, column=0, columnspan=2, pady=15)
        tab.columnconfigure(1, weight=1)

    def create_order_tab(self):
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text=" Place Order ")
        ttk.Label(tab, text="Customer ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.order_cust_id_entry = ttk.Entry(tab, width=30)
        self.order_cust_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(tab, text="Product IDs (comma-separated):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.order_prod_ids_entry = ttk.Entry(tab, width=40)
        self.order_prod_ids_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        place_button = ttk.Button(tab, text="Place Order", command=self.handle_place_order)
        place_button.grid(row=2, column=0, columnspan=2, pady=15)
        tab.columnconfigure(1, weight=1)

    def create_sales_tab(self):
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text=" Daily Sales ")
        ttk.Label(tab, text="Date (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.sales_date_entry = ttk.Entry(tab, width=30)
        self.sales_date_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.sales_date_entry.insert(0, date.today().isoformat())
        report_button = ttk.Button(tab, text="Get Sales Report", command=self.handle_get_sales)
        report_button.grid(row=1, column=0, columnspan=2, pady=15)
        tab.columnconfigure(1, weight=1)

    def create_history_tab(self):
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text=" Order History ")
        ttk.Label(tab, text="Customer ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.history_cust_id_entry = ttk.Entry(tab, width=30)
        self.history_cust_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        view_button = ttk.Button(tab, text="View History", command=self.handle_view_history)
        view_button.grid(row=1, column=0, columnspan=2, pady=15)
        tab.columnconfigure(1, weight=1)

    # --- Event Handler Methods ---
    # (These methods call the backend functions, so they don't need changes themselves)
    def handle_add_customer(self):
        name = self.cust_name_entry.get()
        dob = self.cust_dob_entry.get()
        email = self.cust_email_entry.get()
        address = self.cust_address_entry.get()
        phone = self.cust_phone_entry.get()
        if not all([name, dob, email, address, phone]):
            messagebox.showerror("Input Error", "All customer fields are required.")
            self.log_output("ERROR: Add Customer failed - All fields required.")
            return
        self.log_output(f"Attempting to add customer: {name}...")
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()
        new_id = add_customer(name, dob, email, address, phone) # Calls backend
        sys.stdout = old_stdout
        output_from_func = captured_output.getvalue()
        if output_from_func: self.log_output(f"Backend output:\n---\n{output_from_func.strip()}\n---")
        if new_id:
            messagebox.showinfo("Success", f"Customer '{name}' added with ID: {new_id}")
            self.cust_name_entry.delete(0, tk.END); self.cust_dob_entry.delete(0, tk.END); self.cust_email_entry.delete(0, tk.END); self.cust_address_entry.delete(0, tk.END); self.cust_phone_entry.delete(0, tk.END)
        else: messagebox.showerror("Error", "Failed to add customer. Check logs for details.")

    def handle_check_inventory(self):
        pid_str = self.inv_pid_entry.get()
        sku = self.inv_sku_entry.get()
        pid = None
        if pid_str and sku:
             messagebox.showerror("Input Error", "Provide EITHER Product ID OR SKU, not both.")
             self.log_output("ERROR: Check Inventory failed - Provide ID or SKU, not both.")
             return
        if pid_str:
            try: pid = int(pid_str)
            except ValueError:
                messagebox.showerror("Input Error", "Product ID must be a whole number.")
                self.log_output(f"ERROR: Check Inventory failed - Invalid Product ID '{pid_str}'.")
                return
        search_criteria = f"Product ID={pid}" if pid else f"SKU='{sku}'" if sku else "All Products"
        self.log_output(f"Checking inventory for: {search_criteria}...")
        results, output_message = check_inventory(product_id=pid, sku=sku) # Calls backend
        self.log_output(f"Inventory Check Result:\n{output_message.strip()}")

    def handle_place_order(self):
        cust_id_str = self.order_cust_id_entry.get()
        prod_ids_str = self.order_prod_ids_entry.get()
        if not cust_id_str or not prod_ids_str:
            messagebox.showerror("Input Error", "Customer ID and Product IDs are required.")
            self.log_output("ERROR: Place Order failed - Missing Customer ID or Product IDs.")
            return
        try: cust_id = int(cust_id_str)
        except ValueError:
             messagebox.showerror("Input Error", "Customer ID must be a whole number.")
             self.log_output(f"ERROR: Place Order failed - Invalid Customer ID '{cust_id_str}'.")
             return
        try:
            prod_ids = [int(p.strip()) for p in prod_ids_str.split(',') if p.strip()]
            if not prod_ids: raise ValueError("No valid product IDs entered.")
        except ValueError as e:
             messagebox.showerror("Input Error", f"Invalid Product IDs. Enter numbers separated by commas.\nDetails: {e}")
             self.log_output(f"ERROR: Place Order failed - Invalid Product IDs '{prod_ids_str}'. Details: {e}")
             return
        self.log_output(f"Attempting to place order for Customer ID {cust_id}, Products: {prod_ids}...")
        order_id, message = place_order(cust_id, prod_ids) # Calls backend
        self.log_output(f"Place Order Result: {message}")
        if order_id:
            messagebox.showinfo("Success", f"Order placed successfully with ID: {order_id}")
            self.order_prod_ids_entry.delete(0, tk.END)
        else: messagebox.showerror("Error", f"Failed to place order.\nDetails: {message}")

    def handle_get_sales(self):
        target_date_str = self.sales_date_entry.get()
        if not target_date_str:
             messagebox.showerror("Input Error", "Date is required (YYYY-MM-DD).")
             self.log_output("ERROR: Get Sales failed - Date is required.")
             return
        self.log_output(f"Getting daily sales report for: {target_date_str}...")
        total, message = get_daily_sales(target_date_str) # Calls backend
        self.log_output(f"Sales Report Result: {message}")
        if total is not None and total >= 0: messagebox.showinfo("Sales Report", message)
        elif "Invalid date format" in message: messagebox.showerror("Input Error", message)

    def handle_view_history(self):
        cust_id_str = self.history_cust_id_entry.get()
        if not cust_id_str:
             messagebox.showerror("Input Error", "Customer ID is required.")
             self.log_output("ERROR: View History failed - Customer ID is required.")
             return
        try: cust_id = int(cust_id_str)
        except ValueError:
             messagebox.showerror("Input Error", "Customer ID must be a whole number.")
             self.log_output(f"ERROR: View History failed - Invalid Customer ID '{cust_id_str}'.")
             return
        self.log_output(f"Retrieving order history for Customer ID: {cust_id}...")
        history_data, output_message = get_customer_order_history(cust_id) # Calls backend
        self.log_output(f"Order History Result:\n{output_message.strip()}")
        if "not found" in output_message: messagebox.showwarning("Not Found", output_message)
        elif "No orders found" in output_message: messagebox.showinfo("No Orders", output_message)


# --- 5. Main Execution Block ---
if __name__ == "__main__":
    print("Starting Company Task Manager...")
    try: import mysql.connector
    except ImportError:
        print("CRITICAL ERROR: mysql.connector module not found.")
        print("Please install it: pip install mysql-connector-python")
        root = tk.Tk(); root.withdraw(); messagebox.showerror("Missing Library", "MySQL Connector not found.\nPlease install it:\npip install mysql-connector-python"); root.destroy(); sys.exit(1)

    print("Testing database connection...")
    conn_test = None
    try:
        conn_test = get_db_connection()
        if conn_test and conn_test.is_connected():
            print("Database connection successful.")
            conn_test.close()
            print("Launching GUI...")
            app = CompanyApp()
            app.mainloop()
            print("Application closed.")
        else:
             print("CRITICAL: Failed to connect to the database. Check DB_CONFIG and MySQL server status.")
             root = tk.Tk(); root.withdraw(); messagebox.showerror("Database Error", "Failed to connect to the database.\nPlease check DB_CONFIG credentials, database name, and ensure MySQL server is running."); root.destroy(); sys.exit(1)
    except mysql.connector.Error as db_err:
         print(f"CRITICAL: Database connection error during startup test: {db_err}")
         root = tk.Tk(); root.withdraw(); messagebox.showerror("Database Connection Error", f"Failed to connect during startup test:\n{db_err}\n\nPlease check configuration and server status."); root.destroy(); sys.exit(1)
    except Exception as e:
         print(f"An unexpected error occurred during startup: {e}")
         try: root = tk.Tk(); root.withdraw(); messagebox.showerror("Application Error", f"An unexpected error occurred during startup:\n{e}"); root.destroy()
         except: pass
         sys.exit(1)
    finally:
        if conn_test and conn_test.is_connected(): conn_test.close()