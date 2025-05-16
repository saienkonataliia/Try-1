import sqlite3

PIXELS_PER_METER = 100

# --- Ініціалізація ---
def init_db():
    conn = sqlite3.connect("interior.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            width INTEGER NOT NULL,
            height INTEGER NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS furniture (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER,
            name TEXT NOT NULL,
            width INTEGER,
            height INTEGER,
            x INTEGER,
            y INTEGER,
            angle INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

# --- Операції з кімнатами ---
def add_room(name, width, height):
    with sqlite3.connect("interior.db") as conn:
        conn.execute("INSERT INTO rooms (name, width, height) VALUES (?, ?, ?)", (name, width, height))

def get_rooms():
    with sqlite3.connect("interior.db") as conn:
        return conn.execute("SELECT * FROM rooms").fetchall()

def get_room_by_id(room_id):
    with sqlite3.connect("interior.db") as conn:
        return conn.execute("SELECT * FROM rooms WHERE id = ?", (room_id,)).fetchone()

def delete_room(room_id):
    with sqlite3.connect("interior.db") as conn:
        conn.execute("DELETE FROM furniture WHERE room_id = ?", (room_id,))
        conn.execute("DELETE FROM rooms WHERE id = ?", (room_id,))

def update_room(room_id, width, height):
    with sqlite3.connect("interior.db") as conn:
        conn.execute("UPDATE rooms SET width = ?, height = ? WHERE id = ?", (width, height, room_id))

# --- Операції з меблями ---
def add_furniture(room_id, name, width, height, x, y, angle=0):
    with sqlite3.connect("interior.db") as conn:
        conn.execute("""
            INSERT INTO furniture (room_id, name, width, height, x, y, angle)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (room_id, name, width, height, x, y, angle))

def get_furniture_by_room(room_id):
    with sqlite3.connect("interior.db") as conn:
        return conn.execute("SELECT * FROM furniture WHERE room_id = ?", (room_id,)).fetchall()

def update_furniture_position(furniture_id, x, y):
    with sqlite3.connect("interior.db") as conn:
        conn.execute("UPDATE furniture SET x = ?, y = ? WHERE id = ?", (x, y, furniture_id))

def update_furniture(furniture_id, name, width, height):
    with sqlite3.connect("interior.db") as conn:
        conn.execute("UPDATE furniture SET name = ?, width = ?, height = ? WHERE id = ?",
                     (name, width, height, furniture_id))

def update_furniture_angle(furniture_id, angle):
    with sqlite3.connect("interior.db") as conn:
        conn.execute("UPDATE furniture SET angle = ? WHERE id = ?", (angle, furniture_id))

def delete_furniture(furniture_id):
    with sqlite3.connect("interior.db") as conn:
        conn.execute("DELETE FROM furniture WHERE id = ?", (furniture_id,))
