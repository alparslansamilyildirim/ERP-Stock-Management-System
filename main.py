"""
main.py

This is the main entry point for the ERP stock management application.
It initializes the database log table and launches the main GUI window.
"""
from gui import ERPApp
import tkinter as tk
from database import init_log_table

if __name__ == "__main__":
    init_log_table()
    root = tk.Tk()
    app = ERPApp(root)
    root.mainloop()