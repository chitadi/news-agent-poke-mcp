import feedparser, hashlib, datetime, pytz
from sqlalchemy.orm import Session
from models import Article
import dateutil.parser

UTC = pytz.utc
UA = {"User-Agent": "Mozilla/5.0"}

def fetch_rss(source: dict, db: Session, horizon_hours=24):
    cutoff = datetime.datetime.now(tz=UTC) - datetime.timedelta(hours=horizon_hours)
    feed = feedparser.parse(source["feed_url"])
    
    for entry in feed.entries:
        # --- Published date handling ---
        published = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            # Normal case (RFC822 etc.)
            published = datetime.datetime(*entry.published_parsed[:6], tzinfo=pytz.utc)
        else:
            # Fallback to raw string
            raw_date = getattr(entry, "published", None) or entry.get("pubDate")
            if raw_date:
                try:
                    published = dateutil.parser.parse(raw_date)
                    if published.tzinfo is None:
                        published = published.replace(tzinfo=UTC)
                    print(f"⚠️ Fallback date parse for {source['name']}: {raw_date}")
                except Exception as e:
                    print(f"❌ Failed to parse date for {source['name']}: {raw_date} ({e})")
                    continue
            else:
                print(f"❌ No date found for entry in {source['name']}, skipping")
                continue

        if published < cutoff:
            continue

        # --- URL handling ---
        url = getattr(entry, "link", None)
        if not url:
            print(f"❌ No link found for entry in {source['name']}, skipping")
            continue

        aid = hashlib.sha256(url.encode()).hexdigest()
        if db.query(Article).get(aid):
            continue

        # --- Insert into DB ---
        db.add(Article(
            id=aid,
            source_name=source["name"],
            url=url,
            title=getattr(entry, "title", "(no title)"),
            published_at=published,
            fetched_at=datetime.datetime.utcnow()
        ))
    db.commit()

