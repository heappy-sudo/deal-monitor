import sqlite3
from typing import List, Optional
from models import Listing, SearchTask

DB_PATH = "deal_monitor.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            target_price REAL NOT NULL,
            tolerance_percent REAL NOT NULL,
            platforms TEXT NOT NULL,
            active INTEGER DEFAULT 1
        )
    ''')
    # Migrazione colonne statistiche (ignoriamo l'errore se esistono già)
    try:
        c.execute('ALTER TABLE searches ADD COLUMN run_count INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass
    try:
        c.execute('ALTER TABLE searches ADD COLUMN results_found INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass
    try:
        c.execute('ALTER TABLE searches ADD COLUMN check_interval INTEGER DEFAULT 5')
    except sqlite3.OperationalError:
        pass
    try:
        c.execute('ALTER TABLE searches ADD COLUMN last_checked TEXT')
    except sqlite3.OperationalError:
        pass

    c.execute('''
        CREATE TABLE IF NOT EXISTS seen_listings (
            id TEXT PRIMARY KEY,
            platform TEXT NOT NULL,
            seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_search(keyword: str, target_price: float, tolerance: float, platforms: str, check_interval: int = 5):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO searches (keyword, target_price, tolerance_percent, platforms, check_interval) VALUES (?, ?, ?, ?, ?)',
              (keyword, target_price, tolerance, platforms, check_interval))
    conn.commit()
    conn.close()

def get_active_searches() -> List[SearchTask]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Aggiungiamo tutte le colonne
    c.execute('SELECT id, keyword, target_price, tolerance_percent, platforms, active, COALESCE(run_count, 0), COALESCE(results_found, 0), COALESCE(check_interval, 5), last_checked FROM searches WHERE active=1')
    rows = c.fetchall()
    conn.close()
    
    return [SearchTask(
        id=r[0], keyword=r[1], target_price=r[2], tolerance_percent=r[3], 
        platforms=r[4], active=bool(r[5]), run_count=r[6], results_found=r[7],
        check_interval=r[8], last_checked=r[9]
    ) for r in rows]

def increment_search_stats(search_id: int, new_results: int, last_checked_str: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE searches SET run_count = COALESCE(run_count, 0) + 1, results_found = COALESCE(results_found, 0) + ?, last_checked = ? WHERE id=?', 
              (new_results, last_checked_str, search_id))
    conn.commit()
    conn.close()

def mark_listing_seen(listing_id: str, platform: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO seen_listings (id, platform) VALUES (?, ?)', (listing_id, platform))
        conn.commit()
    except sqlite3.IntegrityError:
        pass # Already seen
    conn.close()

def is_listing_seen(listing_id: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT 1 FROM seen_listings WHERE id=?', (listing_id,))
    seen = c.fetchone() is not None
    conn.close()
    return seen

def delete_search(search_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM searches WHERE id=?', (search_id,))
    conn.commit()
    conn.close()

def update_search(search_id: int, target_price: float, tolerance: float, platforms: str, check_interval: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE searches SET target_price=?, tolerance_percent=?, platforms=?, check_interval=? WHERE id=?', 
              (target_price, tolerance, platforms, check_interval, search_id))
    conn.commit()
    conn.close()
