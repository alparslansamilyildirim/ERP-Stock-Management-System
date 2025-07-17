"""
database.py

This module provides all database operations for the ERP stock management application.
It includes functions for CRUD operations, KOD mapping management, logging, and data export.
"""
import mysql.connector
import pandas as pd
import sys
import os
"""
database.py
...
"""

MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'sql7790309',
    'password': 'egeNDfRDh7',
    'database': 'sql7790309',
    'port': 3306,
    'charset': 'utf8mb4'
}

TABLE_NAME = "ERP_DB"

# --- KOD MAPPING TABLE INITIALIZATION ---
def init_kod_mapping_table():
    """Initialize the KOD mappings table if it doesn't exist."""
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kod_mappings (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        original_kod VARCHAR(100) NOT NULL,
        alternative_value VARCHAR(100) NOT NULL,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(original_kod, alternative_value)
        )
    ''')
    conn.commit()
    conn.close()

# --- KOD MAPPING OPERATIONS ---
def create_kod_mapping(original_kod, alternative_value):
    """Create a new mapping between KOD and alternative value. Returns True if created, False if duplicate."""
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO kod_mappings (original_kod, alternative_value) VALUES (%s, %s)',
            (str(original_kod).strip(), str(alternative_value).strip())
        )
        conn.commit()
        conn.close()
        log_action('INFO', f'Created KOD mapping: {alternative_value} -> {original_kod}')
        return True
    except mysql.connector.IntegrityError:
        log_action('WARNING', f'KOD mapping already exists: {alternative_value} -> {original_kod}')
        return False

def get_kod_mapping(alternative_value):
    """Get the original KOD for an alternative value. Returns the KOD or None if not found."""
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        'SELECT original_kod FROM kod_mappings WHERE alternative_value = %s',
        (str(alternative_value).strip(),)
    )
    result = cursor.fetchone()
    conn.close()
    if result and isinstance(result, dict):
        return result['original_kod']
    return None

def get_all_kod_mappings():
    """Get all existing KOD mappings as a list of tuples."""
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT id, original_kod, alternative_value, created_date FROM kod_mappings ORDER BY created_date DESC')
    result = cursor.fetchall()
    conn.close()
    return result

def delete_kod_mapping(mapping_id):
    """Delete a KOD mapping by its ID."""
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM kod_mappings WHERE id = %s', (mapping_id,))
    conn.commit()
    conn.close()
    log_action('INFO', f'Deleted KOD mapping with ID: {mapping_id}')

def get_all_kod_values():
    """Get all unique KOD values from the main database table."""
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f'SELECT DISTINCT `KOD` FROM `{TABLE_NAME}` WHERE `KOD` IS NOT NULL ORDER BY `KOD`')
    result = cursor.fetchall()
    conn.close()
    return [row['KOD'] for row in result if isinstance(row, dict) and 'KOD' in row]

def get_all_kod_and_paket_values():
    """Get all unique (KOD, PAKET) pairs from the main database, excluding NULL KODs."""
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f'SELECT DISTINCT `KOD`, `PAKET` FROM `{TABLE_NAME}` WHERE `KOD` IS NOT NULL ORDER BY `KOD`')
    result = cursor.fetchall()
    conn.close()
    return [(row['KOD'], row['PAKET']) for row in result if isinstance(row, dict) and 'KOD' in row and 'PAKET' in row]

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
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS actions_log (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        level VARCHAR(20),
            message TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_action(level, message):
    """Insert a log entry into the actions_log table."""
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO actions_log (level, message) VALUES (%s, %s)',
        (level, message)
    )
    conn.commit()
    conn.close()

# --- COLUMN INFO ---
def get_column_info():
    """Return (columns, column_types) for the main database table."""
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f'SHOW COLUMNS FROM `{TABLE_NAME}`')
    col_info = cursor.fetchall()
    cols = [row['Field'] for row in col_info if isinstance(row, dict) and 'Field' in row]
    col_types = {row['Field']: row['Type'].upper() if isinstance(row['Type'], str) else str(row['Type']).upper() for row in col_info if isinstance(row, dict) and 'Field' in row and 'Type' in row}
    conn.close()
    return cols, col_types

# --- DATA OPERATIONS ---
def fetch_all_rows():
    """Fetch all rows from the main database table, including rowid."""
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f'SELECT * FROM `{TABLE_NAME}`')
    result = cursor.fetchall()
    conn.close()
    return result

def insert_row(values, cols):
    """Insert a new row into the main database table. Returns the new rowid."""
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    placeholders = ', '.join(['%s'] * len(cols))
    cursor.execute(f'INSERT INTO "{TABLE_NAME}" ({", ".join([f'"{c}"' for c in cols])}) VALUES ({placeholders})', values)
    rowid = cursor.lastrowid
    conn.commit()
    conn.close()
    log_action('INFO', f'Inserted row {rowid} with values: {values}')
    return rowid

def delete_row_by_rowid(rowid, cols):
    """Delete a row by rowid and return the old values."""
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    cursor.execute(f'SELECT {", ".join([f'"{c}"' for c in cols])} FROM "{TABLE_NAME}" WHERE rowid=?', (rowid,))
    old_vals = cursor.fetchone()
    cursor.execute(f'DELETE FROM "{TABLE_NAME}" WHERE rowid=?', (rowid,))
    conn.commit()
    conn.close()
    log_action('INFO', f'Deleted row {rowid} (old values: {old_vals})')
    return old_vals

def update_cell(rowid, col_name, new_value, cols):
    """Update a single cell in the main database table. Returns the old values."""
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    cursor.execute(f'SELECT {", ".join([f'"{c}"' for c in cols])} FROM "{TABLE_NAME}" WHERE rowid=?', (rowid,))
    old_db_vals = cursor.fetchone()
    cursor.execute(f'UPDATE "{TABLE_NAME}" SET "{col_name}"=? WHERE rowid=?', (new_value, rowid))
    conn.commit()
    conn.close()
    log_action('INFO', f'Updated row {rowid} column {col_name} to {new_value} (old values: {old_db_vals})')
    return old_db_vals

def undo_add(rowid):
    """Undo an add operation by deleting the row with the given rowid."""
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    cursor.execute(f'DELETE FROM "{TABLE_NAME}" WHERE rowid=?', (rowid,))
    conn.commit()
    conn.close()
    log_action('INFO', f'Undo add: deleted row {rowid}')

def undo_update(rowid, old_vals, cols):
    """Undo an update operation by restoring the old values for the row."""
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    set_clause = ', '.join([f'"{c}"=?' for c in cols])
    cursor.execute(f'UPDATE "{TABLE_NAME}" SET {set_clause} WHERE rowid=?', list(old_vals) + [rowid])
    conn.commit()
    conn.close()
    log_action('INFO', f'Undo update: restored row {rowid} to values: {old_vals}')

def export_to_excel(file_path):
    """Export the main database table to an Excel file at the given file path."""
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    df = pd.read_sql_query(f'SELECT * FROM "{TABLE_NAME}"', conn)
    df.to_excel(file_path, index=False)
    conn.close()
    log_action('INFO', f'Exported table to {file_path}')

def print_table_column_types():
    """Print column names and their types for the main database table (for debugging)."""
    import mysql.connector
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f'SHOW COLUMNS FROM `{TABLE_NAME}`')
    col_info = cursor.fetchall()
    print(f"Column types for table '{TABLE_NAME}':")
    for row in col_info:
        if isinstance(row, dict):
            print(f"  {row['Field']}: {row['Type']}")
    conn.close()

# Initialize tables when module is imported
init_log_table()
init_kod_mapping_table()

if __name__ == '__main__':
    print_table_column_types() 