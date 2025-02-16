import sqlite3
conn = sqlite3.connect('araminator.db')

cur = conn.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS guild(id INTEGER PRIMARY KEY)')


res = cur.execute("SELECT * FROM guild")

