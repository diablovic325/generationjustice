from pydantic import BaseModel, Field


class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=150, description="Назва книги")
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Короткий опис або анотація книги",
    )


class BookCreate(BookBase):
    pass


class Book(BookBase):
    id: int
    author_id: int

    class Config:
        from_attributes = True


class AuthorBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Ім'я автора")


class AuthorCreate(AuthorBase):
    pass


class Author(AuthorBase):
    id: int
    books: list[Book] = []

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    login: str = Field(..., min_length=3, max_length=50, description="Логін користувача")


class UserCreate(UserBase):
    password: str = Field(..., min_length=4, max_length=100, description="Пароль")


class LoginRequest(UserBase):
    password: str = Field(..., min_length=4, max_length=100, description="Пароль")


class User(UserBase):
    id: int
    rights: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class LibraryStats(BaseModel):
    total_authors: int = Field(description="Загальна кількість авторів")
    total_books: int = Field(description="Загальна кількість книг")
    top_author: str | None = Field(description="Автор із найбільшою кількістю книг")
    top_author_books: int = Field(description="Кількість книг у найактивнішого автора")


class AppInfo(BaseModel):
    message: str
    version: str
    features: list[str]
