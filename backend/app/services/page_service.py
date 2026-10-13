from sqlalchemy.orm import Session

from app.models.page import Page

from app.services.crawler import crawl

from app.services.chunk_service import save_page_chunk

#function to save the page data to the DB
def save_page(db: Session, analysis_id: int, page_data: dict):
    page = Page(
        analysis_id=analysis_id,
        url=page_data["url"],
        title=page_data["title"],
        description=page_data["description"],
        heading=str(page_data["headings"]),
        text=page_data["text"],
    )

    db.add(page)
    db.commit()
    db.refresh(page)

    return page

#function to store the page data one bby one and getting the data from crawl
def run_crawl_for_analysis(
    db: Session,
    analysis_id: int,
    start_url: str
):
    pages = crawl(start_url)
    page_count = 0

    for page_data in pages:
        page = save_page(
            db,
            analysis_id,
            page_data
        )
        page_count+=1

        save_page_chunk(
            db,
            page
        )


    return page_count