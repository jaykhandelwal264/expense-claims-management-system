from datetime import datetime

from database.db import get_connection
import hashlib
import shutil

from pathlib import Path
from services.analytics_service import (
    check_claim_limit
)
from services.duplicate_checker import (
    check_duplicate_claim
)
from services.receipt_processor import (
    extract_text_from_receipt,
    parse_receipt
)
from datetime import datetime
from database.db import get_connection


BASE_DIR = Path(__file__).resolve().parent.parent

UPLOAD_FOLDER = (
    BASE_DIR
    / "uploads"
    / "receipts"
)

UPLOAD_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)

def get_category_id(category_name):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT category_id
        FROM categories
        WHERE category_name = ?
        """,
        (category_name,)
    )

    category = cursor.fetchone()

    conn.close()

    if category:
        return category["category_id"]

    # Fallback to Other
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT category_id
        FROM categories
        WHERE category_name = 'Other'
        """
    )

    category = cursor.fetchone()

    conn.close()

    if not category:
        raise ValueError(
            "Other category is missing from database."
        )

    return category["category_id"]

def calculate_file_hash(file_path):
    sha256 = hashlib.sha256()

    with open(
        file_path,
        "rb"
    ) as file:

        while True:

            chunk = file.read(
                8192
            )

            if not chunk:
                break

            sha256.update(
                chunk
            )

    return sha256.hexdigest()



def generate_claim_id():
    """
    Generate claim IDs like:
    CLM-20260918-0001
    CLM-20260918-0002
    """

    conn = get_connection()
    cursor = conn.cursor()

    today = datetime.now().strftime("%Y%m%d")

    cursor.execute(
        """
        SELECT claim_id
        FROM claims
        WHERE claim_id LIKE ?
        ORDER BY claim_id DESC
        LIMIT 1
        """,
        (f"CLM-{today}-%",)
    )

    last_claim = cursor.fetchone()

    if last_claim:
        last_number = int(
            last_claim["claim_id"].split("-")[-1]
        )
        next_number = last_number + 1
    else:
        next_number = 1

    conn.close()

    return f"CLM-{today}-{next_number:04d}"


def get_employee(employee_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM employees
        WHERE employee_id = ?
        AND is_active = 1
        """,
        (employee_id,)
    )

    employee = cursor.fetchone()

    conn.close()

    return employee


def get_approver(employee_id):
    """
    Find the employee's immediate higher-level manager.
    """

    employee = get_employee(employee_id)

    if not employee:
        raise ValueError(
            f"Employee {employee_id} was not found."
        )

    approver_id = employee["reports_to"]

    if not approver_id:
        raise ValueError(
            f"No approver is configured for {employee['full_name']}."
        )

    # Extra safety:
    # nobody can approve their own claim
    if approver_id == employee_id:
        raise ValueError(
            "An employee cannot approve their own claim."
        )

    approver = get_employee(approver_id)

    if not approver:
        raise ValueError(
            "Configured approver does not exist or is inactive."
        )

    return approver


def create_claim(
    employee_id,
    merchant_name,
    expense_date,
    amount,
    category_id,
    description="",
    currency="INR"
):
    employee = get_employee(
        employee_id
    )

    if not employee:
        raise ValueError(
            "Employee was not found."
        )

    approver = get_approver(
        employee_id
    )

    try:
        amount = float(
            amount
        )

    except (
        TypeError,
        ValueError
    ):
        raise ValueError(
            "Claim amount must be a valid number."
        )

    if amount <= 0:
        raise ValueError(
            "Claim amount must be greater than zero."
        )

    claim_id = generate_claim_id()

    now = datetime.now().isoformat(
        sep=" ",
        timespec="seconds"
    )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO claims (
            claim_id,
            employee_id,
            approver_id,
            merchant_name,
            expense_date,
            amount,
            currency,
            category_id,
            description,
            status,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            claim_id,
            employee_id,
            approver["employee_id"],
            merchant_name,
            expense_date,
            amount,
            currency,
            category_id,
            description,
            "Draft",
            now,
            now
        )
    )

    conn.commit()
    conn.close()

    return claim_id

def get_employee_claims(employee_id):
    """
    Return all claims belonging to one employee.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            c.claim_id,
            c.expense_date,
            c.merchant_name,
            c.amount,
            c.currency,
            cat.category_name,
            c.status,
            c.created_at

        FROM claims c

        LEFT JOIN categories cat
            ON c.category_id = cat.category_id

        WHERE c.employee_id = ?

        ORDER BY c.created_at DESC
        """,
        (employee_id,)
    )

    claims = cursor.fetchall()

    conn.close()

    return claims


def get_employee_unpaid_claims(employee_id):
    """
    Return submitted or approved claims
    which have not yet been paid.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            c.claim_id,
            c.expense_date,
            c.merchant_name,
            c.amount,
            c.currency,
            cat.category_name,
            c.status,
            c.submitted_at

        FROM claims c

        LEFT JOIN categories cat
            ON c.category_id = cat.category_id

        WHERE
            c.employee_id = ?
            AND c.status IN (
                'Submitted',
                'Approved'
            )

        ORDER BY
            c.submitted_at DESC
        """,
        (employee_id,)
    )

    claims = cursor.fetchall()

    conn.close()

    return claims

def create_claim_from_receipt(
    employee_id,
    image_path
):
    """
    Convert one receipt image into one Draft claim.
    """

    image_path = Path(
        image_path
    )

    if not image_path.exists():
        raise FileNotFoundError(
            f"Receipt image not found: {image_path}"
        )

    # OCR
    ocr_text = extract_text_from_receipt(
        str(image_path)
    )

    # Structured information
    parsed = parse_receipt(
        ocr_text
    )

    # We need minimum information before
    # creating a database claim
    if not parsed["expense_date"]:
        raise ValueError(
            "Receipt date could not be detected. "
            "User correction will be required before claim creation."
        )

    if parsed["amount"] is None:
        raise ValueError(
            "Receipt amount could not be detected. "
            "User correction will be required before claim creation."
        )

    category_id = get_category_id(
        parsed["category"]
    )

    claim_id = create_claim(
        employee_id=employee_id,
        merchant_name=parsed["merchant"],
        expense_date=parsed["expense_date"],
        amount=parsed["amount"],
        category_id=category_id,
        description="Created from uploaded receipt",
        currency=parsed["currency"]
    )

    # Preserve original file extension
    extension = image_path.suffix.lower()

    saved_filename = (
        f"{claim_id}{extension}"
    )

    saved_path = (
        UPLOAD_FOLDER
        / saved_filename
    )

    shutil.copy2(
        image_path,
        saved_path
    )

    file_hash = calculate_file_hash(
        saved_path
    )

    now = datetime.now().isoformat(
        sep=" ",
        timespec="seconds"
    )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO receipts (
            claim_id,
            image_path,
            original_filename,
            ocr_text,
            file_hash,
            uploaded_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            claim_id,
            str(saved_path),
            image_path.name,
            ocr_text,
            file_hash,
            now
        )
    )

    conn.commit()
    conn.close()

    return {
        "claim_id": claim_id,
        "employee_id": employee_id,
        "merchant": parsed["merchant"],
        "expense_date": parsed["expense_date"],
        "amount": parsed["amount"],
        "currency": parsed["currency"],
        "category": parsed["category"],
        "needs_review": parsed[
            "needs_review"
        ],
        "review_reasons": parsed[
            "review_reasons"
        ],
        "receipt_path": str(
            saved_path
        )
    }

def get_claim(claim_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            c.claim_id,
            c.employee_id,
            e.full_name AS employee_name,

            c.approver_id,
            a.full_name AS approver_name,

            c.merchant_name,
            c.expense_date,
            c.amount,
            c.currency,
            cat.category_name,

            c.description,
            c.status,
            c.duplicate_flag,
            c.duplicate_score,
            
            c.created_at

        FROM claims c

        JOIN employees e
            ON c.employee_id = e.employee_id

        LEFT JOIN employees a
            ON c.approver_id = a.employee_id

        LEFT JOIN categories cat
            ON c.category_id = cat.category_id

        WHERE c.claim_id = ?
        """,
        (claim_id,)
    )

    claim = cursor.fetchone()

    conn.close()

    return claim


def submit_claim(claim_id, employee_id):
    """
    Submit a Draft claim for manager approval.

    Rules:
    - Only the claim owner can submit it.
    - Only Draft claims can be submitted.
    - Required claim information must be valid.
    - Exact duplicate receipts are blocked.
    - Possible duplicates are flagged.
    - Monthly expense limits are checked.
    - Going over a monthly limit does not block submission.
    """

    # Get the claim
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
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

    # Employee can submit only their own claim
    if claim["employee_id"] != employee_id:
        raise PermissionError(
            "You cannot submit another employee's claim."
        )

    # Only Draft claims can be submitted
    if claim["status"] != "Draft":
        raise ValueError(
            "Only Draft claims can be submitted."
        )

    # Validate merchant, date, amount, category, etc.
    validate_claim_before_submission(
        claim_id,
        employee_id
    )

    # Check for duplicate receipts
    duplicate_result = check_duplicate_claim(
        claim_id
    )

    # Exact receipt duplicate is blocked
    if duplicate_result["exact_duplicate"]:
        raise ValueError(
            "Submission blocked: this exact receipt "
            "has already been used in claim "
            f"{duplicate_result['matched_claim_id']}."
        )

    # Check monthly category limit
    limit_result = check_claim_limit(
        claim_id
    )

    now = datetime.now().isoformat(
        sep=" ",
        timespec="seconds"
    )

    # Prepare monthly limit values
    limit_flag = (
        1
        if limit_result["limit_exceeded"]
        else 0
    )

    limit_exceeded_by = (
        limit_result["exceeded_by"]
    )

    conn = get_connection()
    cursor = conn.cursor()

    # Submit the claim and store limit warning
    cursor.execute(
        """
        UPDATE claims

        SET
            status = 'Submitted',
            submitted_at = ?,
            limit_flag = ?,
            limit_exceeded_by = ?,
            updated_at = ?

        WHERE
            claim_id = ?
            AND employee_id = ?
            AND status = 'Draft'
        """,
        (
            now,
            limit_flag,
            limit_exceeded_by,
            now,
            claim_id,
            employee_id
        )
    )

    if cursor.rowcount == 0:
        conn.rollback()
        conn.close()

        raise ValueError(
            "Claim could not be submitted. "
            "Its status may have changed."
        )

    # Build audit/history remarks
    remarks_parts = [
        "Claim submitted for manager approval."
    ]

    # Possible duplicate warning
    if duplicate_result["is_duplicate"]:
        remarks_parts.append(
            "Possible duplicate detected with "
            f"{duplicate_result['matched_claim_id']} "
            f"(similarity "
            f"{duplicate_result['duplicate_score']}%)."
        )

    # Monthly limit warning
    if limit_result["foreign_currency"]:
        remarks_parts.append(
            "Foreign-currency expense requires "
            "Finance review for monthly limit analysis."
        )

    elif limit_result["limit_exceeded"]:
        remarks_parts.append(
            "Monthly category limit exceeded by "
            f"INR {limit_result['exceeded_by']:.2f}."
        )

    elif limit_result["near_limit"]:
        remarks_parts.append(
            "Employee is close to the monthly "
            f"category limit "
            f"({limit_result['percentage_used']:.2f}% used)."
        )

    remarks = " ".join(
        remarks_parts
    )

    # Save audit trail
    cursor.execute(
        """
        INSERT INTO claim_history (
            claim_id,
            changed_by,
            old_status,
            new_status,
            remarks,
            changed_at
        )

        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            claim_id,
            employee_id,
            "Draft",
            "Submitted",
            remarks,
            now
        )
    )

    conn.commit()
    conn.close()

    return {
        "claim_id": claim_id,
        "status": "Submitted",

        "possible_duplicate":
            duplicate_result["is_duplicate"],

        "duplicate_score":
            duplicate_result["duplicate_score"],

        "matched_claim_id":
            duplicate_result["matched_claim_id"],

        "limit_flag":
            bool(limit_flag),

        "monthly_limit":
            limit_result["monthly_limit"],

        "current_spend":
            limit_result["current_spend"],

        "projected_spend":
            limit_result["projected_spend"],

        "percentage_used":
            limit_result["percentage_used"],

        "near_limit":
            limit_result["near_limit"],

        "limit_exceeded":
            limit_result["limit_exceeded"],

        "limit_exceeded_by":
            limit_result["exceeded_by"],

        "foreign_currency":
            limit_result["foreign_currency"]
    }

def show_claim(claim_id):
    claim = get_claim(claim_id)

    if not claim:
        print("Claim not found.")
        return

    print("\nClaim Details\n")

    print("Claim ID:", claim["claim_id"])
    print(
        "Employee:",
        claim["employee_id"],
        "-",
        claim["employee_name"]
    )

    print(
        "Approver:",
        claim["approver_id"],
        "-",
        claim["approver_name"]
    )

    print("Merchant:", claim["merchant_name"])
    print("Expense Date:", claim["expense_date"])
    print(
    "Amount:",
    claim["currency"],
    claim["amount"]
)
    print("Category:", claim["category_name"])
    print("Status:", claim["status"])

def approve_claim(claim_id, manager_id, remarks="Approved"):
    """
    Approve a submitted claim.

    Only the assigned approver can approve.
    Nobody can approve their own claim.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM claims
        WHERE claim_id = ?
        """,
        (claim_id,)
    )

    claim = cursor.fetchone()

    if not claim:
        conn.close()
        raise ValueError("Claim was not found.")

    if claim["status"] != "Submitted":
        conn.close()
        raise ValueError(
            "Only Submitted claims can be approved."
        )

    if claim["employee_id"] == manager_id:
        conn.close()
        raise PermissionError(
            "A manager cannot approve their own claim."
        )

    if claim["approver_id"] != manager_id:
        conn.close()
        raise PermissionError(
            "This claim is not assigned to this manager."
        )

    manager = get_employee(manager_id)

    if not manager:
        conn.close()
        raise ValueError("Manager was not found.")

    if manager["role"] != "Manager":
        conn.close()
        raise PermissionError(
            "Only managers can approve claims."
        )

    now = datetime.now().isoformat(
        sep=" ",
        timespec="seconds"
    )

    cursor.execute(
        """
        UPDATE claims

        SET
            status = 'Approved',
            approved_at = ?,
            updated_at = ?

        WHERE claim_id = ?
        """,
        (
            now,
            now,
            claim_id
        )
    )

    cursor.execute(
        """
        INSERT INTO claim_history (
            claim_id,
            changed_by,
            old_status,
            new_status,
            remarks,
            changed_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            claim_id,
            manager_id,
            "Submitted",
            "Approved",
            remarks,
            now
        )
    )

    conn.commit()
    conn.close()

def save_reviewed_receipt_draft(
    employee_id,
    image_path,
    merchant_name,
    expense_date,
    amount,
    currency,
    category_name,
    description="",
    ocr_text=""
):
    """
    Create one Draft claim from a receipt after
    the employee has reviewed/corrected OCR values.
    """

    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(
            f"Receipt image not found: {image_path}"
        )

    category_id = get_category_id(
        category_name
    )

    claim_id = create_claim(
        employee_id=employee_id,
        merchant_name=merchant_name,
        expense_date=expense_date,
        amount=amount,
        category_id=category_id,
        description=description,
        currency=currency
    )

    extension = image_path.suffix.lower()

    saved_filename = (
        f"{claim_id}{extension}"
    )

    saved_path = (
        UPLOAD_FOLDER
        / saved_filename
    )

    shutil.copy2(
        image_path,
        saved_path
    )

    file_hash = calculate_file_hash(
        saved_path
    )

    now = datetime.now().isoformat(
        sep=" ",
        timespec="seconds"
    )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO receipts (
            claim_id,
            image_path,
            original_filename,
            ocr_text,
            file_hash,
            uploaded_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            claim_id,
            str(saved_path),
            image_path.name,
            ocr_text,
            file_hash,
            now
        )
    )

    conn.commit()
    conn.close()

    return claim_id


def get_employee_claims(employee_id):
    """
    Return all claims belonging to one employee.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            c.claim_id,
            c.expense_date,
            c.merchant_name,
            c.amount,
            c.currency,
            cat.category_name,
            c.status,
            c.created_at

        FROM claims c

        LEFT JOIN categories cat
            ON c.category_id = cat.category_id

        WHERE c.employee_id = ?

        ORDER BY c.created_at DESC
        """,
        (employee_id,)
    )

    claims = cursor.fetchall()

    conn.close()

    return claims


def get_employee_unpaid_claims(employee_id):
    """
    Claims already filed but not yet reimbursed.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            c.claim_id,
            c.expense_date,
            c.merchant_name,
            c.amount,
            c.currency,
            cat.category_name,
            c.status

        FROM claims c

        LEFT JOIN categories cat
            ON c.category_id = cat.category_id

        WHERE
            c.employee_id = ?
            AND c.status IN (
                'Submitted',
                'Approved'
            )

        ORDER BY c.expense_date DESC
        """,
        (employee_id,)
    )

    claims = cursor.fetchall()

    conn.close()

    return claims

def reject_claim(claim_id, manager_id, remarks):
    """
    Reject a submitted claim.

    Only the assigned manager can reject it.
    """

    if not remarks.strip():
        raise ValueError(
            "Rejection remarks are required."
        )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM claims
        WHERE claim_id = ?
        """,
        (claim_id,)
    )

    claim = cursor.fetchone()

    if not claim:
        conn.close()
        raise ValueError("Claim was not found.")

    if claim["status"] != "Submitted":
        conn.close()
        raise ValueError(
            "Only Submitted claims can be rejected."
        )

    if claim["employee_id"] == manager_id:
        conn.close()
        raise PermissionError(
            "A manager cannot review their own claim."
        )

    if claim["approver_id"] != manager_id:
        conn.close()
        raise PermissionError(
            "This claim is not assigned to this manager."
        )

    manager = get_employee(manager_id)

    if not manager:
        conn.close()
        raise ValueError("Manager was not found.")

    if manager["role"] != "Manager":
        conn.close()
        raise PermissionError(
            "Only managers can reject claims."
        )

    now = datetime.now().isoformat(
        sep=" ",
        timespec="seconds"
    )

    cursor.execute(
        """
        UPDATE claims

        SET
            status = 'Rejected',
            rejected_at = ?,
            updated_at = ?

        WHERE claim_id = ?
        """,
        (
            now,
            now,
            claim_id
        )
    )

    cursor.execute(
        """
        INSERT INTO claim_history (
            claim_id,
            changed_by,
            old_status,
            new_status,
            remarks,
            changed_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            claim_id,
            manager_id,
            "Submitted",
            "Rejected",
            remarks,
            now
        )
    )

    conn.commit()
    conn.close()


def get_manager_pending_claims(manager_id):
    """
    Return all Submitted claims assigned
    to a particular manager.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            c.claim_id,
            c.employee_id,
            e.full_name AS employee_name,
            c.merchant_name,
            c.expense_date,
            c.amount,
            cat.category_name,
            c.description,
            c.status

        FROM claims c

        JOIN employees e
            ON c.employee_id = e.employee_id

        LEFT JOIN categories cat
            ON c.category_id = cat.category_id

        WHERE
            c.approver_id = ?
            AND c.status = 'Submitted'

        ORDER BY
            c.submitted_at ASC
        """,
        (manager_id,)
    )

    claims = cursor.fetchall()

    conn.close()

    return claims

def get_finance_approved_claims():
    """
    Claims approved by managers and waiting
    for Finance payment.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            c.claim_id,
            c.employee_id,
            e.full_name AS employee_name,

            c.merchant_name,
            c.expense_date,
            c.amount,
            c.currency,

            cat.category_name,

            c.approver_id,
            a.full_name AS approver_name,

            c.status,
            c.approved_at,

            c.duplicate_flag,
            c.duplicate_score,

            c.limit_flag,
            c.limit_exceeded_by

        FROM claims c

        JOIN employees e
            ON c.employee_id = e.employee_id

        LEFT JOIN employees a
            ON c.approver_id = a.employee_id

        LEFT JOIN categories cat
            ON c.category_id = cat.category_id

        WHERE c.status = 'Approved'

        ORDER BY
            c.approved_at ASC
        """
    )

    claims = cursor.fetchall()

    conn.close()

    return claims

def get_finance_paid_claims():
    """
    Return completed Finance payments.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            c.claim_id,
            c.employee_id,
            e.full_name AS employee_name,

            c.merchant_name,
            c.expense_date,
            c.amount,
            c.currency,

            cat.category_name,

            c.paid_at,
            c.paid_by,

            f.full_name AS finance_name

        FROM claims c

        JOIN employees e
            ON c.employee_id = e.employee_id

        LEFT JOIN categories cat
            ON c.category_id = cat.category_id

        LEFT JOIN employees f
            ON c.paid_by = f.employee_id

        WHERE c.status = 'Paid'

        ORDER BY
            c.paid_at DESC
        """
    )

    claims = cursor.fetchall()

    conn.close()

    return claims


def get_claim_receipt_path(claim_id):
    """
    Return the receipt image belonging to a claim.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            image_path
        FROM receipts
        WHERE claim_id = ?
        """,
        (claim_id,)
    )

    receipt = cursor.fetchone()

    conn.close()

    if not receipt:
        return None

    return receipt["image_path"]

def mark_claim_paid(claim_id, finance_employee_id):
    """
    Mark an approved claim as Paid.

    Only a Finance user can perform payment.
    Paid claims cannot move backwards.
    """

    finance_user = get_employee(finance_employee_id)

    if not finance_user:
        raise ValueError(
            "Finance employee was not found."
        )

    if finance_user["role"] != "Finance":
        raise PermissionError(
            "Only Finance users can mark claims as paid."
        )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM claims
        WHERE claim_id = ?
        """,
        (claim_id,)
    )

    claim = cursor.fetchone()

    if not claim:
        conn.close()
        raise ValueError(
            "Claim was not found."
        )

    if claim["status"] == "Paid":
        conn.close()
        raise ValueError(
            "This claim has already been paid."
        )

    if claim["status"] != "Approved":
        conn.close()
        raise ValueError(
            "Only Approved claims can be paid."
        )

    now = datetime.now().isoformat(
        sep=" ",
        timespec="seconds"
    )

    cursor.execute(
        """
        UPDATE claims

        SET
            status = 'Paid',
            paid_at = ?,
            paid_by = ?,
            updated_at = ?

        WHERE claim_id = ?
        """,
        (
            now,
            finance_employee_id,
            now,
            claim_id
        )
    )

    cursor.execute(
        """
        INSERT INTO claim_history (
            claim_id,
            changed_by,
            old_status,
            new_status,
            remarks,
            changed_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            claim_id,
            finance_employee_id,
            "Approved",
            "Paid",
            "Expense reimbursement paid by Finance",
            now
        )
    )

    conn.commit()
    conn.close()


def get_categories():
    """
    Return all available expense categories.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            category_id,
            category_name,
            default_monthly_limit
        FROM categories
        ORDER BY category_name
        """
    )

    categories = cursor.fetchall()

    conn.close()

    return categories


def get_latest_draft_claim(employee_id):
    """
    Return the most recently created Draft claim
    for an employee.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT claim_id
        FROM claims
        WHERE
            employee_id = ?
            AND status = 'Draft'
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (employee_id,)
    )

    result = cursor.fetchone()

    conn.close()

    if result:
        return result["claim_id"]

    return None


def update_draft_claim(
    claim_id,
    employee_id,
    merchant_name,
    expense_date,
    amount,
    category_name,
    currency="INR",
    description=""
):
    """
    Allow an employee to correct OCR-extracted data.

    Only Draft claims can be edited.
    Employees can edit only their own claims.
    """

    merchant_name = merchant_name.strip()
    category_name = category_name.strip()
    currency = currency.strip().upper()

    if not merchant_name:
        raise ValueError(
            "Merchant name is required."
        )

    try:
        parsed_date = datetime.strptime(
            expense_date,
            "%Y-%m-%d"
        )

        expense_date = parsed_date.strftime(
            "%Y-%m-%d"
        )

    except ValueError:
        raise ValueError(
            "Expense date must be in YYYY-MM-DD format."
        )

    try:
        amount = float(amount)

    except (TypeError, ValueError):
        raise ValueError(
            "Amount must be a valid number."
        )

    if amount <= 0:
        raise ValueError(
            "Amount must be greater than zero."
        )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM claims
        WHERE claim_id = ?
        """,
        (claim_id,)
    )

    claim = cursor.fetchone()

    if not claim:
        conn.close()
        raise ValueError(
            "Claim was not found."
        )

    if claim["employee_id"] != employee_id:
        conn.close()
        raise PermissionError(
            "You cannot edit another employee's claim."
        )

    if claim["status"] != "Draft":
        conn.close()
        raise ValueError(
            "Only Draft claims can be edited."
        )

    cursor.execute(
        """
        SELECT category_id
        FROM categories
        WHERE category_name = ?
        """,
        (category_name,)
    )

    category = cursor.fetchone()

    if not category:
        conn.close()
        raise ValueError(
            f"Unknown category: {category_name}"
        )

    now = datetime.now().isoformat(
        sep=" ",
        timespec="seconds"
    )

    cursor.execute(
        """
        UPDATE claims

        SET
            merchant_name = ?,
            expense_date = ?,
            amount = ?,
            currency = ?,
            category_id = ?,
            description = ?,
            updated_at = ?

        WHERE claim_id = ?
        """,
        (
            merchant_name,
            expense_date,
            amount,
            currency,
            category["category_id"],
            description,
            now,
            claim_id
        )
    )

    conn.commit()
    conn.close()


def validate_claim_before_submission(
    claim_id,
    employee_id
):
    """
    Check that the Draft claim has enough
    information before sending it to manager.
    """

    claim = get_claim(
        claim_id
    )

    if not claim:
        raise ValueError(
            "Claim was not found."
        )

    if claim["employee_id"] != employee_id:
        raise PermissionError(
            "This claim does not belong to you."
        )

    if claim["status"] != "Draft":
        raise ValueError(
            "Only Draft claims can be submitted."
        )

    errors = []

    if not claim["merchant_name"]:
        errors.append(
            "Merchant is missing."
        )

    if (
        claim["merchant_name"]
        == "Unknown Merchant"
    ):
        errors.append(
            "Merchant must be reviewed."
        )

    if not claim["expense_date"]:
        errors.append(
            "Expense date is missing."
        )

    if (
        claim["amount"] is None
        or claim["amount"] <= 0
    ):
        errors.append(
            "A valid amount is required."
        )

    if not claim["category_name"]:
        errors.append(
            "Expense category is missing."
        )

    if errors:
        raise ValueError(
            "\n".join(errors)
        )

    return True


# if __name__ == "__main__":

#     claim_id = create_claim(
#         employee_id="EMP001",
#         merchant_name="Uber India",
#         expense_date="2026-09-18",
#         amount=385,
#         category_id=1,
#         description="Auto/cab travel to client office"
#     )

#     print(
#         "\nCreated Claim:",
#         claim_id
#     )

#     submit_claim(
#         claim_id,
#         "EMP001"
#     )

#     show_claim(claim_id)


# if __name__ == "__main__":

#     manager_id = "EMP003"

#     pending_claims = get_manager_pending_claims(
#         manager_id
#     )

#     print("\nPending Claims for Manager\n")

#     for claim in pending_claims:
#         print(
#             claim["claim_id"],
#             "|",
#             claim["employee_name"],
#             "| ₹",
#             claim["amount"],
#             "|",
#             claim["category_name"]
#         )

#     if pending_claims:
#         claim_id = pending_claims[0]["claim_id"]

#         approve_claim(
#             claim_id=claim_id,
#             manager_id=manager_id,
#             remarks="Receipt and expense details verified."
#         )

#         print(
#             "\nApproved Claim:",
#             claim_id
#         )

#         show_claim(claim_id)


# if __name__ == "__main__":

#     manager_id = "EMP003"

#     pending_claims = get_manager_pending_claims(
#         manager_id
#     )

#     print("\nPending Claims for Vikram Singh\n")

#     for claim in pending_claims:
#         print(
#             claim["claim_id"],
#             "|",
#             claim["employee_name"],
#             "| ₹",
#             claim["amount"],
#             "|",
#             claim["category_name"],
#             "|",
#             claim["status"]
#         )

#     if pending_claims:

#         claim_id = pending_claims[0]["claim_id"]

#         approve_claim(
#             claim_id=claim_id,
#             manager_id=manager_id,
#             remarks="Receipt and expense details verified."
#         )

#         print(
#             "\nManager approved:",
#             claim_id
#         )

#         show_claim(claim_id)

#     else:
#         print("No pending claims found.")


# if __name__ == "__main__":

#     finance_id = "FIN001"

#     approved_claims = get_finance_approved_claims()

#     print("\nClaims Waiting for Finance Payment\n")

#     for claim in approved_claims:

#         print(
#             claim["claim_id"],
#             "|",
#             claim["employee_name"],
#             "| ₹",
#             claim["amount"],
#             "|",
#             claim["category_name"],
#             "| Approved By:",
#             claim["approver_name"]
#         )

#     if approved_claims:

#         claim_id = approved_claims[0]["claim_id"]

#         mark_claim_paid(
#             claim_id=claim_id,
#             finance_employee_id=finance_id
#         )

#         print(
#             "\nFinance Paid Claim:",
#             claim_id
#         )

#         show_claim(claim_id)

#     else:
#         print("No approved claims waiting for payment.")

if __name__ == "__main__":

    employee_id = "EMP001"

    claim_id = get_latest_draft_claim(
        employee_id
    )

    if not claim_id:

        print(
            "No Draft claim found."
        )

    else:

        print(
            "\nDraft Before Correction\n"
        )

        show_claim(
            claim_id
        )

        update_draft_claim(
            claim_id=claim_id,
            employee_id=employee_id,

            merchant_name=(
                "PT Kledo Berhati Nyaman"
            ),

            expense_date="2022-02-18",

            amount=170145,

            currency="IDR",

            category_name="Other",

            description=(
                "Business purchase - "
                "details verified from invoice"
            )
        )

        print(
            "\nDraft After Employee Correction\n"
        )

        show_claim(
            claim_id
        )