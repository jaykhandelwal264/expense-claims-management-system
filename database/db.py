import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime


# Database file will be created inside the database folder
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "expense_claims.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    # Enable foreign key relationships in SQLite
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Employees / users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            employee_id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,

            role TEXT NOT NULL CHECK (
                role IN ('Staff', 'Manager', 'Finance')
            ),

            department TEXT,

            manager_level INTEGER DEFAULT 0,

            reports_to TEXT,

            is_active INTEGER DEFAULT 1 CHECK (
                is_active IN (0, 1)
            ),

            created_at TEXT NOT NULL,

            FOREIGN KEY (reports_to)
                REFERENCES employees(employee_id)
        )
    """)

    # Expense categories
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT UNIQUE NOT NULL,
            default_monthly_limit REAL NOT NULL
        )
    """)

    # Employee-specific expense limits
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employee_limits (
            limit_id INTEGER PRIMARY KEY AUTOINCREMENT,

            employee_id TEXT NOT NULL,

            category_id INTEGER NOT NULL,

            monthly_limit REAL NOT NULL,

            FOREIGN KEY (employee_id)
                REFERENCES employees(employee_id),

            FOREIGN KEY (category_id)
                REFERENCES categories(category_id),

            UNIQUE(employee_id, category_id)
        )
    """)

    # Claims
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS claims (
            claim_id TEXT PRIMARY KEY,

            employee_id TEXT NOT NULL,

            approver_id TEXT,

            merchant_name TEXT,

            expense_date TEXT NOT NULL,

            amount REAL NOT NULL CHECK (amount >= 0),

            category_id INTEGER,

            description TEXT,

            status TEXT NOT NULL DEFAULT 'Draft'
                CHECK (
                    status IN (
                        'Draft',
                        'Submitted',
                        'Approved',
                        'Rejected',
                        'Paid'
                    )
                ),

            duplicate_flag INTEGER DEFAULT 0
                CHECK (duplicate_flag IN (0, 1)),

            duplicate_score REAL DEFAULT 0,

            submitted_at TEXT,

            approved_at TEXT,

            rejected_at TEXT,

            paid_at TEXT,

            paid_by TEXT,

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL,

            FOREIGN KEY (employee_id)
                REFERENCES employees(employee_id),

            FOREIGN KEY (approver_id)
                REFERENCES employees(employee_id),

            FOREIGN KEY (category_id)
                REFERENCES categories(category_id),

            FOREIGN KEY (paid_by)
                REFERENCES employees(employee_id)
        )
    """)

    # Receipt images and OCR results
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS receipts (
            receipt_id INTEGER PRIMARY KEY AUTOINCREMENT,

            claim_id TEXT NOT NULL UNIQUE,

            image_path TEXT NOT NULL,

            original_filename TEXT,

            ocr_text TEXT,

            file_hash TEXT,

            perceptual_hash TEXT,

            extraction_confidence REAL,

            uploaded_at TEXT NOT NULL,

            FOREIGN KEY (claim_id)
                REFERENCES claims(claim_id)
                ON DELETE CASCADE
        )
    """)

    # Claim history / audit trail
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS claim_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,

            claim_id TEXT NOT NULL,

            changed_by TEXT NOT NULL,

            old_status TEXT,

            new_status TEXT NOT NULL,

            remarks TEXT,

            changed_at TEXT NOT NULL,

            FOREIGN KEY (claim_id)
                REFERENCES claims(claim_id),

            FOREIGN KEY (changed_by)
                REFERENCES employees(employee_id)
        )
    """)

    conn.commit()
    conn.close()


def seed_categories():
    conn = get_connection()
    cursor = conn.cursor()

    categories = [
        ("Taxi / Local Travel", 6000),
        ("Meals", 5000),
        ("Travel", 12000),
        ("Accommodation", 20000),
        ("Office Supplies", 4000),
        ("Other", 5000)
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO categories (
            category_name,
            default_monthly_limit
        )
        VALUES (?, ?)
    """, categories)

    conn.commit()
    conn.close()


def seed_employees():
    conn = get_connection()
    cursor = conn.cursor()

    created_at = datetime.now().isoformat(
        sep=" ",
        timespec="seconds"
    )

    # Insert highest manager first because other managers report to them
    employees = [
        (
            "EMP007",
            "Ananya Verma",
            "ananya@vsptechverse.com",
            hash_password("1234"),
            "Manager",
            "Management",
            4,
            None,
            1,
            created_at
        ),

        (
            "EMP006",
            "Rohan Malhotra",
            "rohan@vsptechverse.com",
            hash_password("1234"),
            "Manager",
            "Technology",
            3,
            "EMP007",
            1,
            created_at
        ),

        (
            "EMP005",
            "Neha Kapoor",
            "neha@vsptechverse.com",
            hash_password("1234"),
            "Manager",
            "Engineering",
            2,
            "EMP006",
            1,
            created_at
        ),

        (
            "EMP003",
            "Vikram Singh",
            "vikram@vsptechverse.com",
            hash_password("1234"),
            "Manager",
            "Engineering",
            1,
            "EMP005",
            1,
            created_at
        ),

        (
            "EMP001",
            "Aarav Mehta",
            "aarav@vsptechverse.com",
            hash_password("1234"),
            "Staff",
            "Engineering",
            0,
            "EMP003",
            1,
            created_at
        ),

        (
            "EMP002",
            "Priya Sharma",
            "priya@vsptechverse.com",
            hash_password("1234"),
            "Staff",
            "Engineering",
            0,
            "EMP003",
            1,
            created_at
        ),

        (
            "FIN001",
            "Kavya Iyer",
            "kavya.finance@vsptechverse.com",
            hash_password("1234"),
            "Finance",
            "Finance",
            0,
            None,
            1,
            created_at
        )
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO employees (
            employee_id,
            full_name,
            email,
            password_hash,
            role,
            department,
            manager_level,
            reports_to,
            is_active,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, employees)

    conn.commit()
    conn.close()


def show_employees():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            e.employee_id,
            e.full_name,
            e.role,
            e.manager_level,
            e.reports_to,
            m.full_name AS manager_name
        FROM employees e
        LEFT JOIN employees m
            ON e.reports_to = m.employee_id
        ORDER BY
            e.manager_level DESC,
            e.employee_id
    """)

    rows = cursor.fetchall()

    print("\nEmployees and Reporting Structure\n")

    for row in rows:
        print(
            row["employee_id"],
            "|",
            row["full_name"],
            "| Role:",
            row["role"],
            "| Level:",
            row["manager_level"],
            "| Reports To:",
            row["manager_name"]
        )

    conn.close()


def update_database_schema():
    """
    Apply small database upgrades to an existing database.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "PRAGMA table_info(claims)"
    )

    existing_columns = {
        row["name"]
        for row in cursor.fetchall()
    }

    # Add currency column if it does not already exist
    if "currency" not in existing_columns:

        cursor.execute(
            """
            ALTER TABLE claims
            ADD COLUMN currency TEXT
            DEFAULT 'INR'
            """
        )

        print(
            "Added currency column to claims table."
        )
    if "limit_flag" not in existing_columns:
        cursor.execute(
        """
        ALTER TABLE claims
        ADD COLUMN limit_flag INTEGER DEFAULT 0
        """
    )

        print(
        "Added limit_flag column to claims table."
    )


    if "limit_exceeded_by" not in existing_columns:
        cursor.execute(
        """
        ALTER TABLE claims
        ADD COLUMN limit_exceeded_by REAL DEFAULT 0
        """
        )

        print(
        "Added limit_exceeded_by column to claims table."
        )
    conn.commit()
    conn.close()

def seed_employee_limits():
    """
    Give every Staff/Manager the default
    category limits.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO employee_limits (
            employee_id,
            category_id,
            monthly_limit
        )

        SELECT
            e.employee_id,
            c.category_id,
            c.default_monthly_limit

        FROM employees e

        CROSS JOIN categories c

        WHERE e.role IN ('Staff', 'Manager')
        """
    )

    conn.commit()
    conn.close()

def initialize_database():
    create_tables()

    update_database_schema()

    seed_categories()
    seed_employees()
    seed_employee_limits()
    print(
        f"\nDatabase ready at:\n{DB_PATH}"
    )

    show_employees()


if __name__ == "__main__":
    initialize_database()