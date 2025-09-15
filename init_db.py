from sqlalchemy import create_engine
from models import Base
import sqlite3

DB_URL = "sqlite:///newsletter.db"

def ensure_category_column():
    conn = sqlite3.connect("newsletter.db")
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(articles);")
    cols = [row[1] for row in cur.fetchall()]
    if "category" not in cols:
        cur.execute("ALTER TABLE articles ADD COLUMN category TEXT;")
        conn.commit()
        print("✅ Added missing 'category' column to articles")
    conn.close()

def main():
    engine = create_engine(DB_URL)
    Base.metadata.create_all(engine)  # ensure table exists
    ensure_category_column()
    print("newsletter.db schema ensured")

if __name__ == "__main__":
    main()
