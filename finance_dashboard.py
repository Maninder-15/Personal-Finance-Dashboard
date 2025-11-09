import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.widgets import DateEntry
import mysql.connector
from datetime import date
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- Database Connection ---
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'Nishu@15',
    'database': 'finance_db'
}

class FinanceDashboard(tb.Window):
    def __init__(self):
        super().__init__(themename="superhero", title="Personal Finance Dashboard", size=(1300, 800))
        
        # Try to connect to the database
        try:
            self.db_conn = mysql.connector.connect(**DB_CONFIG)
            self.cursor = self.db_conn.cursor()
            # Ensure table exists (optional, but good practice)
            self.setup_database()
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to connect to MySQL: {err}\nPlease check your credentials in DB_CONFIG.")
            self.destroy()
            return

        # Main layout frames
        self.grid_rowconfigure(0, weight=1) # Main content row
        self.grid_rowconfigure(1, weight=3) # Treeview row
        self.grid_columnconfigure(0, weight=1) # Form/Summary column
        self.grid_columnconfigure(1, weight=2) # Chart column

        # --- Top-Left: Summary Frame ---
        summary_frame = tb.Labelframe(self, text="📊 Financial Summary", bootstyle="info", padding=20)
        summary_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        self.total_income_label = tb.Label(summary_frame, text="Total Income: $0.00", font=("Helvetica", 14, "bold"), bootstyle="success")
        self.total_income_label.pack(pady=10)
        
        self.total_expense_label = tb.Label(summary_frame, text="Total Expense: $0.00", font=("Helvetica", 14, "bold"), bootstyle="danger")
        self.total_expense_label.pack(pady=10)
        
        self.balance_label = tb.Label(summary_frame, text="Balance: $0.00", font=("Helvetica", 16, "bold"), bootstyle="primary")
        self.balance_label.pack(pady=20)

        # --- Top-Left: Form Frame (placed below summary) ---
        form_frame = tb.Labelframe(self, text="💸 Add New Transaction", bootstyle="info", padding=20)
        form_frame.grid(row=0, column=0, padx=20, pady=(250, 20), sticky="nsew") # Offset by summary
        
        # Description
        tb.Label(form_frame, text="Description:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.desc_entry = tb.Entry(form_frame, bootstyle="primary")
        self.desc_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Amount
        tb.Label(form_frame, text="Amount:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.amount_entry = tb.Entry(form_frame, bootstyle="primary")
        self.amount_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Type
        tb.Label(form_frame, text="Type:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.type_var = tk.StringVar()
        self.type_combo = tb.Combobox(form_frame, textvariable=self.type_var, values=["Income", "Expense"], state="readonly", bootstyle="primary")
        self.type_combo.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.type_combo.current(1) # Default to 'Expense'

        # Date
        tb.Label(form_frame, text="Date:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.date_entry = DateEntry(form_frame, bootstyle="primary", firstweekday=0, dateformat="%Y-%m-%d")
        self.date_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        # Add Button
        self.add_button = tb.Button(form_frame, text="Add Transaction", command=self.add_transaction, bootstyle="success-outline")
        self.add_button.grid(row=4, column=0, columnspan=2, pady=15, sticky="ew")
        
        form_frame.grid_columnconfigure(1, weight=1)

        # --- Top-Right: Chart Frame ---
        chart_frame = tb.Frame(self, padding=20)
        chart_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.fig = Figure(figsize=(6, 5), dpi=100, facecolor=self.style.colors.bg)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(self.style.colors.bg)
        self.fig.autofmt_xdate()

        self.chart_canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.chart_canvas.get_tk_widget().pack(fill=BOTH, expand=True)

        # --- Bottom: Transaction List (Treeview) ---
        tree_frame = tb.Labelframe(self, text="📋 Transaction History", bootstyle="info", padding=20)
        tree_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=20, sticky="nsew")

        columns = ("id", "date", "description", "amount", "type")
        self.tree = tb.Treeview(tree_frame, columns=columns, show="headings", bootstyle="primary")
        
        self.tree.heading("id", text="ID", anchor="center")
        self.tree.heading("date", text="Date", anchor="center")
        self.tree.heading("description", text="Description", anchor="w")
        self.tree.heading("amount", text="Amount", anchor="e")
        self.tree.heading("type", text="Type", anchor="center")

        self.tree.column("id", width=50, stretch=False, anchor="center")
        self.tree.column("date", width=100, stretch=False, anchor="center")
        self.tree.column("description", width=400, stretch=True, anchor="w")
        self.tree.column("amount", width=100, stretch=False, anchor="e")
        self.tree.column("type", width=100, stretch=False, anchor="center")
        
        # Add a scrollbar
        scrollbar = tb.Scrollbar(tree_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree.pack(fill=BOTH, expand=True)

        # Bind delete event to tree
        self.tree.bind("<Delete>", self.delete_transaction)

        # --- Initial Data Load ---
        self.refresh_all_data()

    def setup_database(self):
        """Ensures the transactions table exists."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                trans_date DATE NOT NULL,
                description VARCHAR(255) NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                type ENUM('Income', 'Expense') NOT NULL
            );
        """)
        self.db_conn.commit()

    def add_transaction(self):
        """Adds a new transaction to the database."""
        description = self.desc_entry.get()
        amount_str = self.amount_entry.get()
        trans_type = self.type_var.get()
        trans_date = self.date_entry.entry.get()

        # Validation
        if not description or not amount_str or not trans_type or not trans_date:
            messagebox.showwarning("Input Error", "All fields are required.")
            return
        
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Input Error", "Amount must be a positive number.")
            return

        # Insert into database
        try:
            sql = "INSERT INTO transactions (trans_date, description, amount, type) VALUES (%s, %s, %s, %s)"
            values = (trans_date, description, amount, trans_type)
            self.cursor.execute(sql, values)
            self.db_conn.commit()
            
            messagebox.showinfo("Success", "Transaction added successfully.")
            self.clear_form()
            self.refresh_all_data()

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to add transaction: {err}")

    def delete_transaction(self, event):
        """Deletes the selected transaction from the treeview and database."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select a transaction to delete.")
            return

        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the selected transaction(s)?"):
            return

        try:
            for item in selected_items:
                item_data = self.tree.item(item)
                trans_id = item_data['values'][0] # Get the 'id' from the first column
                
                sql = "DELETE FROM transactions WHERE id = %s"
                self.cursor.execute(sql, (trans_id,))
            
            self.db_conn.commit()
            self.refresh_all_data()
            messagebox.showinfo("Success", "Transaction(s) deleted.")

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to delete transaction: {err}")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")


    def clear_form(self):
        """Clears the input fields in the form."""
        self.desc_entry.delete(0, END)
        self.amount_entry.delete(0, END)
        self.type_combo.current(1) # Reset to 'Expense'
        self.date_entry.entry.delete(0, END)
        self.date_entry.entry.insert(0, date.today().strftime("%Y-%m-%d"))

    def fetch_all_transactions(self):
        """Fetches all transactions from the database."""
        try:
            self.cursor.execute("SELECT id, trans_date, description, amount, type FROM transactions ORDER BY trans_date DESC")
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to fetch transactions: {err}")
            return []

    def refresh_all_data(self):
        """Updates all parts of the dashboard: tree, summary, and chart."""
        transactions = self.fetch_all_transactions()
        
        # Update Treeview
        self.tree.delete(*self.tree.get_children()) # Clear existing items
        for trans in transactions:
            # Format date and amount for display
            trans_date_str = trans[1].strftime("%Y-%m-%d")
            amount_str = f"${trans[3]:,.2f}"
            
            # Apply color tags based on type
            if trans[4] == 'Income':
                tags = ('income_tag',)
            else:
                tags = ('expense_tag',)
                
            self.tree.insert("", END, values=(trans[0], trans_date_str, trans[2], amount_str, trans[4]), tags=tags)
        
        # Configure tags for row colors
        self.tree.tag_configure('income_tag', background=self.style.colors.success)
        self.tree.tag_configure('expense_tag', background=self.style.colors.danger)

        # Update Summary and Chart
        self.update_summary_and_chart(transactions)
        self.clear_form()

    def update_summary_and_chart(self, transactions):
        """Calculates and displays summary totals and the pie chart."""
        total_income = 0.0
        total_expense = 0.0
        
        for trans in transactions:
            amount = float(trans[3])
            trans_type = trans[4]
            if trans_type == 'Income':
                total_income += amount
            else:
                total_expense += amount
                
        balance = total_income - total_expense

        # Update Summary Labels
        self.total_income_label.config(text=f"Total Income: ${total_income:,.2f}")
        self.total_expense_label.config(text=f"Total Expense: ${total_expense:,.2f}")
        
        balance_style = "success" if balance >= 0 else "danger"
        self.balance_label.config(text=f"Balance: ${balance:,.2f}", bootstyle=balance_style)

        # Update Pie Chart
        self.ax.clear()
        self.ax.set_facecolor(self.style.colors.light) # Set chart background
        
        if total_income == 0 and total_expense == 0:
            self.ax.text(0.5, 0.5, "No Data", horizontalalignment='center', verticalalignment='center', transform=self.ax.transAxes, fontsize=14, color=self.style.colors.primary)
            self.ax.set_title("Income vs. Expense", color=self.style.colors.primary, fontsize=16)
        else:
            labels = ['Income', 'Expense']
            sizes = [total_income, total_expense]
            colors = [self.style.colors.success, self.style.colors.danger]
            explode = (0, 0.1)  # explode the 'Expense' slice

            # Create the pie chart
            wedges, texts, autotexts = self.ax.pie(
                sizes, 
                explode=explode, 
                labels=labels, 
                colors=colors,
                autopct='%1.1f%%',
                shadow=True, 
                startangle=90,
                textprops={'color': self.style.colors.primary}
            )

            # Customize autopct text color
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')

            self.ax.axis('equal')  # Equal aspect ratio ensures pie is circular
            self.ax.set_title("Income vs. Expense", color=self.style.colors.primary, fontsize=16, pad=20)
        
        self.chart_canvas.draw()


if __name__ == "__main__":
    # Ensure you create the database and table first!
    app = FinanceDashboard()
    app.mainloop()
