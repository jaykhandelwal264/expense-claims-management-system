from datetime import datetime

from rapidfuzz import fuzz

from database.db import get_connection


def create_duplicate_check_table():
    """
    Store duplicate-check results for auditing.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS duplicate_checks (
            duplicate_check_id INTEGER PRIMARY KEY AUTOINCREMENT,

            claim_id TEXT NOT NULL,

            matched_claim_id TEXT,

            duplicate_score REAL DEFAULT 0,

            match_type TEXT,

            checked_at TEXT NOT NULL,

            FOREIGN KEY (claim_id)
                REFERENCES claims(claim_id),

            FOREIGN KEY (matched_claim_id)
                REFERENCES claims(claim_id)
        )
        """
    )

    conn.commit()
    conn.close()


def get_claim_duplicate_data(claim_id):
    """
    Get claim + receipt information needed
    for duplicate comparison.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            c.claim_id,
            c.employee_id,
            c.merchant_name,
            c.expense_date,
            c.amount,
            c.currency,
            c.status,

            r.ocr_text,
            r.file_hash,
            r.original_filename

        FROM claims c

        LEFT JOIN receipts r
            ON c.claim_id = r.claim_id

        WHERE c.claim_id = ?
        """,
        (claim_id,)
    )

    claim = cursor.fetchone()

    conn.close()

    return claim


def get_other_claims(current_claim_id):
    """
    Get all other claims having receipt information.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            c.claim_id,
            c.employee_id,
            c.merchant_name,
            c.expense_date,
            c.amount,
            c.currency,
            c.status,

            r.ocr_text,
            r.file_hash,
            r.original_filename

        FROM claims c

        JOIN receipts r
            ON c.claim_id = r.claim_id

        WHERE c.claim_id != ?
        """,
        (current_claim_id,)
    )

    claims = cursor.fetchall()

    conn.close()

    return claims


def calculate_duplicate_score(
    current_claim,
    previous_claim
):
    """
    Calculate similarity between two claims.

    Score range:
    0 to 100
    """

    # Exact same uploaded image
    if (
        current_claim["file_hash"]
        and previous_claim["file_hash"]
        and current_claim["file_hash"]
        == previous_claim["file_hash"]
    ):
        return 100.0, "Exact Image Duplicate"

    score = 0.0

    # OCR text similarity = maximum 40 points
    current_text = (
        current_claim["ocr_text"] or ""
    )

    previous_text = (
        previous_claim["ocr_text"] or ""
    )

    if current_text and previous_text:

        text_similarity = fuzz.token_set_ratio(
            current_text,
            previous_text
        )

        score += (
            text_similarity / 100
        ) * 40

    # Merchant similarity = maximum 20 points
    current_merchant = (
        current_claim["merchant_name"] or ""
    )

    previous_merchant = (
        previous_claim["merchant_name"] or ""
    )

    if (
        current_merchant
        and previous_merchant
    ):

        merchant_similarity = fuzz.ratio(
            current_merchant.lower(),
            previous_merchant.lower()
        )

        score += (
            merchant_similarity / 100
        ) * 20

    # Same amount = 25 points
    if (
        current_claim["amount"] is not None
        and previous_claim["amount"] is not None
        and current_claim["currency"]
        == previous_claim["currency"]
    ):

        amount_difference = abs(
            float(current_claim["amount"])
            - float(previous_claim["amount"])
        )

        if amount_difference < 0.01:
            score += 25

        elif amount_difference <= 1:
            score += 15

    # Same expense date = 15 points
    if (
        current_claim["expense_date"]
        and previous_claim["expense_date"]
    ):

        if (
            current_claim["expense_date"]
            == previous_claim["expense_date"]
        ):
            score += 15

    if score >= 90:
        match_type = "Very High Similarity"

    elif score >= 80:
        match_type = "Possible Duplicate"

    elif score >= 65:
        match_type = "Similar Receipt"

    else:
        match_type = "No Significant Match"

    return round(score, 2), match_type


def check_duplicate_claim(claim_id):
    """
    Compare one claim against all previously
    stored receipt claims.
    """

    create_duplicate_check_table()

    current_claim = get_claim_duplicate_data(
        claim_id
    )

    if not current_claim:
        raise ValueError(
            "Claim was not found."
        )

    if not current_claim["file_hash"]:
        raise ValueError(
            "No receipt image is linked to this claim."
        )

    previous_claims = get_other_claims(
        claim_id
    )

    best_match = None
    highest_score = 0
    best_match_type = "No Match"

    for previous_claim in previous_claims:

        score, match_type = calculate_duplicate_score(
            current_claim,
            previous_claim
        )

        if score > highest_score:

            highest_score = score
            best_match = previous_claim
            best_match_type = match_type

    duplicate_flag = (
        1
        if highest_score >= 80
        else 0
    )

    matched_claim_id = (
        best_match["claim_id"]
        if best_match
        else None
    )

    now = datetime.now().isoformat(
        sep=" ",
        timespec="seconds"
    )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE claims

        SET
            duplicate_flag = ?,
            duplicate_score = ?,
            updated_at = ?

        WHERE claim_id = ?
        """,
        (
            duplicate_flag,
            highest_score,
            now,
            claim_id
        )
    )

    cursor.execute(
        """
        INSERT INTO duplicate_checks (
            claim_id,
            matched_claim_id,
            duplicate_score,
            match_type,
            checked_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            claim_id,
            matched_claim_id,
            highest_score,
            best_match_type,
            now
        )
    )

    conn.commit()
    conn.close()

    return {
        "claim_id": claim_id,

        "is_duplicate": (
            highest_score >= 80
        ),

        "exact_duplicate": (
            highest_score == 100
        ),

        "duplicate_score": highest_score,

        "matched_claim_id": matched_claim_id,

        "match_type": best_match_type
    }


if __name__ == "__main__":

    claim_id = input(
        "Enter Claim ID to check: "
    ).strip()

    result = check_duplicate_claim(
        claim_id
    )

    print(
        "\nDuplicate Check Result\n"
    )

    print(
        "Claim ID:",
        result["claim_id"]
    )

    print(
        "Duplicate:",
        result["is_duplicate"]
    )

    print(
        "Exact Duplicate:",
        result["exact_duplicate"]
    )

    print(
        "Similarity Score:",
        result["duplicate_score"]
    )

    print(
        "Matched Claim:",
        result["matched_claim_id"]
    )

    print(
        "Match Type:",
        result["match_type"]
    )