from __future__ import annotations

import os
import secrets
import shutil
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db, init_db
from .models import ContentItem, NewsItem, SectionType

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

SECTION_META = {
    SectionType.aromas: {
        "name": "Ароматы",
        "description": "Коллекция нишевых и авторских парфюмов.",
    },
    SectionType.brands: {
        "name": "Бренды",
        "description": "Дома моды и независимые парфюмерные бренды.",
    },
    SectionType.care: {
        "name": "Уход",
        "description": "Продукты ухода за телом и ритуалы красоты.",
    },
}

app = FastAPI(title="Perfume Boutique")
security = HTTPBasic()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.mount("/uploads", StaticFiles(directory=str(BASE_DIR / "uploads")), name="uploads")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


def require_admin(credentials: HTTPBasicCredentials = Depends(security)) -> None:
    username_ok = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    password_ok = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (username_ok and password_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


def parse_section(section: str) -> SectionType:
    try:
        return SectionType(section)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Section not found") from exc


async def save_upload(file: UploadFile | None) -> str | None:
    if not file or not file.filename:
        return None
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are allowed")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        suffix = ".jpg"

    filename = f"{uuid.uuid4().hex}{suffix}"
    destination = UPLOAD_DIR / filename

    contents = await file.read()
    destination.write_bytes(contents)
    return f"/uploads/{filename}"


def remove_upload(path: str | None) -> None:
    if not path:
        return
    filename = Path(path).name
    candidate = UPLOAD_DIR / filename
    if candidate.exists():
        candidate.unlink()


def duplicate_upload(path: str | None) -> str | None:
    if not path:
        return None
    source = UPLOAD_DIR / Path(path).name
    if not source.exists() or not source.is_file():
        return None

    suffix = source.suffix.lower() or ".jpg"
    duplicate_name = f"{uuid.uuid4().hex}{suffix}"
    destination = UPLOAD_DIR / duplicate_name
    shutil.copy2(source, destination)
    return f"/uploads/{duplicate_name}"


def get_news_items(db: Session) -> list[NewsItem]:
    return db.scalars(select(NewsItem).order_by(NewsItem.updated_at.desc(), NewsItem.id.desc())).all()


@app.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    news_items = get_news_items(db)
    aroma_items = db.scalars(
        select(ContentItem)
        .where(ContentItem.section == SectionType.aromas)
        .order_by(ContentItem.updated_at.desc(), ContentItem.id.desc())
    ).all()
    brand_items = db.scalars(
        select(ContentItem)
        .where(ContentItem.section == SectionType.brands)
        .order_by(ContentItem.updated_at.desc(), ContentItem.id.desc())
    ).all()
    care_items = db.scalars(
        select(ContentItem)
        .where(ContentItem.section == SectionType.care)
        .order_by(ContentItem.updated_at.desc(), ContentItem.id.desc())
    ).all()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "sections": SECTION_META,
            "news_items": news_items,
            "aroma_items": aroma_items,
            "brand_items": brand_items,
            "care_items": care_items,
        },
    )


@app.get("/section/{section_slug}")
def section_page(section_slug: str, request: Request, db: Session = Depends(get_db)):
    section = parse_section(section_slug)
    news_items = get_news_items(db)
    items = db.scalars(
        select(ContentItem)
        .where(ContentItem.section == section)
        .order_by(ContentItem.updated_at.desc(), ContentItem.id.desc())
    ).all()
    return templates.TemplateResponse(
        request=request,
        name="section.html",
        context={
            "section": section,
            "section_data": SECTION_META[section],
            "items": items,
            "sections": SECTION_META,
            "news_items": news_items,
        },
    )


@app.get("/item/{item_id}")
def item_page(item_id: int, request: Request, db: Session = Depends(get_db)):
    item = db.get(ContentItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    section_data = SECTION_META[item.section]
    return templates.TemplateResponse(
        request=request,
        name="item_detail.html",
        context={
            "item": item,
            "section_data": section_data,
            "section_slug": item.section.value,
            "sections": SECTION_META,
        },
    )


@app.get("/admin")
def admin_panel(
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    items = db.scalars(select(ContentItem).order_by(ContentItem.id.desc())).all()
    news_items = get_news_items(db)
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={"items": items, "sections": SECTION_META, "news_items": news_items},
    )


@app.post("/admin/items")
async def create_item(
    title: str = Form(...),
    description: str = Form(...),
    section: str = Form(...),
    image: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    section_type = parse_section(section)
    image_path = await save_upload(image)

    item = ContentItem(
        title=title.strip(),
        description=description.strip(),
        section=section_type,
        image_path=image_path,
    )
    db.add(item)
    db.commit()

    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/admin/items/{item_id}/update")
async def update_item(
    item_id: int,
    title: str = Form(...),
    description: str = Form(...),
    section: str = Form(...),
    image: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    item = db.get(ContentItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item.title = title.strip()
    item.description = description.strip()
    item.section = parse_section(section)

    new_image = await save_upload(image)
    if new_image:
        remove_upload(item.image_path)
        item.image_path = new_image

    db.add(item)
    db.commit()

    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/admin/items/{item_id}/delete")
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    item = db.get(ContentItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    remove_upload(item.image_path)
    db.delete(item)
    db.commit()

    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/admin/items/{item_id}/duplicate")
def duplicate_item(
    item_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    item = db.get(ContentItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    duplicated_item = ContentItem(
        title=item.title,
        description=item.description,
        section=item.section,
        image_path=duplicate_upload(item.image_path),
    )
    db.add(duplicated_item)
    db.commit()

    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/admin/news")
async def create_news(
    title: str = Form(...),
    description: str = Form(...),
    image: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    image_path = await save_upload(image)
    news_item = NewsItem(
        title=title.strip(),
        description=description.strip(),
        image_path=image_path,
    )
    db.add(news_item)
    db.commit()

    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/admin/news/{news_id}/update")
async def update_news(
    news_id: int,
    title: str = Form(...),
    description: str = Form(...),
    image: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    news_item = db.get(NewsItem, news_id)
    if not news_item:
        raise HTTPException(status_code=404, detail="News item not found")

    news_item.title = title.strip()
    news_item.description = description.strip()

    new_image = await save_upload(image)
    if new_image:
        remove_upload(news_item.image_path)
        news_item.image_path = new_image

    db.add(news_item)
    db.commit()

    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/admin/news/{news_id}/delete")
def delete_news(
    news_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    news_item = db.get(NewsItem, news_id)
    if not news_item:
        raise HTTPException(status_code=404, detail="News item not found")

    remove_upload(news_item.image_path)
    db.delete(news_item)
    db.commit()

    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/admin/news/{news_id}/duplicate")
def duplicate_news(
    news_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    news_item = db.get(NewsItem, news_id)
    if not news_item:
        raise HTTPException(status_code=404, detail="News item not found")

    duplicated_news = NewsItem(
        title=news_item.title,
        description=news_item.description,
        image_path=duplicate_upload(news_item.image_path),
    )
    db.add(duplicated_news)
    db.commit()

    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
