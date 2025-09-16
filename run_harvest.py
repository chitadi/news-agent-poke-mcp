from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from rss_scraper import fetch_rss
import yaml

def load_sources(path="sources.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def rss_sites(sources):
    return [s for s in sources if s.get("rss")]

def main():
    engine = create_engine("sqlite:///newsletter.db")
    Session = sessionmaker(bind=engine)
    session = Session()

    sources = load_sources("sources.yaml")
    for src in rss_sites(sources):
        print(f"Fetching RSS feed from {src['name']} …")
        try:
            fetch_rss(src, session)
        except Exception as e:
            print(f"Error on {src['name']}: {e}")
    
    session.close()
    print("Harvest complete")

if __name__ == "__main__":
    main()