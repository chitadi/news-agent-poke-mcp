from sqlalchemy import create_engine
from models import Base

DB_URL = "sqlite:///newsletter.db"

def main():
    engine = create_engine(DB_URL)
    Base.metadata.create_all(engine)
    print("newsletter.db schema ensured")

if __name__ == "__main__":
    main()