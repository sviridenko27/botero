import os
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from .database import Base, SessionLocal, engine, get_db
from .models import Filling, Product, StoreInfo

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Кондитерская витрина")
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "change-me-for-production"),
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

SERIAL_CATEGORIES = {
    "cakes": "Торты",
    "pastries": "Пирожные",
}

CATALOG_CATEGORIES = {
    "wedding": "Свадебные",
    "birthday": "День рождения",
    "kids": "Детские",
}

DEFAULT_PRODUCTS = [
    {
        "name": "Карамельный бархат",
        "section": "serial",
        "category": "cakes",
        "description": "Нежный бисквит с соленой карамелью и кремом маскарпоне.",
        "price": 3100,
        "image_url": "https://images.unsplash.com/photo-1565958011703-44f9829ba187?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "name": "Ягодный мильфей",
        "section": "serial",
        "category": "pastries",
        "description": "Слоеное пирожное с кремом дипломат и свежей малиной.",
        "price": 360,
        "image_url": "https://images.unsplash.com/photo-1486427944299-d1955d23e34d?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "name": "Свадебный белый шифон",
        "section": "catalog",
        "category": "wedding",
        "description": "Трехъярусный торт с ванильным муссом и живыми цветами.",
        "price": 14500,
        "image_url": "https://images.unsplash.com/photo-1535254973040-607b474cb50d?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "name": "Шоколадный праздник",
        "section": "catalog",
        "category": "birthday",
        "description": "Плотный шоколадный бисквит и сливочный ганаш с декором.",
        "price": 6200,
        "image_url": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "name": "Радужный единорог",
        "section": "catalog",
        "category": "kids",
        "description": "Яркий детский торт с натуральными красителями и маршмеллоу.",
        "price": 5900,
        "image_url": "https://images.unsplash.com/photo-1558301211-0d8c8ddee6ec?auto=format&fit=crop&w=1200&q=80",
    },
]

DEFAULT_FILLINGS = [
    {
        "name": "Фисташка-малина",
        "description": "Фисташковый крем, малиновое конфи и тонкий бисквит.",
    },
    {
        "name": "Манго-маракуйя",
        "description": "Тропическая кислинка, воздушный мусс и ванильный корж.",
    },
    {
        "name": "Классический медовик",
        "description": "Медовые коржи и сметанный крем в легкой современной версии.",
    },
]


def ensure_store_info(db: Session) -> StoreInfo:
    store_info = db.scalar(select(StoreInfo).where(StoreInfo.id == 1))
    if store_info:
        return store_info

    store_info = StoreInfo(
        id=1,
        phone="+7 (900) 000-00-00",
        address="г. Москва, ул. Кондитерская, 12",
        delivery_text="Доставка по Москве и МО ежедневно с 10:00 до 22:00."
        " Экспресс-доставка в день заказа обсуждается отдельно.",
        payment_text="Оплата картой на сайте, переводом или наличными при самовывозе.",
    )
    db.add(store_info)
    db.commit()
    db.refresh(store_info)
    return store_info


def seed_demo_content(db: Session) -> None:
    has_products = db.scalar(select(Product.id).limit(1))
    if not has_products:
        for item in DEFAULT_PRODUCTS:
            db.add(Product(**item))

    has_fillings = db.scalar(select(Filling.id).limit(1))
    if not has_fillings:
        for item in DEFAULT_FILLINGS:
            db.add(Filling(**item))

    ensure_store_info(db)
    db.commit()


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_demo_content(db)


def admin_guard(request: Request) -> RedirectResponse | None:
    if request.session.get("is_admin"):
        return None
    return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)


@app.get("/")
def storefront(request: Request, db: Session = Depends(get_db)):
    products = db.scalars(select(Product).order_by(Product.created_at.desc())).all()
    fillings = db.scalars(select(Filling).order_by(Filling.created_at.desc())).all()
    store_info = ensure_store_info(db)

    serial_products = [item for item in products if item.section == "serial"]
    catalog_products = [item for item in products if item.section == "catalog"]

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "serial_products": serial_products,
            "catalog_products": catalog_products,
            "fillings": fillings,
            "store_info": store_info,
            "serial_categories": SERIAL_CATEGORIES,
            "catalog_categories": CATALOG_CATEGORIES,
        },
    )


@app.get("/api/products")
def list_products(db: Session = Depends(get_db)):
    items = db.scalars(select(Product).order_by(Product.created_at.desc())).all()
    return [
        {
            "id": item.id,
            "name": item.name,
            "section": item.section,
            "category": item.category,
            "description": item.description,
            "price": item.price,
            "image_url": item.image_url,
        }
        for item in items
    ]


@app.get("/api/fillings")
def list_fillings(db: Session = Depends(get_db)):
    items = db.scalars(select(Filling).order_by(Filling.created_at.desc())).all()
    return [{"id": item.id, "name": item.name, "description": item.description} for item in items]


@app.get("/admin/login")
def admin_login_page(request: Request):
    if request.session.get("is_admin"):
        return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        "admin_login.html",
        {
            "request": request,
            "error": request.query_params.get("error"),
        },
    )


@app.post("/admin/login")
def admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    expected_username = os.getenv("ADMIN_USERNAME", "owner")
    expected_password = os.getenv("ADMIN_PASSWORD", "owner123")

    if username != expected_username or password != expected_password:
        return RedirectResponse(
            url="/admin/login?error=1",
            status_code=status.HTTP_302_FOUND,
        )

    request.session["is_admin"] = True
    return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)


@app.post("/admin/logout")
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)


@app.get("/admin")
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    guard = admin_guard(request)
    if guard:
        return guard
    products = db.scalars(select(Product).order_by(Product.created_at.desc())).all()
    fillings = db.scalars(select(Filling).order_by(Filling.created_at.desc())).all()
    store_info = ensure_store_info(db)

    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "products": products,
            "fillings": fillings,
            "store_info": store_info,
            "serial_categories": SERIAL_CATEGORIES,
            "catalog_categories": CATALOG_CATEGORIES,
        },
    )


@app.post("/admin/products")
def add_product(
    request: Request,
    name: str = Form(...),
    section: str = Form(...),
    category: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    image_url: str = Form(...),
    db: Session = Depends(get_db),
):
    guard = admin_guard(request)
    if guard:
        return guard

    if section not in {"serial", "catalog"}:
        raise HTTPException(status_code=400, detail="Некорректный раздел")

    if section == "serial" and category not in SERIAL_CATEGORIES:
        raise HTTPException(status_code=400, detail="Некорректная категория")

    if section == "catalog" and category not in CATALOG_CATEGORIES:
        raise HTTPException(status_code=400, detail="Некорректная категория")

    db.add(
        Product(
            name=name,
            section=section,
            category=category,
            description=description,
            price=price,
            image_url=image_url,
        )
    )
    db.commit()
    return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)


@app.post("/admin/products/{product_id}/delete")
def delete_product(product_id: int, request: Request, db: Session = Depends(get_db)):
    guard = admin_guard(request)
    if guard:
        return guard
    item = db.scalar(select(Product).where(Product.id == product_id))
    if item:
        db.delete(item)
        db.commit()
    return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)


@app.post("/admin/fillings")
def add_filling(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    db: Session = Depends(get_db),
):
    guard = admin_guard(request)
    if guard:
        return guard

    exists = db.scalar(select(Filling).where(Filling.name == name))
    if not exists:
        db.add(Filling(name=name, description=description))
        db.commit()

    return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)


@app.post("/admin/fillings/{filling_id}/delete")
def delete_filling(filling_id: int, request: Request, db: Session = Depends(get_db)):
    guard = admin_guard(request)
    if guard:
        return guard
    item = db.scalar(select(Filling).where(Filling.id == filling_id))
    if item:
        db.delete(item)
        db.commit()
    return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)


@app.post("/admin/store-info")
def update_store_info(
    request: Request,
    phone: str = Form(...),
    address: str = Form(...),
    delivery_text: str = Form(...),
    payment_text: str = Form(...),
    db: Session = Depends(get_db),
):
    guard = admin_guard(request)
    if guard:
        return guard
    store_info = ensure_store_info(db)

    store_info.phone = phone
    store_info.address = address
    store_info.delivery_text = delivery_text
    store_info.payment_text = payment_text

    db.add(store_info)
    db.commit()

    return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
