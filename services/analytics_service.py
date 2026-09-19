from datetime import date

from database.db import get_connection


def get_month_range(year, month):

    start_date = date(
        year,
        month,
        1
    )

    if month == 12:

        end_date = date(
            year + 1,
            1,
            1
        )

    else:

        end_date = date(
            year,
            month + 1,
            1
        )

    return (
        start_date.isoformat(),
        end_date.isoformat()
    )


def get_employee_category_limit(
    employee_id,
    category_id
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT monthly_limit
        FROM employee_limits
        WHERE
            employee_id = ?
            AND category_id = ?
        """,
        (
            employee_id,
            category_id
        )
    )

    result = cursor.fetchone()

    conn.close()

    if result:
        return float(
            result["monthly_limit"]
        )

    return None


def get_monthly_category_spend(
    employee_id,
    category_id,
    year,
    month
):
    """
    Count submitted, approved and paid claims.

    Draft and Rejected claims do not count.
    """

    start_date, end_date = get_month_range(
        year,
        month
    )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            COALESCE(
                SUM(amount),
                0
            ) AS total_spend

        FROM claims

        WHERE
            employee_id = ?
            AND category_id = ?
            AND currency = 'INR'
            AND status IN (
                'Submitted',
                'Approved',
                'Paid'
            )
            AND expense_date >= ?
            AND expense_date < ?
        """,
        (
            employee_id,
            category_id,
            start_date,
            end_date
        )
    )

    result = cursor.fetchone()

    conn.close()

    return float(
        result["total_spend"]
    )


def check_claim_limit(claim_id):
    """
    Check what happens to the employee's
    monthly category limit if this claim is submitted.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            claim_id,
            employee_id,
            category_id,
            expense_date,
            amount,
            currency

        FROM claims

        WHERE claim_id = ?
        """,
        (claim_id,)
    )

    claim = cursor.fetchone()

    conn.close()

    if not claim:
        raise ValueError(
            "Claim was not found."
        )

    # For MVP, company limits are maintained in INR.
    # Foreign currency claims will require Finance review.
    if claim["currency"] != "INR":

        return {
            "claim_id": claim_id,
            "currency": claim["currency"],
            "foreign_currency": True,
            "monthly_limit": None,
            "current_spend": None,
            "projected_spend": None,
            "percentage_used": None,
            "near_limit": False,
            "limit_exceeded": False,
            "exceeded_by": 0
        }

    year, month, _ = map(
        int,
        claim["expense_date"].split("-")
    )

    monthly_limit = get_employee_category_limit(
        claim["employee_id"],
        claim["category_id"]
    )

    if monthly_limit is None:

        return {
            "claim_id": claim_id,
            "foreign_currency": False,
            "monthly_limit": None,
            "current_spend": 0,
            "projected_spend": float(
                claim["amount"]
            ),
            "percentage_used": 0,
            "near_limit": False,
            "limit_exceeded": False,
            "exceeded_by": 0
        }

    current_spend = get_monthly_category_spend(
        claim["employee_id"],
        claim["category_id"],
        year,
        month
    )

    projected_spend = (
        current_spend
        + float(claim["amount"])
    )

    percentage_used = (
        projected_spend
        / monthly_limit
        * 100
    )

    exceeded_by = max(
        0,
        projected_spend
        - monthly_limit
    )

    return {
        "claim_id": claim_id,
        "currency": "INR",
        "foreign_currency": False,

        "monthly_limit": monthly_limit,

        "current_spend": round(
            current_spend,
            2
        ),

        "projected_spend": round(
            projected_spend,
            2
        ),

        "percentage_used": round(
            percentage_used,
            2
        ),

        "near_limit": (
            90 <= percentage_used <= 100
        ),

        "limit_exceeded": (
            projected_spend > monthly_limit
        ),

        "exceeded_by": round(
            exceeded_by,
            2
        )
    }


def get_limit_report(
    year,
    month
):
    """
    Finance report:
    employee + category + monthly spend + limit.
    """

    start_date, end_date = get_month_range(
        year,
        month
    )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            e.employee_id,
            e.full_name,

            c.category_id,
            c.category_name,

            el.monthly_limit,

            COALESCE(
                SUM(
                    CASE

                        WHEN
                            cl.currency = 'INR'

                            AND cl.status IN (
                                'Submitted',
                                'Approved',
                                'Paid'
                            )

                            AND cl.expense_date >= ?
                            AND cl.expense_date < ?

                        THEN cl.amount

                        ELSE 0

                    END
                ),
                0
            ) AS monthly_spend

        FROM employee_limits el

        JOIN employees e
            ON el.employee_id = e.employee_id

        JOIN categories c
            ON el.category_id = c.category_id

        LEFT JOIN claims cl
            ON cl.employee_id = e.employee_id
            AND cl.category_id = c.category_id

        WHERE e.is_active = 1

        GROUP BY
            e.employee_id,
            e.full_name,
            c.category_id,
            c.category_name,
            el.monthly_limit

        ORDER BY
            e.full_name,
            c.category_name
        """,
        (
            start_date,
            end_date
        )
    )

    rows = cursor.fetchall()

    conn.close()

    report = []

    for row in rows:

        spend = float(
            row["monthly_spend"]
        )

        limit_value = float(
            row["monthly_limit"]
        )

        percentage = (
            spend
            / limit_value
            * 100
            if limit_value > 0
            else 0
        )

        report.append(
            {
                "employee_id":
                    row["employee_id"],

                "employee_name":
                    row["full_name"],

                "category":
                    row["category_name"],

                "monthly_limit":
                    limit_value,

                "monthly_spend":
                    round(
                        spend,
                        2
                    ),

                "percentage_used":
                    round(
                        percentage,
                        2
                    ),

                "over_limit":
                    spend > limit_value,

                "exceeded_by":
                    round(
                        max(
                            0,
                            spend - limit_value
                        ),
                        2
                    )
            }
        )

    return report

def get_finance_filter_options():
    """
    Values used by Finance dashboard filters.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT DISTINCT
            SUBSTR(expense_date, 1, 7) AS month_key

        FROM claims

        WHERE expense_date IS NOT NULL

        ORDER BY month_key DESC
        """
    )

    months = [
        row["month_key"]
        for row in cursor.fetchall()
        if row["month_key"]
    ]

    cursor.execute(
        """
        SELECT
            employee_id,
            full_name

        FROM employees

        WHERE
            is_active = 1
            AND role IN (
                'Staff',
                'Manager'
            )

        ORDER BY full_name
        """
    )

    employees = [
        dict(row)
        for row in cursor.fetchall()
    ]

    cursor.execute(
        """
        SELECT
            category_id,
            category_name

        FROM categories

        ORDER BY category_name
        """
    )

    categories = [
        dict(row)
        for row in cursor.fetchall()
    ]

    cursor.execute(
        """
        SELECT DISTINCT currency

        FROM claims

        WHERE
            currency IS NOT NULL
            AND currency != ''

        ORDER BY currency
        """
    )

    currencies = [
        row["currency"]
        for row in cursor.fetchall()
    ]

    conn.close()

    if "INR" not in currencies:
        currencies.insert(
            0,
            "INR"
        )

    return {
        "months": months,
        "employees": employees,
        "categories": categories,
        "currencies": currencies
    }


def _finance_filter_sql(
    month_key=None,
    employee_id=None,
    category_id=None,
    currency="INR"
):
    conditions = [
        """
        c.status IN (
            'Submitted',
            'Approved',
            'Paid'
        )
        """
    ]

    parameters = []

    if month_key:

        conditions.append(
            """
            SUBSTR(
                c.expense_date,
                1,
                7
            ) = ?
            """
        )

        parameters.append(
            month_key
        )

    if employee_id:

        conditions.append(
            "c.employee_id = ?"
        )

        parameters.append(
            employee_id
        )

    if category_id:

        conditions.append(
            "c.category_id = ?"
        )

        parameters.append(
            category_id
        )

    if currency:

        conditions.append(
            "c.currency = ?"
        )

        parameters.append(
            currency
        )

    return (
        " AND ".join(
            conditions
        ),
        parameters
    )


def get_finance_analysis(
    month_key=None,
    employee_id=None,
    category_id=None,
    currency="INR"
):
    """
    Return filtered Finance analytics.
    """

    where_sql, params = (
        _finance_filter_sql(
            month_key=month_key,
            employee_id=employee_id,
            category_id=category_id,
            currency=currency
        )
    )

    conn = get_connection()
    cursor = conn.cursor()

    # KPI summary
    cursor.execute(
        f"""
        SELECT
            COUNT(*) AS claim_count,

            COALESCE(
                SUM(c.amount),
                0
            ) AS total_claimed,

            COALESCE(
                SUM(
                    CASE
                        WHEN c.status = 'Submitted'
                        THEN c.amount
                        ELSE 0
                    END
                ),
                0
            ) AS submitted_amount,

            COALESCE(
                SUM(
                    CASE
                        WHEN c.status = 'Approved'
                        THEN c.amount
                        ELSE 0
                    END
                ),
                0
            ) AS approved_amount,

            COALESCE(
                SUM(
                    CASE
                        WHEN c.status = 'Paid'
                        THEN c.amount
                        ELSE 0
                    END
                ),
                0
            ) AS paid_amount,

            COALESCE(
                SUM(
                    CASE
                        WHEN c.limit_flag = 1
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ) AS over_limit_count,

            COALESCE(
                SUM(
                    CASE
                        WHEN c.duplicate_flag = 1
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ) AS duplicate_count

        FROM claims c

        WHERE {where_sql}
        """,
        params
    )

    summary = dict(
        cursor.fetchone()
    )

    # Category totals
    cursor.execute(
        f"""
        SELECT
            cat.category_name,

            COALESCE(
                SUM(c.amount),
                0
            ) AS total

        FROM claims c

        LEFT JOIN categories cat
            ON c.category_id = cat.category_id

        WHERE {where_sql}

        GROUP BY
            cat.category_name

        ORDER BY
            total DESC
        """,
        params
    )

    category_spend = [
        dict(row)
        for row in cursor.fetchall()
    ]

    # Employee totals
    cursor.execute(
        f"""
        SELECT
            e.employee_id,
            e.full_name,

            COALESCE(
                SUM(c.amount),
                0
            ) AS total

        FROM claims c

        JOIN employees e
            ON c.employee_id = e.employee_id

        WHERE {where_sql}

        GROUP BY
            e.employee_id,
            e.full_name

        ORDER BY
            total DESC
        """,
        params
    )

    employee_spend = [
        dict(row)
        for row in cursor.fetchall()
    ]

    # Status composition
    cursor.execute(
        f"""
        SELECT
            c.status,
            COUNT(*) AS total

        FROM claims c

        WHERE {where_sql}

        GROUP BY c.status
        """,
        params
    )

    status_counts = [
        dict(row)
        for row in cursor.fetchall()
    ]

    # If a specific month is selected,
    # show daily movement.
    if month_key:

        period_expression = (
            "c.expense_date"
        )

    else:

        period_expression = (
            "SUBSTR(c.expense_date, 1, 7)"
        )

    cursor.execute(
        f"""
        SELECT
            {period_expression} AS period,

            COALESCE(
                SUM(c.amount),
                0
            ) AS total

        FROM claims c

        WHERE {where_sql}

        GROUP BY period

        ORDER BY period
        """,
        params
    )

    trend = [
        dict(row)
        for row in cursor.fetchall()
    ]

    # Claims where monthly limits were exceeded
    cursor.execute(
        f"""
        SELECT
            c.claim_id,
            e.employee_id,
            e.full_name,
            cat.category_name,
            c.amount,
            c.currency,
            c.limit_exceeded_by

        FROM claims c

        JOIN employees e
            ON c.employee_id = e.employee_id

        LEFT JOIN categories cat
            ON c.category_id = cat.category_id

        WHERE
            {where_sql}
            AND c.limit_flag = 1

        ORDER BY
            c.limit_exceeded_by DESC
        """,
        params
    )

    limit_alerts = [
        dict(row)
        for row in cursor.fetchall()
    ]

    conn.close()

    return {
        "summary": summary,
        "category_spend": category_spend,
        "employee_spend": employee_spend,
        "status_counts": status_counts,
        "trend": trend,
        "limit_alerts": limit_alerts
    }


if __name__ == "__main__":

    report = get_limit_report(
        2026,
        9
    )

    print(
        "\nSeptember 2026 Expense Limit Report\n"
    )

    for row in report:

        # Only display categories where money
        # has actually been spent
        if row["monthly_spend"] > 0:

            print(
                row["employee_id"],
                "|",
                row["employee_name"],
                "|",
                row["category"],
                "| Spend: ₹",
                row["monthly_spend"],
                "| Limit: ₹",
                row["monthly_limit"],
                "| Used:",
                str(
                    row["percentage_used"]
                ) + "%",
                "| Over Limit:",
                row["over_limit"]
            )