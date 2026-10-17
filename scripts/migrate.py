import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load apps/api/.env
env_path = Path(__file__).resolve().parent.parent / "apps" / "api" / ".env"
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL or "[YOUR-PASSWORD]" in DATABASE_URL:
    print("ERROR: Please set your actual Supabase DATABASE_URL in apps/api/.env before migrating.")
    sys.exit(1)

try:
    import psycopg
except ImportError:
    print("ERROR: psycopg is not installed. Run 'pip install psycopg[binary]' first.")
    sys.exit(1)

migration_file = Path(__file__).resolve().parent.parent / "database" / "migrations" / "001_initial_schema.sql"
if not migration_file.exists():
    print(f"ERROR: Migration file not found at {migration_file}")
    sys.exit(1)

print(f"Connecting to database...")

# Strip SQLAlchemy prefix 'postgresql+psycopg://' if present for direct psycopg connection
conn_url = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")

try:
    with psycopg.connect(conn_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            print("Running initial schema migration (001_initial_schema.sql)...")
            sql = migration_file.read_text(encoding="utf-8")
            cur.execute(sql)
            print("[SUCCESS] Migration applied successfully! All tables, enums, and indexes created in Supabase.")

            seed_file = Path(__file__).resolve().parent.parent / "database" / "seeds" / "001_seed_data.sql"
            if seed_file.exists():
                print("Seeding initial fleet data (drivers, vehicles, delivery types)...")
                seed_sql = seed_file.read_text(encoding="utf-8")
                cur.execute(seed_sql)
                print("[SUCCESS] Seed data inserted successfully!")
except Exception as e:
    print(f"[FAILED] Migration failed: {e}")
    sys.exit(1)
