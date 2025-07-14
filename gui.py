"""
gui.py

This module implements the main graphical user interface (GUI) for the ERP stock management application.
It provides the ERPApp class, which manages the main window, data display, user interactions, and integration
with the database and mapping management dialogs.
"""
import platform
import tkinter as tk
from tkinter import ttk, filedialog
from database import (
    get_column_info, fetch_all_rows, insert_row, delete_row_by_rowid, update_cell,
    undo_add, undo_update, export_to_excel,
    compare_with_mappings, create_kod_mapping, get_all_kod_values, get_all_kod_mappings, delete_kod_mapping, get_kod_mapping
)
from utils import autosize_columns, create_dialog, create_treeview, create_combobox, labeled_entry, sort_treeview_column
import pandas as pd
from tkinter import messagebox
from shortcuts import bind_fullscreen_shortcuts, bind_common_shortcuts
from mapping_gui import show_kod_mappings, show_mapping_dialog


# Utility: Toggle fullscreen for any Tkinter window

def toggle_fullscreen_for_window(window, state_attr='_is_fullscreen'):
    is_fullscreen = getattr(window, state_attr, False)
    is_fullscreen = not is_fullscreen
    setattr(window, state_attr, is_fullscreen)
    window.attributes("-fullscreen", is_fullscreen)

class ERPApp:
    def __init__(self, root):
        style = ttk.Style()
        self.root = root
        self.root.title("Stock-Management")
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.undo_stack = []
        self.selected_iid = None
        self.cols, self.col_types = get_column_info()
        self.cell_editor = None  # Initialize cell editor
        self.setup_widgets()
        self.load_data()
        self.root.after(100, self.autosize_columns)
        self.root.bind('<Configure>', lambda e: self.autosize_columns())
        # Bind keyboard shortcuts for fullscreen, undo, and reload
        bind_fullscreen_shortcuts(self.root)
        bind_common_shortcuts(self.root, undo_callback=lambda e: self.undo_action(), reload_callback=lambda e: self.load_data())
        self.is_fullscreen = False  # Track fullscreen state

    def setup_widgets(self):
        # --- Search Bar ---
        search_frame = ttk.Frame(self.root)
        search_frame.pack(fill="x", padx=10, pady=(10,5))
        ttk.Label(search_frame, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side="left", fill="x", expand=True, padx=(5,0))
        search_entry.bind("<KeyRelease>", self.filter_rows)
        self.row_count_var = tk.StringVar(value="Rows: 0")
        count_label = ttk.Label(search_frame, textvariable=self.row_count_var)
        count_label.pack(side="right")
        # --- Data Table (Treeview) ---
        frame = ttk.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(frame, columns=self.cols, show="headings")
        for c in self.cols:
            self.tree.heading(c, text=c, command=lambda _c=c: self.sort_column(_c, False))
            self.tree.column(c, width=120, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind('<Double-1>', self.on_tree_cell_double_click)
        # Force visible colors for all rows
        self.tree.tag_configure('all', foreground='black', background='white')
        # --- Action Buttons ---
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(side="bottom", fill="x", expand=False, padx=5, pady=5)
        btn_frame.columnconfigure(tuple(range(4)), weight=1)
        ttk.Button(btn_frame, text="Add Row",    command=self.add_row).grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        ttk.Button(btn_frame, text="Export to Excel", command=self.export_to_excel).grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        ttk.Button(btn_frame, text="Upload a File", command=self.upload_file).grid(row=0, column=2, padx=2, pady=2, sticky="ew")
        ttk.Button(btn_frame, text="Manage KOD Mappings", command=lambda: show_kod_mappings(self.root)).grid(row=0, column=3, padx=2, pady=2, sticky="ew")

    def clear_selection(self):
        """Clear any selection in the data table."""
        self.tree.selection_remove(self.tree.selection())
        self.selected_iid = None

    def update_row_count(self):
        """Update the displayed row count based on the current data table."""
        count = len(self.tree.get_children())
        self.row_count_var.set(f"Rows: {count}")

    def filter_rows(self, event=None):
        """Filter rows in the data table based on the search bar input."""
        query = self.search_var.get().lower()
        self.tree.delete(*self.tree.get_children())
        for row in fetch_all_rows():
            values = [str(v) if v is not None else '' for v in row[1:]]
            if not query or any(query in v.lower() for v in values):
                self.tree.insert("", "end", iid=str(row[0]), values=values)
        self.update_row_count()

    def sort_column(self, col, reverse=False):
        """Sort the data table by the given column."""
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children()]
        col_type = self.col_types.get(col, 'TEXT')
        def try_cast(val):
            if col_type in ('INTEGER', 'REAL', 'NUMERIC', 'FLOAT', 'DOUBLE'):
                try:
                    return float(val) if val != '' else float('-inf')
                except ValueError:
                    return float('-inf')
            return val.lower() if isinstance(val, str) else str(val)
        items.sort(key=lambda t: try_cast(t[0]), reverse=reverse)
        for index, (_, k) in enumerate(items):
            self.tree.move(k, '', index)
        self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))

    def load_data(self):
        """Reload all data from the database and refresh the table."""
        self.search_var.set("")
        self.filter_rows()
        self.clear_selection()
        self.autosize_columns()

    def on_tree_select(self, _):
        """Handle row selection in the data table."""
        sel = self.tree.selection()
        if not sel: return
        self.selected_iid = sel[0]

    def show_add_row_dialog(self):
        """Show a dialog for adding a new row to the database."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Row")
        dialog.transient(self.root)
        dialog.grab_set()
        entries = {}
        for i, col in enumerate(self.cols):
            tk.Label(dialog, text=col).grid(row=i, column=0, padx=10, pady=5, sticky="e")
            entry = tk.Entry(dialog)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="w")
            entries[col] = entry
        def on_ok():
            # Type validation for each entry
            validated_values = []
            for c in self.cols:
                val = entries[c].get()
                col_type = self.col_types.get(c, 'TEXT')
                if val == '':
                    validated_values.append(None)
                    continue
                try:
                    if col_type in ('INTEGER', 'INT'):
                        validated_values.append(int(val))
                    elif col_type in ('REAL', 'NUMERIC', 'FLOAT', 'DOUBLE'):
                        validated_values.append(float(val))
                    else:
                        validated_values.append(val)
                except ValueError:
                    messagebox.showerror("Invalid Input", f"Column '{c}' expects type {col_type}. Invalid value: '{val}'")
                    return
            try:
                rowid = insert_row(validated_values, self.cols)
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to add row: {e}")
                return
            self.undo_stack.append({'action': 'add', 'rowid': rowid})
            self.load_data()
            dialog.destroy()
        def on_cancel():
            dialog.destroy()
        btn_frame = tk.Frame(dialog)
        btn_frame.grid(row=len(self.cols), column=0, columnspan=2, pady=10)
        tk.Button(btn_frame, text="OK", width=10, command=on_ok).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancel", width=10, command=on_cancel).pack(side="left", padx=5)
        dialog.bind('<Return>', lambda e: on_ok())
        dialog.bind('<Escape>', lambda e: on_cancel())
        dialog.wait_window()

    def add_row(self):
        """Open the add row dialog."""
        self.show_add_row_dialog()

    def undo_action(self):
        """Undo the last add or update action."""
        if not self.undo_stack:
            return
        last = self.undo_stack.pop()
        act = last['action']
        if act == 'add':
            undo_add(last['rowid'])
        elif act == 'update':
            undo_update(last['rowid'], last['old'], self.cols)
        self.load_data()

    def export_to_excel(self):
        """Export the current database table to an Excel file."""
        file_path = filedialog.asksaveasfilename(
            defaultextension='.xlsx',
            filetypes=[('Excel files', '*.xlsx')],
            title='Save Excel File As'
        )
        if not file_path:
            return
        export_to_excel(file_path)
        print(f'Exported database to {file_path}')

    def autosize_columns(self):
        """Automatically resize columns in the data table to fit content."""
        autosize_columns(self.tree, self.cols, self.root)

    def get_treeview_column_from_event(self, event):
        """Given a mouse event, return the (rowid, column name) in the treeview, or (None, None) if not a cell."""
        region = self.tree.identify('region', event.x, event.y)
        if region != 'cell':
            return None, None
        rowid = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not rowid or not col:
            return None, None
        col_index = int(col.replace('#', '')) - 1
        col_name = self.cols[col_index]
        return rowid, col_name

    def on_tree_cell_double_click(self, event):
        """Enable in-place editing of a cell when double-clicked."""
        if self.cell_editor is not None:
            try:
                self.cell_editor.destroy()
            except Exception:
                pass
            self.cell_editor = None
        rowid, col_name = self.get_treeview_column_from_event(event)
        if not rowid or not col_name:
            return
        bbox = self.tree.bbox(rowid, col_name)
        if not bbox:
            return
        x, y, width, height = bbox
        value = self.tree.set(rowid).get(col_name, "")
        self.cell_editor = tk.Entry(self.tree)
        self.cell_editor.insert(0, value)
        self.cell_editor.select_range(0, tk.END)
        self.cell_editor.focus()
        self.cell_editor.place(x=x, y=y, width=width, height=height)
        def save_edit(event=None):
            if self.cell_editor is None:
                return
            new_value = self.cell_editor.get()
            col_type = self.col_types.get(col_name, 'TEXT')
            # Type validation for cell edit
            if new_value == '':
                validated_value = None
            else:
                try:
                    if col_type in ('INTEGER', 'INT'):
                        validated_value = int(new_value)
                    elif col_type in ('REAL', 'NUMERIC', 'FLOAT', 'DOUBLE'):
                        validated_value = float(new_value)
                    else:
                        validated_value = new_value
                except ValueError:
                    messagebox.showerror("Invalid Input", f"Column '{col_name}' expects type {col_type}. Invalid value: '{new_value}'")
                    return
            old_values = self.tree.item(rowid, 'values')
            col_idx = self.cols.index(col_name)
            old_value = old_values[col_idx]
            if validated_value != old_value:
                try:
                    old_db_vals = update_cell(int(rowid), col_name, validated_value, self.cols)
                except Exception as e:
                    messagebox.showerror("Database Error", f"Failed to update cell: {e}")
                    return
                self.undo_stack.append({'action': 'update', 'rowid': int(rowid), 'old': old_db_vals})
                self.load_data()
                self.tree.selection_set(rowid)
            if self.cell_editor is not None:
                try:
                    self.cell_editor.destroy()
                except Exception:
                    pass
                self.cell_editor = None
        self.cell_editor.bind('<Return>', save_edit)
        self.cell_editor.bind('<FocusOut>', lambda e: self.cell_editor and self.cell_editor.destroy())

    def upload_file(self):
        """Open a file dialog to upload an Excel file and display its contents in a popup window."""
        file_path = filedialog.askopenfilename(
            defaultextension='.xlsx',
            filetypes=[('Excel files', '*.xlsx')],
            title='Open Excel File'
        )
        if not file_path:
            return
        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file:\n{e}")
            return
        # --- Add Box and In Stock Columns Left of Qty ---
        cols = list(df.columns)
        qty_index = cols.index('Qty') if 'Qty' in cols else len(cols)
        cols.insert(qty_index, 'In Stock')
        cols.insert(qty_index, 'Box')
        # Create popup window to display uploaded data
        popup = create_dialog(self.root, "BOM-List", "800x400")
        frame = ttk.Frame(popup)
        frame.pack(fill="both", expand=True)
        tree = create_treeview(frame, cols)
        for c in cols:
            tree.heading(c, text=c, command=lambda _c=c: sort_treeview_column(tree, _c, self.col_types, cols, False))
        # --- Prepare Database DataFrame for Comparison ---
        db_rows = fetch_all_rows()
        db_cols = pd.Index([str(c) for c in get_column_info()[0]])
        db_data = [row[1:] for row in db_rows]
        db_df = pd.DataFrame(db_data, columns=db_cols)
        # --- Insert Rows with In Stock (Difference) ---
        for idx, row in df.iterrows():
            value = row.get('Value')
            qty_file = row.get('Qty')
            stock_check = ""
            box = ""  # Will be filled with YER from db_row if available
            # Try direct match first
            db_row = db_df[db_df['KOD'] == value]
            if db_row.empty:
                # Try mapped match
                mapped_kod = get_kod_mapping(value)
                if mapped_kod:
                    db_row = db_df[db_df['KOD'] == mapped_kod]
            if not db_row.empty:
                qty_db = db_row.iloc[0].get('MİKTAR')
                box = db_row.iloc[0].get('YER', "")  # Fill Box with YER
                if qty_file is not None and qty_db is not None and str(qty_file).strip() != "" and str(qty_db).strip() != "":
                    try:
                        qty_file_num = int(qty_file)
                        qty_db_num = int(qty_db)
                        if qty_file_num > qty_db_num:
                            stock_check = qty_db_num - qty_file_num
                        else:
                            stock_check = qty_file_num
                    except (TypeError, ValueError):
                        stock_check = ""
                else:
                    stock_check = ""
            else:
                stock_check = ""
            values = list(row)
            values.insert(qty_index, box)
            values.insert(qty_index + 1, stock_check)
            tree.insert("", "end", iid=str(idx), values=values)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        hsb.grid(row=1, column=0, sticky="ew")
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        bind_fullscreen_shortcuts(popup)
        # --- Qty Multiplier Section ---
        amount_frame = ttk.Frame(popup)
        amount_frame.pack(fill="x", padx=10, pady=(5, 0))
        amount_var = tk.StringVar()
        _, amount_entry = labeled_entry(amount_frame, "The Amount of Card:", textvariable=amount_var, width=10, row=0, column=0, padx=10, pady=0)
        def apply_qty_multiplier(event=None):
            skipped_rows = []
            try:
                multiplier = int(amount_var.get())
            except ValueError:
                multiplier = 1
            if 'Qty_orig' not in df.columns:
                df['Qty_orig'] = df['Qty']
            for idx, row in df.iterrows():
                orig_qty = row.get('Qty_orig', row['Qty'])
                if orig_qty is None or str(orig_qty).strip() == "":
                    new_qty = orig_qty
                    skipped_rows.append(idx)
                else:
                    try:
                        orig_qty_num = int(orig_qty)
                        new_qty = orig_qty_num * multiplier if multiplier != 1 else orig_qty_num
                    except (TypeError, ValueError):
                        new_qty = orig_qty
                        skipped_rows.append(idx)
                df.at[idx, 'Qty'] = new_qty
                values = list(tree.item(str(idx), 'values'))
                try:
                    qty_col_idx = cols.index('Qty')
                    box_col_idx = cols.index('Box')
                    stock_check_col_idx = cols.index('In Stock')
                except ValueError:
                    continue
                values[qty_col_idx] = str(new_qty)
                # Unified stock_check calculation for direct and mapped matches
                value = values[cols.index('Value')] if 'Value' in cols else None
                stock_check = ""
                box = ""
                db_row = db_df[db_df['KOD'] == value]
                if db_row.empty:
                    mapped_kod = get_kod_mapping(value)
                    if mapped_kod:
                        db_row = db_df[db_df['KOD'] == mapped_kod]
                if not db_row.empty:
                    qty_db = db_row.iloc[0].get('MİKTAR')
                    box = db_row.iloc[0].get('YER', "")  # Fill Box with YER
                    if new_qty is not None and qty_db is not None and str(new_qty).strip() != "" and str(qty_db).strip() != "":
                        try:
                            qty_file_num = int(new_qty)
                            qty_db_num = int(qty_db)
                            if qty_file_num > qty_db_num:
                                stock_check = qty_db_num - qty_file_num
                            else:
                                stock_check = qty_file_num
                        except (TypeError, ValueError):
                            stock_check = ""
                    else:
                        stock_check = ""
                else:
                    stock_check = ""
                values[box_col_idx] = str(box)
                values[stock_check_col_idx] = str(stock_check)
                tree.item(str(idx), values=values)
            if skipped_rows:
                messagebox.showwarning(
                    "Qty Multiplier",
                    f"Skipped {len(skipped_rows)} row(s) due to invalid or missing 'Qty' values."
                )
            compare_with_database()
                
        amount_entry.bind('<Return>', apply_qty_multiplier)
      
         
        # --- Compare with Database Section ---
        def compare_with_database():
            # Compare uploaded file with database using KOD mappings
            db_rows = fetch_all_rows()
            db_cols = pd.Index([str(c) for c in get_column_info()[0]])
            db_data = [row[1:] for row in db_rows]
            db_df = pd.DataFrame(db_data, columns=db_cols)
            if 'Value' not in df.columns or 'KOD' not in db_df.columns:
                messagebox.showerror("Error", "'Value' column in file or 'KOD' column in database not found.")
                return
            comparison_result = compare_with_mappings(df, db_df)
            # Clear previous tags
            for idx in df.index:
                tree.item(str(idx), tags=())
            # Tag direct matches
            for idx, row in comparison_result['direct_matches'].iterrows():
                tree.item(str(idx), tags=("direct_match",))
            # Tag mapped matches
            for idx, row in comparison_result['mapped_matches'].iterrows():
                tree.item(str(idx), tags=("mapped_match",))
            # Configure tags for highlighting
            tree.tag_configure("direct_match", background="#4caf50", foreground="#fff")
            tree.tag_configure("mapped_match", background="#ff9800", foreground="#fff")
        # Automatically run comparison after file is loaded
        compare_with_database()
        # --- Row Double-Click Handler for Mapping ---
        def on_popup_row_double_click(event):
            selected = tree.selection()
            if not selected:
                return
            iid = selected[0]
            tags = tree.item(iid, 'tags')
            value = tree.item(iid, 'values')[cols.index('Value')] if 'Value' in cols else None
            if not value:
                return
            if 'direct_match' in tags:
                # Select the corresponding row in the main window
                try:
                    kod_idx = self.cols.index('KOD')
                except ValueError:
                    return
                for main_iid in self.tree.get_children():
                    db_row_values = self.tree.item(main_iid, 'values')
                    if db_row_values and len(db_row_values) > kod_idx:
                        db_kod = db_row_values[kod_idx]
                        if db_kod is not None and str(db_kod).strip() == str(value).strip():
                            self.tree.selection_set(main_iid)
                            self.tree.see(main_iid)
                            self.root.lift()
                            self.root.focus_force()
                            break
            elif 'mapped_match' in tags:
                # For mapped_match, get the original KOD and select it
                from database import get_kod_mapping
                original_kod = get_kod_mapping(value)
                if not original_kod:
                    return
                try:
                    kod_idx = self.cols.index('KOD')
                except ValueError:
                    return
                for main_iid in self.tree.get_children():
                    db_row_values = self.tree.item(main_iid, 'values')
                    if db_row_values and len(db_row_values) > kod_idx:
                        db_kod = db_row_values[kod_idx]
                        if db_kod is not None and str(db_kod).strip() == str(original_kod).strip():
                            self.tree.selection_set(main_iid)
                            self.tree.see(main_iid)
                            self.root.lift()
                            self.root.focus_force()
                            break
            else:
                # Unmatched: open mapping dialog, pre-fill value
                import pandas as pd
                unmatched_df = pd.DataFrame([{'Value': value}])
                show_mapping_dialog(self.root, unmatched_df)
        tree.bind('<Double-1>', on_popup_row_double_click)