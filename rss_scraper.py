import feedparser, hashlib, datetime, pytz
from sqlalchemy.orm import Session
from models import Article

UTC = pytz.utc
UA = {"User-Agent": "Mozilla/5.0"}

def fetch_rss(source: dict, db: Session, horizon_hours=12):
    cutoff = datetime.datetime.now(tz=UTC) - datetime.timedelta(hours=horizon_hours)
    feed = feedparser.parse(source["feed_url"])
    
    for entry in feed.entries:
        if not hasattr(entry, "published_parsed"):
            continue
        published = datetime.datetime(*entry.published_parsed[:6], tzinfo=pytz.utc)
        if published.tzinfo is None:  # some feeds omit tz
            published = published.replace(tzinfo=UTC)
        if published < cutoff:
            continue

        url = entry.link
        aid = hashlib.sha256(url.encode()).hexdigest()
        if db.query(Article).get(aid):
            continue

        db.add(Article(
            id=aid,
            source_name=source["name"],
            url=url,
            title=entry.title,
            published_at=published,
            fetched_at=datetime.datetime.utcnow()
        ))
    db.commit()
