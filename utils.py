"""
utils.py

This module provides utility functions for the ERP application, including dialog creation,
treeview setup, combobox creation, labeled entries, autosizing columns, and treeview sorting.
"""
import tkinter as tk
from tkinter import ttk
from typing import Optional, Sequence

# Utility to create a dialog window

def create_dialog(root: tk.Tk, title: str, geometry: str) -> tk.Toplevel:
    dialog = tk.Toplevel(root)
    dialog.title(title)
    dialog.geometry(geometry)
    dialog.transient(root)
    dialog.grab_set()
    return dialog

# Utility to create a treeview with columns and optional headings

def create_treeview(parent, columns: Sequence[str], headings: Optional[Sequence[str]] = None, column_width: int = 120, show: str = "headings"):
    # Only allow valid show values
    if show not in ("tree", "headings", "tree headings", ""):
        show = "headings"
    tree = ttk.Treeview(parent, columns=list(columns), show=show)
    for i, c in enumerate(columns):
        tree.heading(c, text=headings[i] if headings else c)
        tree.column(c, width=column_width, anchor="w")
    return tree

# Utility to create a combobox

def create_combobox(parent, values, textvariable: Optional[tk.Variable] = None, width: int = 20):
    if textvariable is not None:
        combo = ttk.Combobox(parent, values=values, textvariable=textvariable, width=width)
    else:
        combo = ttk.Combobox(parent, values=values, width=width)
    return combo

# Utility to create a labeled entry (returns label and entry)

def labeled_entry(parent, label_text: str, textvariable: Optional[tk.Variable] = None, width: int = 20, row: int = 0, column: int = 0, padx: int = 0, pady: int = 0):
    label = ttk.Label(parent, text=label_text)
    if textvariable is not None:
        entry = ttk.Entry(parent, textvariable=textvariable, width=width)
    else:
        entry = ttk.Entry(parent, width=width)
    label.grid(row=row, column=column, sticky="w", padx=padx, pady=pady)
    entry.grid(row=row, column=column+1, padx=padx, pady=pady)
    return label, entry

# Utility to normalize a DataFrame column (strip and convert to string)

def normalize_column(df, col):
    df[col] = df[col].astype(str).str.strip()
    return df 

def autosize_columns(tree, cols, root):
    window_width = root.winfo_width()
    margin = 40  # Leave some margin for window borders/scrollbars
    available_width = max(window_width - margin, 200)
    n_cols = len(cols)
    min_width = 80
    if n_cols == 0:
        return
    col_width = max(int(available_width / n_cols), min_width)
    for c in cols:
        tree.column(c, width=col_width) 

def sort_treeview_column(tree, col, col_types, columns, reverse=False):
    """
    Sort a Treeview by the given column.
    Args:
        tree: The ttk.Treeview instance.
        col: The column name to sort by.
        col_types: Dict mapping column names to types (e.g., from get_column_info()).
        columns: List of column names (order matters).
        reverse: Whether to sort in reverse order.
    Usage:
        for c in columns:
            tree.heading(c, text=c, command=lambda _c=c: sort_treeview_column(tree, _c, col_types, columns, False))
    """
    items = [(tree.set(k, col), k) for k in tree.get_children()]
    col_type = col_types.get(col, 'TEXT')
    def try_cast(val):
        if col_type in ('INTEGER', 'REAL', 'NUMERIC', 'FLOAT', 'DOUBLE'):
            try:
                return float(val) if val != '' else float('-inf')
            except ValueError:
                return float('-inf')
        return val.lower() if isinstance(val, str) else str(val)
    items.sort(key=lambda t: try_cast(t[0]), reverse=reverse)
    for index, (_, k) in enumerate(items):
        tree.move(k, '', index)
    # Re-bind the header for toggling sort order
    tree.heading(col, command=lambda: sort_treeview_column(tree, col, col_types, columns, not reverse)) 