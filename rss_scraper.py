import feedparser, hashlib, datetime, pytz, re
from sqlalchemy.orm import Session
from models import Article
import dateutil.parser

UTC = pytz.utc
UA = {"User-Agent": "Mozilla/5.0"}

# --- Main Categories ---
CATEGORIES = {
    "tech": [
        "tech", "technology", "ai", "artificial intelligence", "software", "hardware",
        "digital", "cyber", "cloud", "automation", "app", "mobile", "internet",
        "data", "blockchain", "crypto", "cryptocurrency", "robotics", "gadget"
    ],
    "startups": [
        "startup", "startups", "founder", "entrepreneur", "venture",
        "incubator", "accelerator", "scaleup", "seed round", "series a",
        "series b", "series c", "unicorn"
    ],
    "business": [
        "business", "corporate", "company", "industry", "trade", "merger", "acquisition",
        "revenue", "profit", "loss", "ipo", "market share", "partnership", "strategy",
        "growth", "expansion", "operations", "manufacturing", "supply chain"
    ],
    "politics": [
        "politics", "political", "government", "election", "minister", "policy", "parliament",
        "law", "legal", "bill", "congress", "party", "bjp", "opposition", "democracy",
        "constitution", "ruling", "supreme court", "judiciary"
    ],
    "finance": [
        "finance", "financial", "economy", "economic", "market", "stock", "shares",
        "investment", "investor", "bank", "banking", "funding", "valuation",
        "mutual fund", "equity", "bond", "currency", "exchange rate", "inflation",
        "interest rate"
    ],
    "miscellaneous": [
        # Everything else (catch-all world/general/society)
        "world", "international", "global", "news", "society", "culture", "education",
        "sports", "entertainment", "climate", "environment", "weather", "disaster",
        "community", "lifestyle", "wellness", "health", "science", "space"
    ]
}

def should_categorize(source_category: str) -> bool:
    """
    Decide whether to categorize based on source-provided category.
    """
    if not source_category:
        return True
    
    sc = source_category.lower().strip()

    # If multiple categories, need categorization
    if "," in sc:
        return True
    
    # If it's already one of our 6 main buckets
    if sc in ["tech", "startups", "business", "politics", "finance"]:
        return False
    
    # If vague
    if sc in ["misc", "general", "mixed", "various"]:
        return True
    
    # Otherwise, categorize
    return True

def get_direct_category(source_category: str) -> str:
    """
    Map source category directly to one of our 6 categories.
    """
    if not source_category:
        return "miscellaneous"
    
    sc = source_category.lower().strip()
    if sc in ["tech", "startups", "business", "politics", "finance", "miscellaneous"]:
        return sc
    return "miscellaneous"

def categorize_article(title: str, description: str = "", source_category: str = "") -> str:
    """
    Keyword-based categorization → returns one of 6 categories.
    """
    text = f"{title} {description} {source_category}".lower()
    scores = {}
    
    for category, keywords in CATEGORIES.items():
        score = 0
        for kw in keywords:
            score += text.count(kw.lower())
        scores[category] = score
    
    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best
    return "miscellaneous"

def fetch_rss(source: dict, db: Session, horizon_hours=24):
    cutoff = datetime.datetime.now(tz=UTC) - datetime.timedelta(hours=horizon_hours)
    feed = feedparser.parse(source["feed_url"])
    
    for entry in feed.entries:
        # --- Published date ---
        published = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published = datetime.datetime(*entry.published_parsed[:6], tzinfo=UTC)
        else:
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
        
        # --- URL ---
        url = getattr(entry, "link", None)
        if not url:
            print(f"❌ No link found for entry in {source['name']}, skipping")
            continue
        
        aid = hashlib.sha256(url.encode()).hexdigest()
        if db.query(Article).get(aid):
            continue
        
        # --- Categorization ---
        title = getattr(entry, "title", "(no title)")
        source_category = source.get("category", "")
        
        if should_categorize(source_category):
            description = getattr(entry, "description", "") or getattr(entry, "summary", "")
            article_category = categorize_article(title, description, source_category)
            print(f"📰 {source['name']}: '{title[:50]}...' → {article_category} (categorized)")
        else:
            article_category = get_direct_category(source_category)
            print(f"📰 {source['name']}: '{title[:50]}...' → {article_category} (direct from source)")
        
        # --- Insert into DB ---
        db.add(Article(
            id=aid,
            source_name=source["name"],
            url=url,
            title=title,
            category=article_category,
            published_at=published,
            fetched_at=datetime.datetime.utcnow()
        ))
    
    db.commit()