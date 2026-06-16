from datetime import datetime
from html import escape
import os
from pathlib import Path
import hashlib
import secrets
import sqlite3

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("DATABASE_PATH", str(BASE_DIR / "generation_justice.db"))).expanduser()
SESSION_COOKIE = "gj_session"
TEMPLATES_DIR = BASE_DIR / "templates"
MEMBERSHIP_LEVELS = {"Ambassador", "Active Ambassador", "Senior Ambassador", "Country Lead"}
MODERATOR_LEVELS = {"Senior Ambassador", "Country Lead", "Organizer", "Admin"}
ADMIN_LEVELS = {"Admin"}
DONATION_FREQUENCIES = ("one_time", "monthly", "annual")
DONATION_TIERS = {
    "bronze": {"label": "Bronze", "amount": 25},
    "silver": {"label": "Silver", "amount": 50},
    "gold": {"label": "Gold", "amount": 100},
    "platinum": {"label": "Platinum", "amount": 250},
}

app = FastAPI(
    title="Generation Justice",
    description="Membership hub with applications, certificates, discussions, courses, publications, internships, and broadcasts.",
    version="3.0.0",
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


class LoginPayload(BaseModel):
    email: str
    password: str


class ApplicationPayload(BaseModel):
    name: str
    address: str
    city: str = ""
    country: str
    email: str
    phone: str
    organization: str = ""
    password: str
    membership: str = "Ambassador"
    interests: str = ""


class CommentPayload(BaseModel):
    name: str = ""
    text: str


class BroadcastPayload(BaseModel):
    title: str
    target: str
    message: str


class TopicPayload(BaseModel):
    title: str
    body: str


class ReplyPayload(BaseModel):
    topic_id: int
    body: str


class EssayPayload(BaseModel):
    title: str
    country: str
    summary: str


class ArticlePayload(BaseModel):
    title: str
    category: str
    abstract: str


class InternshipPayload(BaseModel):
    project_id: int
    motivation: str


class DonationPreviewPayload(BaseModel):
    frequency: str = "one_time"
    tier: str = "silver"
    amount: int = 50


def connect_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def now_label() -> str:
    return datetime.now().strftime("%b %d, %Y at %H:%M")


def clean(value: str, limit: int = 500) -> str:
    return value.strip()[:limit]


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    return dict(row) if row else None


def read_template(name: str) -> str:
    return (TEMPLATES_DIR / name).read_text(encoding="utf-8")


def can_moderate_comments(user: dict | None) -> bool:
    return bool(user and user.get("membership") in MODERATOR_LEVELS)


def is_admin(user: dict | None) -> bool:
    return bool(user and user.get("membership") in ADMIN_LEVELS)


def ensure_column(connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = [row["name"] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in columns:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def generate_registration_number(user_id: int) -> str:
    return f"GJ-{datetime.now().year}-{user_id:05d}"


def init_db() -> None:
    connection = connect_db()
    try:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                membership TEXT NOT NULL,
                joined_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS broadcasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                target TEXT NOT NULL,
                message TEXT NOT NULL,
                created_by TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS discussion_topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS discussion_replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER NOT NULL,
                body TEXT NOT NULL,
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(topic_id) REFERENCES discussion_topics(id)
            );

            CREATE TABLE IF NOT EXISTS competition_winners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month TEXT NOT NULL,
                winner_name TEXT NOT NULL,
                country TEXT NOT NULL,
                essay_title TEXT NOT NULL,
                summary TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS essay_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                country TEXT NOT NULL,
                summary TEXT NOT NULL,
                submitted_at TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS live_lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                lesson_date TEXT NOT NULL,
                host TEXT NOT NULL,
                platform TEXT NOT NULL,
                link TEXT NOT NULL,
                summary TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS internship_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                country TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                coordinator TEXT NOT NULL,
                spots TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS internship_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                project_id INTEGER NOT NULL,
                motivation TEXT NOT NULL,
                submitted_at TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(project_id) REFERENCES internship_projects(id)
            );

            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                duration TEXT NOT NULL,
                summary TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS article_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                abstract TEXT NOT NULL,
                submitted_at TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS magazines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                link TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                year TEXT NOT NULL,
                summary TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS panels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month TEXT NOT NULL,
                title TEXT NOT NULL,
                panel_date TEXT NOT NULL,
                speakers TEXT NOT NULL,
                link TEXT NOT NULL,
                summary TEXT NOT NULL
            );
            """
        )

        for column, definition in {
            "address": "TEXT DEFAULT ''",
            "city": "TEXT DEFAULT ''",
            "country": "TEXT DEFAULT ''",
            "phone": "TEXT DEFAULT ''",
            "organization": "TEXT DEFAULT ''",
            "interests": "TEXT DEFAULT ''",
            "registration_number": "TEXT DEFAULT ''",
            "status": "TEXT DEFAULT 'approved'",
        }.items():
            ensure_column(connection, "users", column, definition)

        seed_data(connection)
        connection.commit()
    finally:
        connection.close()


def table_is_empty(connection: sqlite3.Connection, table: str) -> bool:
    return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


def seed_data(connection: sqlite3.Connection) -> None:
    connection.execute(
        "UPDATE users SET membership = 'Ambassador' WHERE membership IN ('Starter', 'Member')"
    )
    connection.execute(
        "UPDATE users SET membership = 'Country Lead' WHERE membership = 'Organizer'"
    )

    if table_is_empty(connection, "users"):
        connection.execute(
            """
            INSERT INTO users
                (name, email, password_hash, membership, joined_at, address, city, country, phone, organization, interests, registration_number, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Demo Student",
                "demo@generationjustice.org",
                hash_password("demo123"),
                "Ambassador",
                now_label(),
                "1 Rule of Law Street",
                "London",
                "United Kingdom",
                "+44 0000 000000",
                "Generation Justice Demo",
                "Legal writing, panel discussions, internships",
                "GJ-2026-00001",
                "approved",
            ),
        )

    organizer = connection.execute(
        "SELECT id FROM users WHERE email = ?",
        ("organizer@generationjustice.org",),
    ).fetchone()
    if not organizer:
        connection.execute(
            """
            INSERT INTO users
                (name, email, password_hash, membership, joined_at, address, city, country, phone, organization, interests, registration_number, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Project Organizer",
                "organizer@generationjustice.org",
                hash_password("organizer123"),
                "Country Lead",
                now_label(),
                "1 Rule of Law Street",
                "London",
                "United Kingdom",
                "+44 0000 000001",
                "Generation Justice",
                "Moderation, country leadership, member support",
                "GJ-2026-00002",
                "approved",
            ),
        )

    admin = connection.execute(
        "SELECT id FROM users WHERE email = ?",
        ("admin@generationjustice.org",),
    ).fetchone()
    if not admin:
        connection.execute(
            """
            INSERT INTO users
                (name, email, password_hash, membership, joined_at, address, city, country, phone, organization, interests, registration_number, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Main Administrator",
                "admin@generationjustice.org",
                hash_password("admin123"),
                "Admin",
                now_label(),
                "1 Rule of Law Street",
                "London",
                "United Kingdom",
                "+44 0000 000002",
                "Generation Justice",
                "Project administration, organizer supervision, site moderation",
                "GJ-2026-00003",
                "approved",
            ),
        )

    for user in connection.execute("SELECT id FROM users WHERE registration_number = '' OR registration_number IS NULL"):
        connection.execute(
            "UPDATE users SET registration_number = ? WHERE id = ?",
            (generate_registration_number(user["id"]), user["id"]),
        )

    if table_is_empty(connection, "comments"):
        connection.executemany(
            "INSERT INTO comments (user_name, text, created_at) VALUES (?, ?, ?)",
            [
                ("Alex Rivera", "The leadership workshop helped me feel ready to speak during our school assembly.", "Apr 20, 2026 at 16:10"),
                ("Priya Shah", "I want to organize a student panel about safety, belonging, and mental health.", "Apr 21, 2026 at 11:35"),
                ("Marcus Lee", "The broadcast center makes it easier for our club to share campaign updates.", "Apr 22, 2026 at 09:20"),
            ],
        )

    if table_is_empty(connection, "broadcasts"):
        connection.execute(
            """
            INSERT INTO broadcasts (title, target, message, created_by, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "Welcome Members",
                "All pages",
                "Join this week's student action meeting and bring one idea for a new Rule of Law campaign.",
                "Demo Student",
                "running",
                "Apr 23, 2026 at 13:00",
            ),
        )

    if table_is_empty(connection, "discussion_topics"):
        connection.executemany(
            "INSERT INTO discussion_topics (title, body, created_by, created_at) VALUES (?, ?, ?, ?)",
            [
                (
                    "What does the Rule of Law mean for students?",
                    "Share examples from your school, university, city, or country. Long comments and detailed replies are welcome.",
                    "Demo Student",
                    "Apr 24, 2026 at 10:00",
                ),
                (
                    "How can legal writing become easier to understand?",
                    "Discuss methods for clearer legal communication, better structure, and publication-ready articles.",
                    "Generation Justice Team",
                    "Apr 25, 2026 at 12:30",
                ),
            ],
        )

    if table_is_empty(connection, "discussion_replies"):
        connection.executemany(
            "INSERT INTO discussion_replies (topic_id, body, created_by, created_at) VALUES (?, ?, ?, ?)",
            [
                (1, "For me it starts with fair procedures that every person can understand, not only lawyers.", "Demo Student", "Apr 24, 2026 at 10:45"),
                (2, "A useful legal text should explain the problem, the rule, and the real-world effect in plain language.", "Priya Shah", "Apr 25, 2026 at 13:05"),
            ],
        )

    if table_is_empty(connection, "competition_winners"):
        connection.executemany(
            "INSERT INTO competition_winners (month, winner_name, country, essay_title, summary) VALUES (?, ?, ?, ?, ?)",
            [
                ("May 2026", "Sofia Marin", "Romania", "Why Independent Courts Matter", "A clear essay connecting court independence to everyday public trust."),
                ("April 2026", "Daniel Brooks", "United Kingdom", "Youth Voices and Justice", "A strong argument for student participation in Rule of Law education."),
                ("March 2026", "Amina Hassan", "Kenya", "Access to Justice in Local Communities", "A practical essay about legal information, language, and community support."),
            ],
        )

    if table_is_empty(connection, "live_lessons"):
        connection.executemany(
            "INSERT INTO live_lessons (title, lesson_date, host, platform, link, summary) VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("Legal Communication Skills", "June 05, 2026 - 17:00 London time", "British Legal Centre", "Zoom", "https://zoom.us/", "A live class on structure, clarity, and persuasion in legal communication."),
                ("Writing Legal Articles for Publication", "June 12, 2026 - 17:00 London time", "Generation Justice Editorial Team", "YouTube Live", "https://www.youtube.com/", "A practical lesson on article planning, citations, and editorial standards."),
                ("Rule of Law Around the World", "June 19, 2026 - 17:00 London time", "Guest Panel", "Zoom", "https://zoom.us/", "A comparative lesson on challenges to the Rule of Law in different regions."),
            ],
        )

    if table_is_empty(connection, "internship_projects"):
        connection.executemany(
            "INSERT INTO internship_projects (country, title, description, coordinator, spots) VALUES (?, ?, ?, ?, ?)",
            [
                ("Ukraine", "Youth Rule of Law Media Project", "Students prepare short explainers and interviews about legal rights and civic responsibility.", "Olena K.", "8 places"),
                ("Poland", "Community Legal Writing Project", "Volunteers create accessible legal articles for students and local communities.", "Marta S.", "6 places"),
                ("United Kingdom", "Rule of Law Debate Series", "Interns help organize student debates, panel questions, and publication summaries.", "James R.", "5 places"),
                ("Georgia", "Access to Justice Student Network", "Participants map local Rule of Law challenges and propose student-led responses.", "Nino T.", "7 places"),
            ],
        )

    if table_is_empty(connection, "courses"):
        connection.executemany(
            "INSERT INTO courses (title, category, duration, summary) VALUES (?, ?, ?, ?)",
            [
                ("Legal Communication Skills", "Free Course", "4 modules", "A tailored course for members covering clarity, structure, audience, and oral presentation."),
                ("Legal Writing and Publication", "Free Course", "5 modules", "Training on legal article writing, editing, references, and publication standards."),
                ("Rule of Law Project Design", "Free Course", "3 modules", "A practical guide to designing student projects with goals, partners, and measurable outcomes."),
            ],
        )

    if table_is_empty(connection, "magazines"):
        connection.executemany(
            "INSERT INTO magazines (month, title, summary, link) VALUES (?, ?, ?, ?)",
            [
                ("May 2026", "Generation Justice Monthly: Courts and Trust", "Rule of Law news and member articles about public trust in justice systems.", "#"),
                ("April 2026", "Generation Justice Monthly: Youth and Legal Change", "Student writing, interviews, and project updates from members.", "#"),
            ],
        )

    if table_is_empty(connection, "books"):
        connection.executemany(
            "INSERT INTO books (title, year, summary) VALUES (?, ?, ?)",
            [
                ("Student Essays on the Rule of Law", "2026", "A compilation book featuring the best accredited essays from members."),
                ("Legal Communication for Young Lawyers", "2026", "A British Legal Centre publication built around accessible legal writing and publication skills."),
            ],
        )

    if table_is_empty(connection, "panels"):
        connection.executemany(
            "INSERT INTO panels (month, title, panel_date, speakers, link, summary) VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("June 2026", "Challenges to the Rule of Law in Times of Crisis", "June 28, 2026", "Judges, academics, student moderators", "https://zoom.us/", "A monthly expert discussion about institutions, rights, and public accountability."),
                ("July 2026", "Legal Education and Civic Responsibility", "July 26, 2026", "Legal educators and student project leaders", "https://www.youtube.com/", "A panel on how young people can make legal knowledge more accessible."),
            ],
        )


@app.on_event("startup")
def startup() -> None:
    init_db()


def get_user_by_session(request: Request) -> dict | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None

    connection = connect_db()
    try:
        user = connection.execute(
            """
            SELECT users.id, users.name, users.email, users.membership, users.joined_at,
                   users.address, users.city, users.country, users.phone, users.organization,
                   users.interests, users.registration_number, users.status
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token = ?
            """,
            (token,),
        ).fetchone()
        result = row_to_dict(user)
        if result:
            result["can_moderate_comments"] = can_moderate_comments(result)
            result["is_admin"] = is_admin(result)
        return result
    finally:
        connection.close()


def create_session_response(user: dict, message: str) -> JSONResponse:
    user = dict(user)
    user["can_moderate_comments"] = can_moderate_comments(user)
    user["is_admin"] = is_admin(user)
    token = secrets.token_urlsafe(32)
    connection = connect_db()
    try:
        connection.execute("DELETE FROM sessions WHERE user_id = ?", (user["id"],))
        connection.execute(
            "INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)",
            (token, user["id"], now_label()),
        )
        connection.commit()
    finally:
        connection.close()

    response = JSONResponse({"ok": True, "message": message, "user": user})
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )
    return response


def require_member(request: Request) -> dict:
    user = get_user_by_session(request)
    if not user:
        raise HTTPException(status_code=401, detail="Apply or log in before using this member feature.")
    return user


def fetch_all(sql: str, params: tuple = ()) -> list[dict]:
    connection = connect_db()
    try:
        rows = connection.execute(sql, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def get_comments() -> list[dict]:
    return fetch_all("SELECT id, user_name, text, created_at FROM comments ORDER BY id DESC LIMIT 30")


def get_recent_broadcasts() -> list[dict]:
    return fetch_all(
        """
        SELECT id, title, target, message, created_by, status, created_at
        FROM broadcasts
        ORDER BY id DESC
        LIMIT 8
        """
    )


def get_latest_broadcast() -> dict | None:
    rows = fetch_all(
        """
        SELECT id, title, target, message, created_by, status, created_at
        FROM broadcasts
        WHERE status = 'running'
        ORDER BY id DESC
        LIMIT 1
        """
    )
    return rows[0] if rows else None


def get_discussions() -> list[dict]:
    topics = fetch_all(
        "SELECT id, title, body, created_by, created_at FROM discussion_topics ORDER BY id DESC"
    )
    replies = fetch_all(
        "SELECT id, topic_id, body, created_by, created_at FROM discussion_replies ORDER BY id ASC"
    )
    for topic in topics:
        topic["replies"] = [reply for reply in replies if reply["topic_id"] == topic["id"]]
    return topics


def get_competition_winners() -> list[dict]:
    return fetch_all("SELECT id, month, winner_name, country, essay_title, summary FROM competition_winners ORDER BY id DESC")


def get_live_lessons() -> list[dict]:
    return fetch_all("SELECT id, title, lesson_date, host, platform, link, summary FROM live_lessons ORDER BY id ASC")


def get_projects() -> list[dict]:
    return fetch_all("SELECT id, country, title, description, coordinator, spots FROM internship_projects ORDER BY country ASC")


def get_courses() -> list[dict]:
    return fetch_all("SELECT id, title, category, duration, summary FROM courses ORDER BY id ASC")


def get_magazines() -> list[dict]:
    return fetch_all("SELECT id, month, title, summary, link FROM magazines ORDER BY id DESC")


def get_books() -> list[dict]:
    return fetch_all("SELECT id, title, year, summary FROM books ORDER BY id DESC")


def get_panels() -> list[dict]:
    return fetch_all("SELECT id, month, title, panel_date, speakers, link, summary FROM panels ORDER BY id DESC")


def get_member_submissions(user_id: int) -> dict:
    return {
        "essays": fetch_all(
            "SELECT id, title, country, summary, submitted_at, status FROM essay_entries WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ),
        "articles": fetch_all(
            "SELECT id, title, category, abstract, submitted_at, status FROM article_submissions WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ),
        "internships": fetch_all(
            """
            SELECT internship_applications.id, internship_projects.country, internship_projects.title,
                   internship_applications.motivation, internship_applications.submitted_at, internship_applications.status
            FROM internship_applications
            JOIN internship_projects ON internship_projects.id = internship_applications.project_id
            WHERE internship_applications.user_id = ?
            ORDER BY internship_applications.id DESC
            """,
            (user_id,),
        ),
    }


def active_class(current: str, expected: str) -> str:
    return "active" if current == expected else ""


def render_latest_broadcast(broadcast: dict | None) -> str:
    if not broadcast:
        return ""
    return f"""
        <section class="broadcast-strip" id="liveBroadcastBanner">
            <strong>{escape(broadcast["title"])}</strong>
            <span>{escape(broadcast["message"])}</span>
            <small>{escape(broadcast["target"])} - by {escape(broadcast["created_by"])}</small>
        </section>
    """


def render_simple_cards(items: list[dict], fields: list[str], class_name: str = "resource-card") -> str:
    cards = []
    for item in items:
        body = "".join(f"<p><strong>{escape(label)}:</strong> {escape(str(item[key]))}</p>" for key, label in fields if item.get(key))
        cards.append(f'<article class="{class_name}">{body}</article>')
    return "\n".join(cards)


def render_comments(comments: list[dict], user: dict | None = None) -> str:
    delete_button = ""
    can_delete = can_moderate_comments(user)
    return "\n".join(
        f"""
        <article class="comment" data-comment-id="{comment["id"]}">
            <strong>{escape(comment["user_name"])}</strong>
            <small>{escape(comment["created_at"])}</small>
            <p>{escape(comment["text"])}</p>
            {f'<button class="danger-button delete-comment" type="button" data-comment-id="{comment["id"]}">Delete Comment</button>' if can_delete else delete_button}
        </article>
        """
        for comment in comments
    )


def render_broadcasts(broadcasts: list[dict]) -> str:
    return "\n".join(
        f"""
        <article class="broadcast-item">
            <strong>{escape(broadcast["title"])}</strong>
            <span>{escape(broadcast["message"])}</span>
            <small>{escape(broadcast["target"])} - {escape(broadcast["status"])} - {escape(broadcast["created_at"])} - by {escape(broadcast["created_by"])}</small>
        </article>
        """
        for broadcast in broadcasts
    )


def render_discussions(topics: list[dict]) -> str:
    html = []
    for topic in topics:
        replies = "\n".join(
            f"""
            <article class="reply">
                <strong>{escape(reply["created_by"])}</strong>
                <small>{escape(reply["created_at"])}</small>
                <p>{escape(reply["body"])}</p>
            </article>
            """
            for reply in topic["replies"]
        )
        html.append(
            f"""
            <article class="discussion-topic" data-topic-id="{topic["id"]}">
                <div class="topic-head">
                    <div>
                        <h2>{escape(topic["title"])}</h2>
                        <small>Started by {escape(topic["created_by"])} - {escape(topic["created_at"])}</small>
                    </div>
                </div>
                <p>{escape(topic["body"])}</p>
                <div class="reply-list">{replies}</div>
                <form class="reply-form" data-topic-id="{topic["id"]}">
                    <label>
                        Reply with a detailed comment
                        <textarea name="replyBody" placeholder="Write a thoughtful reply..." required></textarea>
                    </label>
                    <button class="button secondary" type="submit">Post Reply</button>
                    <div class="status"></div>
                </form>
            </article>
            """
        )
    return "\n".join(html)


def render_lessons(lessons: list[dict]) -> str:
    return "\n".join(
        f"""
        <article class="resource-card">
            <span class="eyebrow">{escape(lesson["platform"])}</span>
            <h2>{escape(lesson["title"])}</h2>
            <p>{escape(lesson["summary"])}</p>
            <p><strong>Date:</strong> {escape(lesson["lesson_date"])}</p>
            <p><strong>Host:</strong> {escape(lesson["host"])}</p>
            <a class="button" href="{escape(lesson["link"])}" target="_blank" rel="noopener">Join Live Lesson</a>
        </article>
        """
        for lesson in lessons
    )


def render_magazines(magazines: list[dict]) -> str:
    return "\n".join(
        f"""
        <article class="resource-card">
            <span class="eyebrow">{escape(magazine["month"])}</span>
            <h2>{escape(magazine["title"])}</h2>
            <p>{escape(magazine["summary"])}</p>
            <a class="button secondary" href="{escape(magazine["link"])}">Open Magazine</a>
        </article>
        """
        for magazine in magazines
    )


def render_panels(panels: list[dict]) -> str:
    return "\n".join(
        f"""
        <article class="resource-card">
            <span class="eyebrow">{escape(panel["month"])}</span>
            <h2>{escape(panel["title"])}</h2>
            <p>{escape(panel["summary"])}</p>
            <p><strong>Date:</strong> {escape(panel["panel_date"])}</p>
            <p><strong>Speakers:</strong> {escape(panel["speakers"])}</p>
            <a class="button" href="{escape(panel["link"])}" target="_blank" rel="noopener">Join Panel</a>
        </article>
        """
        for panel in panels
    )


def render_project_options(projects: list[dict]) -> str:
    return "\n".join(
        f'<option value="{project["id"]}">{escape(project["country"])} - {escape(project["title"])}</option>'
        for project in projects
    )


def render_projects(projects: list[dict]) -> str:
    return "\n".join(
        f"""
        <article class="resource-card">
            <span class="eyebrow">{escape(project["country"])}</span>
            <h2>{escape(project["title"])}</h2>
            <p>{escape(project["description"])}</p>
            <p><strong>Coordinator:</strong> {escape(project["coordinator"])}</p>
            <p><strong>Availability:</strong> {escape(project["spots"])}</p>
        </article>
        """
        for project in projects
    )


def render_winners(winners: list[dict]) -> str:
    return "\n".join(
        f"""
        <article class="resource-card winner-card">
            <span class="eyebrow">{escape(winner["month"])}</span>
            <h2>{escape(winner["essay_title"])}</h2>
            <p><strong>Winner:</strong> {escape(winner["winner_name"])} ({escape(winner["country"])})</p>
            <p>{escape(winner["summary"])}</p>
        </article>
        """
        for winner in winners
    )


def render_user_list(items: list[dict], empty_text: str) -> str:
    if not items:
        return f"<p class=\"muted\">{escape(empty_text)}</p>"
    return "\n".join(
        f"""
        <article class="mini-item">
            <strong>{escape(item.get("title", item.get("country", "Submission")))}</strong>
            <small>{escape(item.get("submitted_at", ""))} - {escape(item.get("status", ""))}</small>
            <p>{escape(item.get("summary", item.get("abstract", item.get("motivation", ""))))}</p>
        </article>
        """
        for item in items
    )


def render_donation_widget() -> str:
    return read_template("components/donation_widget.html")


def replace_content_placeholders(content: str, context: dict, user: dict | None) -> str:
    submissions = get_member_submissions(user["id"]) if user else {"essays": [], "articles": [], "internships": []}
    replacements = {
        "__COMMENT_NAME__": escape(user["name"]) if user else "",
        "__COMMENTS__": render_comments(context.get("comments", []), user),
        "__BROADCASTS__": render_broadcasts(context.get("broadcasts", [])),
        "__DISCUSSIONS__": render_discussions(context.get("discussions", [])),
        "__WINNERS__": render_winners(context.get("winners", [])),
        "__LESSONS__": render_lessons(context.get("lessons", [])),
        "__PROJECTS__": render_projects(context.get("projects", [])),
        "__PROJECT_OPTIONS__": render_project_options(context.get("projects", [])),
        "__COURSES__": render_simple_cards(context.get("courses", []), [("category", "Category"), ("title", "Course"), ("duration", "Duration"), ("summary", "Summary")]),
        "__MAGAZINES__": render_magazines(context.get("magazines", [])),
        "__BOOKS__": render_simple_cards(context.get("books", []), [("year", "Year"), ("title", "Book"), ("summary", "Summary")]),
        "__PANELS__": render_panels(context.get("panels", [])),
        "__USER_ESSAYS__": render_user_list(submissions["essays"], "No essay submissions yet."),
        "__USER_ARTICLES__": render_user_list(submissions["articles"], "No article submissions yet."),
        "__USER_INTERNSHIPS__": render_user_list(submissions["internships"], "No internship applications yet."),
        "__CERTIFICATE_NAME__": escape(user["name"]) if user else "",
        "__CERTIFICATE_REGISTRATION__": escape(user["registration_number"]) if user else "",
        "__CERTIFICATE_DATE__": escape(user["joined_at"]) if user else "",
        "__CERTIFICATE_COUNTRY__": escape(user["country"]) if user else "",
        "__CERTIFICATE_LEVEL__": escape(user["membership"]) if user else "",
        "__DONATION_WIDGET__": render_donation_widget(),
    }
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)
    return content


def render_page(request: Request, template_name: str, active_page: str, title: str, protected: bool = False, **context):
    user = get_user_by_session(request)
    if protected and not user:
        content = read_template("member_required.html")
    else:
        content = read_template(template_name)

    content = replace_content_placeholders(content, context, user)

    base = read_template("base.html")
    chip_text = f"{escape(user['membership'])} Member" if user else ""
    chip_class = "member-chip show" if user else "member-chip"
    base_replacements = {
        "__TITLE__": escape(title),
        "__ACTIVE_HOME__": active_class(active_page, "home"),
        "__ACTIVE_ABOUT__": active_class(active_page, "about"),
        "__ACTIVE_WORK__": active_class(active_page, "work"),
        "__ACTIVE_MEMBERSHIP__": active_class(active_page, "membership"),
        "__ACTIVE_CONDUCT__": active_class(active_page, "conduct"),
        "__ACTIVE_CERTIFICATES__": active_class(active_page, "certificates"),
        "__ACTIVE_HUB__": active_class(active_page, "hub"),
        "__ACTIVE_DISCUSSIONS__": active_class(active_page, "discussions"),
        "__ACTIVE_COMPETITIONS__": active_class(active_page, "competitions"),
        "__ACTIVE_LESSONS__": active_class(active_page, "lessons"),
        "__ACTIVE_INTERNSHIPS__": active_class(active_page, "internships"),
        "__ACTIVE_COURSES__": active_class(active_page, "courses"),
        "__ACTIVE_PUBLICATIONS__": active_class(active_page, "publications"),
        "__ACTIVE_PANELS__": active_class(active_page, "panels"),
        "__ACTIVE_BROADCAST__": active_class(active_page, "broadcast"),
        "__ACTIVE_DONATE__": active_class(active_page, "donate"),
        "__LOGIN_HIDDEN__": "hidden" if user else "",
        "__LOGOUT_HIDDEN__": "" if user else "hidden",
        "__MEMBER_CHIP_CLASS__": chip_class,
        "__MEMBER_CHIP_TEXT__": chip_text,
        "__BROADCAST_BANNER__": render_latest_broadcast(get_latest_broadcast()),
        "__CONTENT__": content,
    }
    for placeholder, value in base_replacements.items():
        base = base.replace(placeholder, value)

    return HTMLResponse(base)


@app.get("/")
def home(request: Request):
    return render_page(request, "index.html", "home", "Generation Justice | Home")


@app.get("/health")
def health():
    return {"status": "ok", "service": "generation-justice"}


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt():
    return "User-agent: *\nAllow: /\n"


@app.get("/about")
def about(request: Request):
    return render_page(request, "about.html", "about", "Generation Justice | Who We Are")


@app.get("/what-we-do")
def what_we_do(request: Request):
    return render_page(request, "what_we_do.html", "work", "Generation Justice | What We Do")


@app.get("/membership")
def membership(request: Request):
    return render_page(request, "membership.html", "membership", "Generation Justice | Apply")


@app.get("/donate")
def donate(request: Request):
    return render_page(request, "donate.html", "donate", "Generation Justice | Donate")


@app.get("/code-of-conduct")
def code_of_conduct(request: Request):
    return render_page(request, "code_of_conduct.html", "conduct", "Generation Justice | Code of Conduct")


@app.get("/certificates")
def certificates(request: Request):
    return render_page(request, "certificates.html", "certificates", "Generation Justice | Membership Certificates")


@app.get("/hub")
def hub(request: Request):
    return render_page(request, "hub.html", "hub", "Generation Justice | Member Hub", protected=True)


@app.get("/certificate")
def certificate(request: Request):
    return render_page(request, "certificate.html", "hub", "Generation Justice | Membership Certificate", protected=True)


@app.get("/discussions")
def discussions(request: Request):
    return render_page(
        request,
        "discussions.html",
        "discussions",
        "Generation Justice | Discussions",
        protected=True,
        discussions=get_discussions(),
    )


@app.get("/competitions")
def competitions(request: Request):
    return render_page(
        request,
        "competitions.html",
        "competitions",
        "Generation Justice | Essay Competitions",
        protected=True,
        winners=get_competition_winners(),
    )


@app.get("/lessons")
def lessons(request: Request):
    return render_page(
        request,
        "lessons.html",
        "lessons",
        "Generation Justice | Live Lessons",
        protected=True,
        lessons=get_live_lessons(),
    )


@app.get("/internships")
def internships(request: Request):
    projects = get_projects()
    return render_page(
        request,
        "internships.html",
        "internships",
        "Generation Justice | Internships",
        protected=True,
        projects=projects,
    )


@app.get("/courses")
def courses(request: Request):
    return render_page(
        request,
        "courses.html",
        "courses",
        "Generation Justice | Free Courses",
        protected=True,
        courses=get_courses(),
    )


@app.get("/publications")
def publications(request: Request):
    return render_page(
        request,
        "publications.html",
        "publications",
        "Generation Justice | Publications",
        protected=True,
        magazines=get_magazines(),
        books=get_books(),
    )


@app.get("/panels")
def panels(request: Request):
    return render_page(
        request,
        "panels.html",
        "panels",
        "Generation Justice | Panel Discussions",
        protected=True,
        panels=get_panels(),
    )


@app.get("/comments")
def comments(request: Request):
    return render_page(
        request,
        "comments.html",
        "discussions",
        "Generation Justice | Comments",
        protected=True,
        comments=get_comments(),
    )


@app.get("/broadcast")
def broadcast(request: Request):
    return render_page(
        request,
        "broadcast.html",
        "broadcast",
        "Generation Justice | Broadcast",
        protected=True,
        broadcasts=get_recent_broadcasts(),
    )


@app.get("/api/me")
def current_user(request: Request):
    return {"user": get_user_by_session(request)}


@app.post("/api/login")
def login(payload: LoginPayload):
    email = clean(payload.email.lower(), 160)
    password = payload.password
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required.")

    connection = connect_db()
    try:
        user_row = connection.execute(
            """
            SELECT id, name, email, membership, joined_at, address, city, country, phone,
                   organization, interests, registration_number, status, password_hash
            FROM users
            WHERE email = ?
            """,
            (email,),
        ).fetchone()
        if not user_row or user_row["password_hash"] != hash_password(password):
            raise HTTPException(status_code=401, detail="Incorrect email or password.")

        user = dict(user_row)
        user.pop("password_hash")
    finally:
        connection.close()

    return create_session_response(user, "You are logged in.")


@app.post("/api/apply")
def apply_for_membership(payload: ApplicationPayload):
    name = clean(payload.name, 120)
    address = clean(payload.address, 220)
    city = clean(payload.city, 120)
    country = clean(payload.country, 120)
    email = clean(payload.email.lower(), 160)
    phone = clean(payload.phone, 80)
    organization = clean(payload.organization, 160)
    password = payload.password.strip()
    membership = payload.membership if payload.membership in MEMBERSHIP_LEVELS else "Ambassador"
    interests = clean(payload.interests, 1000)

    if not name or not address or not country or not email or not phone or len(password) < 4:
        raise HTTPException(
            status_code=400,
            detail="Name, address, country, email, phone, and a password with at least 4 characters are required.",
        )

    connection = connect_db()
    try:
        existing = connection.execute("SELECT id, registration_number FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            user_id = existing["id"]
            registration_number = existing["registration_number"] or generate_registration_number(user_id)
            connection.execute(
                """
                UPDATE users
                SET name = ?, password_hash = ?, membership = ?, address = ?, city = ?, country = ?,
                    phone = ?, organization = ?, interests = ?, registration_number = ?, status = ?
                WHERE id = ?
                """,
                (
                    name,
                    hash_password(password),
                    membership,
                    address,
                    city,
                    country,
                    phone,
                    organization,
                    interests,
                    registration_number,
                    "approved",
                    user_id,
                ),
            )
        else:
            cursor = connection.execute(
                """
                INSERT INTO users
                    (name, email, password_hash, membership, joined_at, address, city, country, phone, organization, interests, registration_number, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    email,
                    hash_password(password),
                    membership,
                    now_label(),
                    address,
                    city,
                    country,
                    phone,
                    organization,
                    interests,
                    "",
                    "approved",
                ),
            )
            user_id = cursor.lastrowid
            registration_number = generate_registration_number(user_id)
            connection.execute(
                "UPDATE users SET registration_number = ? WHERE id = ?",
                (registration_number, user_id),
            )

        connection.commit()
        user = connection.execute(
            """
            SELECT id, name, email, membership, joined_at, address, city, country, phone,
                   organization, interests, registration_number, status
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()
    finally:
        connection.close()

    return create_session_response(
        dict(user),
        f"Application approved. Your registration number is {registration_number}.",
    )


@app.post("/api/join")
def join(payload: ApplicationPayload):
    return apply_for_membership(payload)


@app.post("/api/logout")
def logout(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        connection = connect_db()
        try:
            connection.execute("DELETE FROM sessions WHERE token = ?", (token,))
            connection.commit()
        finally:
            connection.close()

    response = JSONResponse({"ok": True, "message": "You are logged out."})
    response.delete_cookie(SESSION_COOKIE)
    return response


@app.post("/api/comments")
def create_comment(payload: CommentPayload, request: Request):
    user = require_member(request)
    text = clean(payload.text, 2000)
    if not text:
        raise HTTPException(status_code=400, detail="Comment text is required.")

    connection = connect_db()
    try:
        cursor = connection.execute(
            "INSERT INTO comments (user_name, text, created_at) VALUES (?, ?, ?)",
            (user["name"], text, now_label()),
        )
        connection.commit()
        comment = connection.execute(
            "SELECT id, user_name, text, created_at FROM comments WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        return {"ok": True, "comment": dict(comment)}
    finally:
        connection.close()


@app.delete("/api/comments/{comment_id}")
def delete_comment(comment_id: int, request: Request):
    user = require_member(request)
    if not can_moderate_comments(user):
        raise HTTPException(status_code=403, detail="Only organizer-level accounts can delete comments.")

    connection = connect_db()
    try:
        comment = connection.execute(
            "SELECT id FROM comments WHERE id = ?",
            (comment_id,),
        ).fetchone()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment was not found.")
        connection.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
        connection.commit()
        return {"ok": True, "message": "Comment deleted.", "comment_id": comment_id}
    finally:
        connection.close()


@app.post("/api/discussions/topics")
def create_topic(payload: TopicPayload, request: Request):
    user = require_member(request)
    title = clean(payload.title, 180)
    body = clean(payload.body, 5000)
    if not title or not body:
        raise HTTPException(status_code=400, detail="Topic title and body are required.")

    connection = connect_db()
    try:
        cursor = connection.execute(
            "INSERT INTO discussion_topics (title, body, created_by, created_at) VALUES (?, ?, ?, ?)",
            (title, body, user["name"], now_label()),
        )
        connection.commit()
        topic = connection.execute(
            "SELECT id, title, body, created_by, created_at FROM discussion_topics WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        result = dict(topic)
        result["replies"] = []
        return {"ok": True, "topic": result}
    finally:
        connection.close()


@app.post("/api/discussions/replies")
def create_reply(payload: ReplyPayload, request: Request):
    user = require_member(request)
    body = clean(payload.body, 5000)
    if not body:
        raise HTTPException(status_code=400, detail="Reply text is required.")

    connection = connect_db()
    try:
        topic = connection.execute("SELECT id FROM discussion_topics WHERE id = ?", (payload.topic_id,)).fetchone()
        if not topic:
            raise HTTPException(status_code=404, detail="Discussion topic was not found.")
        cursor = connection.execute(
            "INSERT INTO discussion_replies (topic_id, body, created_by, created_at) VALUES (?, ?, ?, ?)",
            (payload.topic_id, body, user["name"], now_label()),
        )
        connection.commit()
        reply = connection.execute(
            "SELECT id, topic_id, body, created_by, created_at FROM discussion_replies WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        return {"ok": True, "reply": dict(reply)}
    finally:
        connection.close()


@app.post("/api/essays")
def submit_essay(payload: EssayPayload, request: Request):
    user = require_member(request)
    title = clean(payload.title, 180)
    country = clean(payload.country, 120)
    summary = clean(payload.summary, 3000)
    if not title or not country or not summary:
        raise HTTPException(status_code=400, detail="Essay title, country, and summary are required.")

    connection = connect_db()
    try:
        cursor = connection.execute(
            "INSERT INTO essay_entries (user_id, title, country, summary, submitted_at, status) VALUES (?, ?, ?, ?, ?, ?)",
            (user["id"], title, country, summary, now_label(), "received"),
        )
        connection.commit()
        entry = connection.execute(
            "SELECT id, title, country, summary, submitted_at, status FROM essay_entries WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        return {"ok": True, "entry": dict(entry), "message": "Essay submitted for the monthly competition."}
    finally:
        connection.close()


@app.post("/api/articles")
def submit_article(payload: ArticlePayload, request: Request):
    user = require_member(request)
    title = clean(payload.title, 180)
    category = clean(payload.category, 120)
    abstract = clean(payload.abstract, 3000)
    if not title or not category or not abstract:
        raise HTTPException(status_code=400, detail="Article title, category, and abstract are required.")

    connection = connect_db()
    try:
        cursor = connection.execute(
            "INSERT INTO article_submissions (user_id, title, category, abstract, submitted_at, status) VALUES (?, ?, ?, ?, ?, ?)",
            (user["id"], title, category, abstract, now_label(), "received"),
        )
        connection.commit()
        article = connection.execute(
            "SELECT id, title, category, abstract, submitted_at, status FROM article_submissions WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        return {"ok": True, "article": dict(article), "message": "Article submitted for editorial review."}
    finally:
        connection.close()


@app.post("/api/internships/apply")
def apply_internship(payload: InternshipPayload, request: Request):
    user = require_member(request)
    motivation = clean(payload.motivation, 3000)
    if not motivation:
        raise HTTPException(status_code=400, detail="Please explain why you want to volunteer for this project.")

    connection = connect_db()
    try:
        project = connection.execute(
            "SELECT id FROM internship_projects WHERE id = ?",
            (payload.project_id,),
        ).fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="Project was not found.")
        cursor = connection.execute(
            "INSERT INTO internship_applications (user_id, project_id, motivation, submitted_at, status) VALUES (?, ?, ?, ?, ?)",
            (user["id"], payload.project_id, motivation, now_label(), "received"),
        )
        connection.commit()
        application = connection.execute(
            """
            SELECT internship_applications.id, internship_projects.country, internship_projects.title,
                   internship_applications.motivation, internship_applications.submitted_at, internship_applications.status
            FROM internship_applications
            JOIN internship_projects ON internship_projects.id = internship_applications.project_id
            WHERE internship_applications.id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
        return {"ok": True, "application": dict(application), "message": "Internship application received."}
    finally:
        connection.close()


@app.post("/api/broadcasts")
def create_broadcast(payload: BroadcastPayload, request: Request):
    user = require_member(request)
    allowed_targets = {
        "Home page",
        "Who We Are page",
        "What We Do page",
        "Membership page",
        "Member Hub",
        "Discussions page",
        "Competitions page",
        "Lessons page",
        "Internships page",
        "Courses page",
        "Publications page",
        "Panel Discussions page",
        "Donate page",
        "All pages",
    }
    title = clean(payload.title, 140)
    target = payload.target if payload.target in allowed_targets else "All pages"
    message = clean(payload.message, 900)
    if not title or not message:
        raise HTTPException(status_code=400, detail="Broadcast title and message are required.")

    connection = connect_db()
    try:
        cursor = connection.execute(
            """
            INSERT INTO broadcasts (title, target, message, created_by, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, target, message, user["name"], "running", now_label()),
        )
        connection.commit()
        broadcast = connection.execute(
            """
            SELECT id, title, target, message, created_by, status, created_at
            FROM broadcasts
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
        return {"ok": True, "broadcast": dict(broadcast)}
    finally:
        connection.close()


@app.get("/api/broadcasts")
def broadcasts():
    return {"broadcasts": get_recent_broadcasts()}


@app.get("/api/donations/config")
def donation_config():
    return {
        "payments_enabled": False,
        "provider": "stripe",
        "currency": "USD",
        "frequencies": list(DONATION_FREQUENCIES),
        "tiers": DONATION_TIERS,
        "custom_amount_enabled": True,
    }


@app.post("/api/donations/preview")
def donation_preview(payload: DonationPreviewPayload):
    frequency = payload.frequency if payload.frequency in DONATION_FREQUENCIES else "one_time"
    tier = payload.tier if payload.tier in DONATION_TIERS or payload.tier == "custom" else "silver"
    default_amount = DONATION_TIERS.get(tier, DONATION_TIERS["silver"])["amount"] if tier != "custom" else 50
    amount = payload.amount if payload.amount > 0 else default_amount

    return {
        "ok": True,
        "payments_enabled": False,
        "provider": "stripe",
        "currency": "USD",
        "frequency": frequency,
        "tier": tier,
        "amount": amount,
        "message": "Donation preview prepared. Payments are not active yet.",
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port)
