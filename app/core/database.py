# app/core/database.py
import logging
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.confing import settings
Base = declarative_base()
_RUNTIME_SCHEMA_VERIFIED = False

DATABASE_URL = settings.database_url


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=settings.sql_echo,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def load_models():
    """Import ORM models so SQLAlchemy can register metadata before create_all."""
    import app.models.audit_log  # noqa: F401
    import app.models.noor_program  # noqa: F401
    import app.models.role  # noqa: F401
    import app.models.student_profile  # noqa: F401
    import app.models.user  # noqa: F401



def ensure_student_profiles_schema():
    inspector = inspect(engine)
    if "student_profiles" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("student_profiles")}
    pending_columns = []

    if "first_name" not in existing_columns:
        pending_columns.append(("first_name", "VARCHAR(50) NOT NULL DEFAULT ''"))
    if "last_name" not in existing_columns:
        pending_columns.append(("last_name", "VARCHAR(50) NOT NULL DEFAULT ''"))
    if "student_number" not in existing_columns:
        pending_columns.append(("student_number", "VARCHAR(20) NOT NULL DEFAULT ''"))
    if "has_authenticated" not in existing_columns:
        pending_columns.append(("has_authenticated", "BOOLEAN NOT NULL DEFAULT 0"))

    existing_indexes = {index["name"] for index in inspector.get_indexes("student_profiles")}

    if not pending_columns and "ix_student_profiles_phone_number" in existing_indexes:
        return

    with engine.begin() as connection:
        for column_name, column_ddl in pending_columns:
            connection.execute(
                text(f"ALTER TABLE student_profiles ADD COLUMN {column_name} {column_ddl}")
            )
        if "ix_student_profiles_phone_number" not in existing_indexes:
            duplicate_phone_numbers = connection.execute(
                text(
                    """
                    SELECT phone_number
                    FROM student_profiles
                    GROUP BY phone_number
                    HAVING COUNT(*) > 1
                    LIMIT 1
                    """
                )
            ).first()

            if duplicate_phone_numbers:
                logging.getLogger(__name__).warning(
                    "Skipped creating unique index on student_profiles.phone_number "
                    "because duplicate values already exist (example=%s).",
                    duplicate_phone_numbers[0],
                )
                return

            try:
                connection.execute(
                    text(
                        "CREATE UNIQUE INDEX IF NOT EXISTS ix_student_profiles_phone_number "
                        "ON student_profiles (phone_number)"
                    )
                )
            except IntegrityError:
                logging.getLogger(__name__).exception(
                    "Failed to create unique index ix_student_profiles_phone_number due to existing duplicates."
                )


def ensure_noor_program_schema():
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    noor_tables = {
        "quran_class_requests": """
            CREATE TABLE IF NOT EXISTS quran_class_requests (
                id INTEGER NOT NULL PRIMARY KEY,
                user_id INTEGER,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                level INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users (id)
            )
        """,
        "quran_classes": """
            CREATE TABLE IF NOT EXISTS quran_classes (
                id INTEGER NOT NULL PRIMARY KEY,
                title VARCHAR(100) NOT NULL,
                level INTEGER NOT NULL,
                description VARCHAR(255),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
            )
        """,
        "light_path_students": """
            CREATE TABLE IF NOT EXISTS light_path_students (
                id INTEGER NOT NULL PRIMARY KEY,
                user_id INTEGER,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                email VARCHAR(255) NOT NULL,
                phone_number VARCHAR(20) NOT NULL,
                enrollment_date DATE NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                student_number VARCHAR(20),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users (id)
            )
        """,
    }

    required_indexes = [
        "CREATE INDEX IF NOT EXISTS ix_quran_class_requests_user_id ON quran_class_requests (user_id)",
        "CREATE INDEX IF NOT EXISTS ix_quran_classes_level ON quran_classes (level)",
        "CREATE INDEX IF NOT EXISTS ix_light_path_students_user_id ON light_path_students (user_id)",
        "CREATE INDEX IF NOT EXISTS ix_light_path_students_email ON light_path_students (email)",
        "CREATE INDEX IF NOT EXISTS ix_light_path_students_student_number ON light_path_students (student_number)",
    ]

    with engine.begin() as connection:
        for table_name, ddl in noor_tables.items():
            if table_name not in table_names:
                connection.execute(text(ddl))
        if "light_path_students" in table_names:
            existing_columns = {column["name"] for column in inspector.get_columns("light_path_students")}
            if "email" not in existing_columns:
                connection.execute(
                    text("ALTER TABLE light_path_students ADD COLUMN email VARCHAR(255) NOT NULL DEFAULT ''")
                )
            if "phone_number" not in existing_columns:
                connection.execute(
                    text("ALTER TABLE light_path_students ADD COLUMN phone_number VARCHAR(20) NOT NULL DEFAULT ''")
                )
            if "enrollment_date" not in existing_columns:
                connection.execute(
                    text(
                        "ALTER TABLE light_path_students ADD COLUMN enrollment_date DATE NOT NULL DEFAULT CURRENT_DATE"
                    )
                )
            if "is_active" not in existing_columns:
                connection.execute(
                    text("ALTER TABLE light_path_students ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1")
                )
        for ddl in required_indexes:
            connection.execute(text(ddl))




def create_database():
    load_models()
    Base.metadata.create_all(bind=engine)
    ensure_student_profiles_schema()
    ensure_noor_program_schema()
    logging.getLogger(__name__).info("✅ دیتابیس در %s ایجاد شد", DATABASE_URL)

def ensure_runtime_schema():
    """Ensure required tables exist even when startup lifespan hooks are skipped."""
    global _RUNTIME_SCHEMA_VERIFIED
    if _RUNTIME_SCHEMA_VERIFIED:
        return

    load_models()
    Base.metadata.create_all(bind=engine)
    ensure_student_profiles_schema()
    ensure_noor_program_schema()
    _RUNTIME_SCHEMA_VERIFIED = True


def show_tables():
    from sqlalchemy import inspect

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print("\n📊 جداول موجود در دیتابیس:")
    for table in tables:
        print(f"  - {table}")
        columns = inspector.get_columns(table)
        for column in columns:
            print(f"    ├─ {column['name']}: {column['type']}")

    return tables