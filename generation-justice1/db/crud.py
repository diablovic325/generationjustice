import hashlib
import secrets
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from . import models, schemas


def get_author(db: Session, author_id: int):
    return db.query(models.Author).filter(models.Author.id == author_id).first()


def get_author_by_name(db: Session, name: str):
    return db.query(models.Author).filter(models.Author.name == name).first()


def get_authors(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Author).offset(skip).limit(limit).all()


def create_author(db: Session, author: schemas.AuthorCreate):
    db_author = models.Author(name=author.name)
    db.add(db_author)
    db.commit()
    db.refresh(db_author)
    return db_author


def update_author(db: Session, author_id: int, author: schemas.AuthorCreate):
    db_author = get_author(db, author_id)
    if not db_author:
        return None

    db_author.name = author.name
    db.commit()
    db.refresh(db_author)
    return db_author


def delete_author(db: Session, author_id: int):
    db_author = get_author(db, author_id)
    if not db_author:
        return None

    db.delete(db_author)
    db.commit()
    return db_author


def get_book(db: Session, book_id: int):
    return db.query(models.Book).filter(models.Book.id == book_id).first()


def get_books(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Book).offset(skip).limit(limit).all()


def search_books(db: Session, query: str):
    pattern = f"%{query}%"
    return (
        db.query(models.Book)
        .filter(
            or_(
                models.Book.title.ilike(pattern),
                models.Book.description.ilike(pattern),
            )
        )
        .all()
    )


def create_author_book(db: Session, book: schemas.BookCreate, author_id: int):
    db_book = models.Book(**book.model_dump(), author_id=author_id)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


def update_book(db: Session, book_id: int, book: schemas.BookCreate):
    db_book = get_book(db, book_id)
    if not db_book:
        return None

    db_book.title = book.title
    db_book.description = book.description
    db.commit()
    db.refresh(db_book)
    return db_book


def delete_book(db: Session, book_id: int):
    db_book = get_book(db, book_id)
    if not db_book:
        return None

    db.delete(db_book)
    db.commit()
    return db_book


def get_random_book(db: Session):
    return db.query(models.Book).order_by(func.random()).first()


def get_library_stats(db: Session):
    total_authors = db.query(func.count(models.Author.id)).scalar() or 0
    total_books = db.query(func.count(models.Book.id)).scalar() or 0
    top_author_row = (
        db.query(models.Author.name, func.count(models.Book.id).label("books_count"))
        .outerjoin(models.Book)
        .group_by(models.Author.id)
        .order_by(func.count(models.Book.id).desc(), models.Author.name.asc())
        .first()
    )

    return {
        "total_authors": total_authors,
        "total_books": total_books,
        "top_author": top_author_row[0] if top_author_row else None,
        "top_author_books": top_author_row[1] if top_author_row else 0,
    }


def get_password_hash(password: str):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str):
    return get_password_hash(plain_password) == hashed_password


def get_user(db: Session, login: str):
    return db.query(models.User).filter(models.User.login == login).first()


def create_user(db: Session, login: str, password: str, rights: str = "user"):
    salt = secrets.token_hex(16)
    hashed_password = get_password_hash(password + salt)
    db_user = models.User(login=login, password=hashed_password, salt=salt, rights=rights)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, login: str, password: str):
    user = get_user(db, login)
    if not user:
        return None
    if not verify_password(password + user.salt, user.password):
        return None
    return user
