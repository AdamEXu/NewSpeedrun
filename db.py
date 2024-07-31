import sqlite3

def init_db():
    con = sqlite3.connect("main.db")
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, username TEXT, discriminator TEXT, avatar TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS runs (id INTEGER PRIMARY KEY AUTOINCREMENT,user_id TEXT,time REAL,video_url TEXT,game TEXT);")
    con.commit()
    con.close()

def get_db():
    con = sqlite3.connect("main.db")
    return con
