# app/core/database.py
import logging
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.confing import settings

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


Base = declarative_base()



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
            connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_student_profiles_phone_number ON student_profiles (phone_number)"))




def create_database():
    Base.metadata.create_all(bind=engine)
    ensure_student_profiles_schema()
    logging.getLogger(__name__).info("✅ دیتابیس در %s ایجاد شد", DATABASE_URL)


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