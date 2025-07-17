"""
mapping_gui.py

This module implements dialogs for managing KOD mappings in the ERP application.
It provides interfaces for viewing, creating, and deleting KOD mappings, and for mapping unmatched values.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from database import get_all_kod_mappings, delete_kod_mapping, get_all_kod_values, create_kod_mapping, get_all_kod_and_paket_values
from utils import create_dialog, create_treeview, create_combobox, labeled_entry, sort_treeview_column

def show_kod_mappings(root):
    """Show the KOD mappings management dialog."""
    dialog = create_dialog(root, "KOD Mappings Management", "800x600")
    # --- Tabs for Viewing and Creating Mappings ---
    notebook = ttk.Notebook(dialog)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)
    # --- Tab 1: View Existing Mappings ---
    view_frame = ttk.Frame(notebook)
    notebook.add(view_frame, text="Existing Mappings")
    # Treeview for existing mappings
    mapping_tree = create_treeview(view_frame, ["ID", "Original KOD", "Alternative Value", "Created Date"])
    mapping_cols = ["ID", "Original KOD", "Alternative Value", "Created Date"]
    mapping_col_types = {c: 'TEXT' for c in mapping_cols}
    for c in mapping_cols:
        mapping_tree.heading(c, text=c, command=lambda _c=c: sort_treeview_column(mapping_tree, _c, mapping_col_types, mapping_cols, False))
    mapping_tree.pack(side="left", fill="both", expand=True)
    mapping_scrollbar = ttk.Scrollbar(view_frame, orient="vertical", command=mapping_tree.yview)
    mapping_tree.configure(yscrollcommand=mapping_scrollbar.set)
    mapping_scrollbar.pack(side="right", fill="y")
    def load_mappings():
        """Load all existing KOD mappings into the treeview."""
        mapping_tree.delete(*mapping_tree.get_children())
        mappings = get_all_kod_mappings()
        for mapping in mappings:
            if isinstance(mapping, dict):
                mapping_tree.insert("", "end", values=[mapping[c] for c in mapping_cols])
            else:
                mapping_tree.insert("", "end", values=list(mapping))
    load_mappings()
    def delete_selected_mapping():
        """Delete the selected KOD mapping after confirmation."""
        selected = mapping_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a mapping to delete.")
            return
        mapping_id = mapping_tree.item(selected[0])['values'][0]
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this mapping?"):
            delete_kod_mapping(mapping_id)
            load_mappings()
    ttk.Button(view_frame, text="Delete Selected", command=delete_selected_mapping).pack(pady=5)
    # --- Tab 2: Create New Mapping ---
    create_frame = ttk.Frame(notebook)
    notebook.add(create_frame, text="Create New Mapping")
    # Form for creating new mapping
    form_frame = ttk.Frame(create_frame)
    form_frame.pack(fill="x", padx=20, pady=20)
    alt_value_var = tk.StringVar()
    _, alt_value_entry = labeled_entry(form_frame, "Alternative Value:", textvariable=alt_value_var, width=30, row=0, column=0, padx=10, pady=5)
    original_kod_var = tk.StringVar()
    ttk.Label(form_frame, text="Original KOD:").grid(row=1, column=0, sticky="w", pady=5)
    # --- Table with search for KOD and PAKET ---
    search_var = tk.StringVar()
    search_entry = ttk.Entry(form_frame, textvariable=search_var, width=27)
    search_entry.grid(row=1, column=1, padx=(10, 0), pady=(0, 2), sticky="ew")
    kod_paket_list = get_all_kod_and_paket_values()
    kod_tree = ttk.Treeview(form_frame, columns=("KOD", "PAKET"), show="headings", height=6)
    kod_tree.heading("KOD", text="KOD")
    kod_tree.heading("PAKET", text="PAKET")
    kod_tree.column("KOD", width=100)
    kod_tree.column("PAKET", width=150)
    for kod, paket in kod_paket_list:
        kod_tree.insert("", "end", values=(kod, paket))
    kod_tree.grid(row=2, column=1, padx=(10, 0), pady=5, sticky="ew")
    def on_tree_select(event):
        """Set the original KOD variable when a KOD is selected from the table."""
        selected = kod_tree.selection()
        if selected:
            values = kod_tree.item(selected[0], "values")
            original_kod_var.set(values[0])
    kod_tree.bind("<<TreeviewSelect>>", on_tree_select)
    def filter_kod_table(*args):
        """Filter the KOD/PAKET table based on the search entry."""
        query = search_var.get().lower()
        kod_tree.delete(*kod_tree.get_children())
        for kod, paket in kod_paket_list:
            if query in str(kod).lower() or query in str(paket).lower():
                kod_tree.insert("", "end", values=(kod, paket))
    search_var.trace_add('write', filter_kod_table)
    def create_mapping():
        """Create a new KOD mapping if both fields are filled and mapping does not exist."""
        alt_value = alt_value_var.get().strip()
        original_kod = original_kod_var.get().strip()
        if not alt_value or not original_kod:
            messagebox.showerror("Error", "Please fill in both fields.")
            return
        if create_kod_mapping(original_kod, alt_value):
            messagebox.showinfo("Success", f"Mapping created: {alt_value} -> {original_kod}")
            alt_value_var.set("")
            original_kod_var.set("")
            load_mappings()  # Refresh the mappings list
        else:
            messagebox.showwarning("Warning", "This mapping already exists.")
    button_frame = ttk.Frame(dialog)
    button_frame.pack(side="bottom", fill="x", pady=(0, 10), padx=10)
    ttk.Button(button_frame, text="Create Mapping", command=create_mapping).pack(side="right")

def show_mapping_dialog(root, unmatched_values):
    """Show dialog to create mappings for unmatched values from an uploaded file."""
    if unmatched_values.empty:
        messagebox.showinfo("Info", "No unmatched values to map.")
        return
    dialog = create_dialog(root, "Create KOD Mappings", "600x500")
    kod_values = get_all_kod_values()
    notebook = ttk.Notebook(dialog)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)
    create_frame = ttk.Frame(notebook)
    notebook.add(create_frame, text="Create New Mapping")
    form_frame = ttk.Frame(create_frame)
    form_frame.pack(fill="x", padx=20, pady=20)
    alt_value_var = tk.StringVar()
    _, alt_value_entry = labeled_entry(form_frame, "Alternative Value:", textvariable=alt_value_var, width=30, row=0, column=0, padx=10, pady=5)
    original_kod_var = tk.StringVar()
    ttk.Label(form_frame, text="Original KOD:").grid(row=1, column=0, sticky="w", pady=5)
    search_var = tk.StringVar()
    search_entry = ttk.Entry(form_frame, textvariable=search_var, width=27)
    search_entry.grid(row=1, column=1, padx=(10, 0), pady=(0, 2), sticky="ew")
    kod_paket_list = get_all_kod_and_paket_values()
    kod_tree = ttk.Treeview(form_frame, columns=("KOD", "PAKET"), show="headings", height=6)
    kod_tree.heading("KOD", text="KOD")
    kod_tree.heading("PAKET", text="PAKET")
    kod_tree.column("KOD", width=100)
    kod_tree.column("PAKET", width=150)
    for kod, paket in kod_paket_list:
        kod_tree.insert("", "end", values=(kod, paket))
    kod_tree.grid(row=2, column=1, padx=(10, 0), pady=5, sticky="ew")
    def on_tree_select(event):
        """Set the original KOD variable when a KOD is selected from the table."""
        selected = kod_tree.selection()
        if selected:
            values = kod_tree.item(selected[0], "values")
            original_kod_var.set(values[0])
    kod_tree.bind("<<TreeviewSelect>>", on_tree_select)
    def filter_kod_table(*args):
        """Filter the KOD/PAKET table based on the search entry."""
        query = search_var.get().lower()
        kod_tree.delete(*kod_tree.get_children())
        for kod, paket in kod_paket_list:
            if query in str(kod).lower() or query in str(paket).lower():
                kod_tree.insert("", "end", values=(kod, paket))
    search_var.trace_add('write', filter_kod_table)
    def create_mapping():
        """Create a new KOD mapping if both fields are filled and mapping does not exist."""
        alt_value = alt_value_var.get().strip()
        original_kod = original_kod_var.get().strip()
        if not alt_value or not original_kod:
            messagebox.showerror("Error", "Please fill in both fields.")
            return
        if create_kod_mapping(original_kod, alt_value):
            messagebox.showinfo("Success", f"Mapping created: {alt_value} -> {original_kod}")
            alt_value_var.set("")
            original_kod_var.set("")
        else:
            messagebox.showwarning("Warning", "This mapping already exists.")
    button_frame = ttk.Frame(dialog)
    button_frame.pack(side="bottom", fill="x", pady=(0, 10), padx=10)
    ttk.Button(button_frame, text="Create Mapping", command=create_mapping).pack(side="right")
    if not unmatched_values.empty:
        first_value = unmatched_values.iloc[0]['Value']
        notebook.select(create_frame)
        alt_value_var.set(first_value)
        alt_value_entry.focus_set()
        