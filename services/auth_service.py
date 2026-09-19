import hashlib

from database.db import get_connection


def hash_password(password):
    return hashlib.sha256(
        password.encode()
    ).hexdigest()


def authenticate_user(login_value, password):
    """
    Login using Employee ID or Email.
    """

    login_value = login_value.strip()

    if not login_value or not password:
        return None

    password_hash = hash_password(
        password
    )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            employee_id,
            full_name,
            email,
            role,
            department,
            manager_level,
            reports_to

        FROM employees

        WHERE
            (
                employee_id = ?
                OR LOWER(email) = LOWER(?)
            )
            AND password_hash = ?
            AND is_active = 1
        """,
        (
            login_value,
            login_value,
            password_hash
        )
    )

    user = cursor.fetchone()

    conn.close()

    if not user:
        return None

    return dict(user)