from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import datetime, timezone
import logging

from app.models.institution import Institution
from app.models.monitored_source import MonitoredSource
from app.models.notice import Notice
from app.models.crawler_run import CrawlerRun
from app.crawler.utils import normalize_title, normalize_url, generate_fingerprint
from app.crawler.spiders.test_spider import TestSpider

logger = logging.getLogger(__name__)

def get_spider_for_source(source: MonitoredSource):
    """
    Returns the appropriate spider instance for a given source.
    For MVP, we just use TestSpider.
    """
    return TestSpider(source_url=source.url)

def run_crawler(db: Session):
    """
    Main engine to run crawlers for all active sources of active institutions.
    """
    active_sources = db.query(MonitoredSource).join(Institution).filter(
        MonitoredSource.is_active == True,
        Institution.is_active == True
    ).all()
    
    logger.info(f"Found {len(active_sources)} active sources to crawl.")
    
    for source in active_sources:
        logger.info(f"Starting crawl for source ID {source.id} ({source.name})")
        
        # 1. Create CrawlerRun in 'running' state
        run_record = CrawlerRun(
            source_id=source.id,
            status="running",
            started_at=datetime.now(timezone.utc),
            items_found=0,
            new_items=0
        )
        db.add(run_record)
        db.commit()
        db.refresh(run_record)
        
        # 2. Get the spider
        spider = get_spider_for_source(source)
        
        try:
            # 3. Extract items
            raw_items = spider.run()
            run_record.items_found = len(raw_items)
            
            new_items_count = 0
            
            # 4. Process and normalize items
            for item in raw_items:
                title = item.get("title", "")
                url = item.get("url", "")
                
                norm_title = normalize_title(title)
                norm_url = normalize_url(url, source.url)
                
                if not norm_title or not norm_url:
                    continue
                
                fingerprint = generate_fingerprint(source.institution_id, norm_title, norm_url)
                
                # Check for duplicate
                existing_notice = db.query(Notice).filter(Notice.fingerprint == fingerprint).first()
                if not existing_notice:
                    # Save new notice
                    new_notice = Notice(
                        institution_id=source.institution_id,
                        source_id=source.id,
                        title=title.strip(),
                        normalized_title=norm_title,
                        url=url.strip(),
                        normalized_url=norm_url,
                        notice_type=item.get("notice_type", "edital"),
                        fingerprint=fingerprint,
                        is_active=True,
                        detected_at=datetime.now(timezone.utc)
                    )
                    # Handle optional fields if they were extracted securely
                    # e.g., pub_date = item.get("publication_date")
                    
                    db.add(new_notice)
                    new_items_count += 1
            
            # Commit the new notices
            db.commit()
            
            # 5. Update success states
            run_record.new_items = new_items_count
            run_record.status = "completed"
            run_record.finished_at = datetime.now(timezone.utc)
            
            source.last_checked_at = datetime.now(timezone.utc)
            source.last_success_at = datetime.now(timezone.utc)
            
            db.commit()
            logger.info(f"Successfully crawled source ID {source.id}. Found: {run_record.items_found}, New: {run_record.new_items}")
            
        except Exception as e:
            logger.error(f"Error crawling source ID {source.id}: {str(e)}")
            db.rollback()
            
            # Update failure states
            run_record.status = "failed"
            run_record.error_message = str(e)
            run_record.finished_at = datetime.now(timezone.utc)
            
            source.last_checked_at = datetime.now(timezone.utc)
            source.last_error_message = str(e)
            
            db.commit()
