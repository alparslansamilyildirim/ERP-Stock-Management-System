"""
database.py

This module provides all database operations for the ERP stock management application.
It includes functions for CRUD operations, KOD mapping management, logging, and data export.
"""
import sqlite3
import pandas as pd

DB_PATH = "DB-Stok.db"
TABLE_NAME = "DB-Stok"

# --- KOD MAPPING TABLE INITIALIZATION ---
def init_kod_mapping_table():
    """Initialize the KOD mappings table if it doesn't exist."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kod_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_kod TEXT NOT NULL,
                alternative_value TEXT NOT NULL,
                created_date TIMESTAMP DEFAULT (datetime('now', 'localtime')),
                UNIQUE(original_kod, alternative_value)
            )
        ''')
        conn.commit()

# --- KOD MAPPING OPERATIONS ---
def create_kod_mapping(original_kod, alternative_value):
    """Create a new mapping between KOD and alternative value. Returns True if created, False if duplicate."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO kod_mappings (original_kod, alternative_value) VALUES (?, ?)',
                (str(original_kod).strip(), str(alternative_value).strip())
            )
            conn.commit()
        log_action('INFO', f'Created KOD mapping: {alternative_value} -> {original_kod}')
        return True
    except sqlite3.IntegrityError:
        log_action('WARNING', f'KOD mapping already exists: {alternative_value} -> {original_kod}')
        return False

def get_kod_mapping(alternative_value):
    """Get the original KOD for an alternative value. Returns the KOD or None if not found."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT original_kod FROM kod_mappings WHERE alternative_value = ?',
            (str(alternative_value).strip(),)
        )
        result = cursor.fetchone()
        return result[0] if result else None

def get_all_kod_mappings():
    """Get all existing KOD mappings as a list of tuples."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, original_kod, alternative_value, created_date FROM kod_mappings ORDER BY created_date DESC')
        return cursor.fetchall()

def delete_kod_mapping(mapping_id):
    """Delete a KOD mapping by its ID."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM kod_mappings WHERE id = ?', (mapping_id,))
        conn.commit()
    log_action('INFO', f'Deleted KOD mapping with ID: {mapping_id}')

def get_all_kod_values():
    """Get all unique KOD values from the main database table."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f'SELECT DISTINCT "KOD" FROM "{TABLE_NAME}" WHERE "KOD" IS NOT NULL ORDER BY "KOD"')
        return [row[0] for row in cursor.fetchall()]

def get_all_kod_and_paket_values():
    """Get all unique (KOD, PAKET) pairs from the main database, excluding NULL KODs."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f'SELECT DISTINCT "KOD", "PAKET" FROM "{TABLE_NAME}" WHERE "KOD" IS NOT NULL ORDER BY "KOD"')
        return cursor.fetchall()

# --- ENHANCED COMPARISON FUNCTIONS ---
def compare_with_mappings(file_df, db_df):
    """Compare uploaded file with database using KOD mappings. Returns dict of direct, mapped, and unmatched."""
    # Normalize data
    file_df['Value'] = file_df['Value'].astype(str).str.strip()
    db_df['KOD'] = db_df['KOD'].astype(str).str.strip()
    # Direct matches
    direct_matches = file_df[file_df['Value'].isin(db_df['KOD'])]
    # Check for mapped matches
    unmatched = file_df[~file_df['Value'].isin(db_df['KOD'])]
    mapped_matches = []
    still_unmatched = []
    for _, row in unmatched.iterrows():
        mapped_kod = get_kod_mapping(row['Value'])
        if mapped_kod and mapped_kod in db_df['KOD'].values:
            mapped_matches.append(row)
        else:
            still_unmatched.append(row)
    return {
        'direct_matches': direct_matches,
        'mapped_matches': pd.DataFrame(mapped_matches) if mapped_matches else pd.DataFrame(),
        'still_unmatched': pd.DataFrame(still_unmatched) if still_unmatched else pd.DataFrame()
    }

# --- LOGGING TO DATABASE ---
def init_log_table():
    """Initialize the actions_log table if it doesn't exist."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS actions_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT (datetime('now', 'localtime')),
                level TEXT,
                message TEXT
            )
        ''')
        conn.commit()

def log_action(level, message):
    """Insert a log entry into the actions_log table."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO actions_log (level, message) VALUES (?, ?)',
            (level, message)
        )
        conn.commit()

# --- COLUMN INFO ---
def get_column_info():
    """Return (columns, column_types) for the main database table."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f'PRAGMA table_info("{TABLE_NAME}")')
        col_info = cursor.fetchall()
        cols = [row[1] for row in col_info]
        col_types = {row[1]: row[2].upper() for row in col_info}
    return cols, col_types

# --- DATA OPERATIONS ---
def fetch_all_rows():
    """Fetch all rows from the main database table, including rowid."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f'SELECT rowid, * FROM "{TABLE_NAME}"')
        return cursor.fetchall()

def insert_row(values, cols):
    """Insert a new row into the main database table. Returns the new rowid."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        placeholders = ', '.join(['?'] * len(cols))
        cursor.execute(f'INSERT INTO "{TABLE_NAME}" ({", ".join([f'"{c}"' for c in cols])}) VALUES ({placeholders})', values)
        rowid = cursor.lastrowid
        conn.commit()
    log_action('INFO', f'Inserted row {rowid} with values: {values}')
    return rowid

def delete_row_by_rowid(rowid, cols):
    """Delete a row by rowid and return the old values."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f'SELECT {", ".join([f'"{c}"' for c in cols])} FROM "{TABLE_NAME}" WHERE rowid=?', (rowid,))
        old_vals = cursor.fetchone()
        cursor.execute(f'DELETE FROM "{TABLE_NAME}" WHERE rowid=?', (rowid,))
        conn.commit()
    log_action('INFO', f'Deleted row {rowid} (old values: {old_vals})')
    return old_vals

def update_cell(rowid, col_name, new_value, cols):
    """Update a single cell in the main database table. Returns the old values."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f'SELECT {", ".join([f'"{c}"' for c in cols])} FROM "{TABLE_NAME}" WHERE rowid=?', (rowid,))
        old_db_vals = cursor.fetchone()
        cursor.execute(f'UPDATE "{TABLE_NAME}" SET "{col_name}"=? WHERE rowid=?', (new_value, rowid))
        conn.commit()
    log_action('INFO', f'Updated row {rowid} column {col_name} to {new_value} (old values: {old_db_vals})')
    return old_db_vals

def undo_add(rowid):
    """Undo an add operation by deleting the row with the given rowid."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f'DELETE FROM "{TABLE_NAME}" WHERE rowid=?', (rowid,))
        conn.commit()
    log_action('INFO', f'Undo add: deleted row {rowid}')

def undo_update(rowid, old_vals, cols):
    """Undo an update operation by restoring the old values for the row."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        set_clause = ', '.join([f'"{c}"=?' for c in cols])
        cursor.execute(f'UPDATE "{TABLE_NAME}" SET {set_clause} WHERE rowid=?', list(old_vals) + [rowid])
        conn.commit()
    log_action('INFO', f'Undo update: restored row {rowid} to values: {old_vals}')

def export_to_excel(file_path):
    """Export the main database table to an Excel file at the given file path."""
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(f'SELECT * FROM "{TABLE_NAME}"', conn)
        df.to_excel(file_path, index=False)
    log_action('INFO', f'Exported table to {file_path}') 

# Initialize tables when module is imported
init_log_table()
init_kod_mapping_table() 