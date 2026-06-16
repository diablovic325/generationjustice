from sqlalchemy import create_engine  # Імпортуємо функцію для створення підключення до бази даних
from sqlalchemy.ext.declarative import declarative_base  # Імпортуємо базовий клас для створення
# моделей (таблиць)
from sqlalchemy.orm import sessionmaker  # Імпортуємо фабрику для створення сесій роботи з БД

SQLALCHEMY_DATABASE_URL = "sqlite:///./library.db"  # Рядок підключення до SQLite бази даних
# (файл library.db у поточній папці)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,  # Передаємо адресу бази даних
    connect_args={"check_same_thread": False}  # Дозволяє використовувати БД у кількох потоках
    # (важливо для FastAPI)
)

SessionLocal = sessionmaker(
    autocommit=False,  # Вимикаємо автоматичне збереження змін (потрібно викликати commit вручну)
    autoflush=False,  # Вимикаємо автоматичну відправку змін у БД перед запитами
    bind=engine  # Прив’язуємо сесію до створеного engine (підключення до БД)
)

Base = declarative_base()  # Створюємо базовий клас, від якого будуть наслідуватись усі моделі (таблиці)