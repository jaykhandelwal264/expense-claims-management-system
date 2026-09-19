import os
import re
import cv2
import pytesseract

from datetime import datetime
from decimal import Decimal


pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def preprocess_receipt(image_path):
    image = cv2.imread(image_path)

    if image is None:
        raise FileNotFoundError(
            f"Could not read image: {image_path}"
        )

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    gray = cv2.GaussianBlur(
        gray,
        (3, 3),
        0
    )

    processed = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        15
    )

    return processed


def extract_text_from_receipt(image_path):
    processed_image = preprocess_receipt(
        image_path
    )

    text = pytesseract.image_to_string(
        processed_image,
        config="--psm 6"
    )

    return text.strip()


def clean_lines(text):
    lines = []

    for line in text.splitlines():

        line = line.strip()

        if len(line) >= 2:
            lines.append(line)

    return lines


# def extract_date(text):
#     patterns = [
#         r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b",
#         r"\b(\d{1,2})-(\d{1,2})-(\d{4})\b",
#         r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b"
#     ]

#     for index, pattern in enumerate(patterns):

#         match = re.search(
#             pattern,
#             text
#         )

#         if not match:
#             continue

#         try:

#             if index in (0, 1):

#                 month = int(match.group(1))
#                 day = int(match.group(2))
#                 year = int(match.group(3))

#             else:

#                 year = int(match.group(1))
#                 month = int(match.group(2))
#                 day = int(match.group(3))

#             parsed_date = datetime(
#                 year,
#                 month,
#                 day
#             )

#             return parsed_date.strftime(
#                 "%Y-%m-%d"
#             )

#         except ValueError:
#             continue

#     return None


def extract_date(text):
    """
    Extract receipt/invoice date.

    Supports:
    DD/MM/YYYY
    MM/DD/YYYY
    YYYY-MM-DD
    """

    # ISO format
    iso_match = re.search(
        r"\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b",
        text
    )

    if iso_match:
        try:
            year = int(iso_match.group(1))
            month = int(iso_match.group(2))
            day = int(iso_match.group(3))

            return datetime(
                year,
                month,
                day
            ).strftime("%Y-%m-%d")

        except ValueError:
            pass

    # DD/MM/YYYY or MM/DD/YYYY
    matches = re.findall(
        r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b",
        text
    )

    for first, second, year in matches:

        first = int(first)
        second = int(second)
        year = int(year)

        try:

            # 18/02/2022 → definitely DD/MM/YYYY
            if first > 12 and second <= 12:

                day = first
                month = second

            # 02/18/2022 → definitely MM/DD/YYYY
            elif second > 12 and first <= 12:

                month = first
                day = second

            else:
                # Ambiguous date such as 05/06/2022
                # Default to day-first for our receipt processing
                day = first
                month = second

            parsed = datetime(
                year,
                month,
                day
            )

            return parsed.strftime(
                "%Y-%m-%d"
            )

        except ValueError:
            continue

    return None

# def extract_money_from_line(line):
#     values = re.findall(
#         r"(?:₹|\$|Rs\.?|INR)?\s*"
#         r"(\d{1,6}(?:[,.]\d{2}))",
#         line,
#         flags=re.IGNORECASE
#     )

#     amounts = []

#     for value in values:

#         value = value.replace(",", "")

#         try:
#             amounts.append(
#                 Decimal(value)
#             )

#         except Exception:
#             continue

#     return amounts

def extract_money_from_line(
    line,
    currency="Unknown"
):
    """
    Extract numeric monetary values.

    Handles:
    170.145 IDR -> 170145
    1,250.50 -> 1250.50
    1250.50 -> 1250.50
    """

    values = re.findall(
        r"\d[\d.,]*",
        line
    )

    amounts = []

    for value in values:

        value = value.strip(
            ".,"
        )

        if not value:
            continue

        try:

            # Indonesian format:
            # Rp 170.145 = 170145
            if currency == "IDR":

                if re.fullmatch(
                    r"\d{1,3}(?:\.\d{3})+",
                    value
                ):
                    value = value.replace(
                        ".",
                        ""
                    )

                elif re.fullmatch(
                    r"\d{1,3}(?:,\d{3})+",
                    value
                ):
                    value = value.replace(
                        ",",
                        ""
                    )

            else:

                # 1,250.50
                if (
                    "," in value
                    and "." in value
                ):

                    if (
                        value.rfind(".")
                        > value.rfind(",")
                    ):
                        value = value.replace(
                            ",",
                            ""
                        )

                    else:
                        value = (
                            value
                            .replace(".", "")
                            .replace(",", ".")
                        )

                # 1,250
                elif "," in value:

                    parts = value.split(",")

                    if (
                        len(parts[-1]) == 3
                    ):
                        value = value.replace(
                            ",",
                            ""
                        )

                    elif (
                        len(parts[-1]) == 2
                    ):
                        value = value.replace(
                            ",",
                            "."
                        )

            amounts.append(
                Decimal(value)
            )

        except Exception:
            continue

    return amounts

def detect_currency(text):

    if re.search(
        r"\bRp\b",
        text,
        re.IGNORECASE
    ):
        return "IDR"

    if (
        "₹" in text
        or re.search(
            r"\bINR\b",
            text,
            re.IGNORECASE
        )
        or re.search(
            r"\bRs\.?\b",
            text,
            re.IGNORECASE
        )
    ):
        return "INR"

    if "$" in text:
        return "USD"

    if "€" in text:
        return "EUR"

    if "£" in text:
        return "GBP"

    return "Unknown"

# def extract_amount(text):
#     lines = clean_lines(text)

#     total_keywords = [
#         "grand total",
#         "amount due",
#         "total due",
#         "net total",
#         "bill total",
#         "total amount"
#     ]

#     # First look for an explicit final total
#     for line in lines:

#         lower_line = line.lower()

#         if "subtotal" in lower_line:
#             continue

#         if any(
#             keyword in lower_line
#             for keyword in total_keywords
#         ):

#             amounts = extract_money_from_line(
#                 line
#             )

#             if amounts:

#                 return (
#                     float(amounts[-1]),
#                     "receipt_total",
#                     False
#                 )

    # # Handle lines beginning simply with TOTAL
    # for line in lines:

    #     lower_line = line.lower().strip()

    #     if re.match(
    #         r"^total\b",
    #         lower_line
    #     ):

    #         if "subtotal" in lower_line:
    #             continue

    #         amounts = extract_money_from_line(
    #             line
    #         )

    #         if amounts:

    #             return (
    #                 float(amounts[-1]),
    #                 "receipt_total",
    #                 False
    #             )

    # subtotal = None
    # tax = None

    # # Find subtotal and tax separately
    # for line in lines:

    #     lower_line = line.lower()

    #     amounts = extract_money_from_line(
    #         line
    #     )

    #     if not amounts:
    #         continue

    #     if (
    #         "sub total" in lower_line
    #         or "subtotal" in lower_line
    #     ):
    #         subtotal = amounts[-1]

    #     elif re.search(
    #         r"\btax\b",
    #         lower_line
    #     ):
    #         tax = amounts[-1]

    # # If total is missing, infer it but require review
    # if (
    #     subtotal is not None
    #     and tax is not None
    # ):

    #     inferred_total = (
    #         subtotal + tax
    #     )

    #     return (
    #         float(inferred_total),
    #         "subtotal_plus_tax",
    #         True
    #     )

    # if subtotal is not None:

    #     return (
    #         float(subtotal),
    #         "subtotal_only",
    #         True
    #     )

    # return (
    #     None,
    #     "not_found",
    #     True
    # )

def extract_amount(text):
    lines = clean_lines(text)

    currency = detect_currency(
        text
    )

    total_keywords = [
        "grand total",
        "amount due",
        "total due",
        "net total",
        "bill total",
        "total amount",
        "total"
    ]

    for index, line in enumerate(lines):

        lower_line = line.lower().strip()

        # Don't mistake subtotal for final total
        if (
            "subtotal" in lower_line
            or "sub total" in lower_line
        ):
            continue

        if any(
            keyword in lower_line
            for keyword in total_keywords
        ):

            # Check current line first
            amounts = extract_money_from_line(
                line,
                currency
            )

            if amounts:

                return (
                    float(amounts[-1]),
                    "receipt_total",
                    False
                )

            # Total may be printed on the following line
            for next_index in range(
                index + 1,
                min(index + 3, len(lines))
            ):

                amounts = extract_money_from_line(
                    lines[next_index],
                    currency
                )

                if amounts:

                    return (
                        float(amounts[-1]),
                        "receipt_total",
                        False
                    )

    subtotal = None
    tax = None

    for line in lines:

        lower_line = line.lower()

        amounts = extract_money_from_line(
            line,
            currency
        )

        if not amounts:
            continue

        if (
            "subtotal" in lower_line
            or "sub total" in lower_line
        ):

            subtotal = amounts[-1]

        elif re.search(
            r"\btax\b",
            lower_line
        ):

            tax = amounts[-1]

    if (
        subtotal is not None
        and tax is not None
    ):

        return (
            float(
                subtotal + tax
            ),
            "subtotal_plus_tax",
            True
        )

    if subtotal is not None:

        return (
            float(subtotal),
            "subtotal_only",
            True
        )

    return (
        None,
        "not_found",
        True
    )


# def extract_merchant(text):
#     lines = clean_lines(text)

#     ignored_words = [
#         "thank you",
#         "server",
#         "order",
#         "table",
#         "guest",
#         "subtotal",
#         "sub total",
#         "total",
#         "tax",
#         "cash",
#         "visa",
#         "mastercard",
#         "receipt",
#         "invoice"
#     ]

#     for line in lines[:10]:

#         lower_line = line.lower()

#         if any(
#             word in lower_line
#             for word in ignored_words
#         ):
#             continue

#         # Ignore obvious phone numbers
#         if re.search(
#             r"\(\d{3}\)",
#             line
#         ):
#             continue

#         # Ignore mostly numeric lines
#         letters = sum(
#             character.isalpha()
#             for character in line
#         )

#         digits = sum(
#             character.isdigit()
#             for character in line
#         )

#         if letters < 3:
#             continue

#         if digits > letters:
#             continue

#         # Business names are commonly uppercase
#         alphabetic = "".join(
#             character
#             for character in line
#             if character.isalpha()
#         )

#         if (
#             alphabetic
#             and alphabetic.upper()
#             == alphabetic
#         ):

#             return line

#     # Fallback to first reasonable text line
#     for line in lines:

#         if sum(
#             character.isalpha()
#             for character in line
#         ) >= 3:

#             return line

#     return "Unknown Merchant"

def extract_merchant(text):
    lines = clean_lines(text)

    ignored_words = [
        "invoice",
        "receipt",
        "tanggal",
        "date",
        "total",
        "subtotal",
        "tax",
        "email",
        "telp",
        "phone",
        "thank you",
        "server",
        "order"
    ]

    # First prefer recognizable company/legal names
    company_patterns = [
        r"^PT\s+.+",
        r"^CV\s+.+",
        r".+\bPVT\.?\s+LTD\.?\b",
        r".+\bPRIVATE\s+LIMITED\b",
        r".+\bLLC\b",
        r".+\bLLP\b",
        r".+\bINC\.?\b",
        r".+\bLTD\.?\b"
    ]

    for line in lines[:30]:

        for pattern in company_patterns:

            if re.match(
                pattern,
                line,
                re.IGNORECASE
            ):

                return line.strip()

    # Next search for a reasonable business heading
    for line in lines[:15]:

        lower_line = line.lower()

        if any(
            word in lower_line
            for word in ignored_words
        ):
            continue

        # Avoid tiny OCR/logo fragments like "kl=do"
        if len(line) < 6:
            continue

        if "@" in line:
            continue

        letters = sum(
            character.isalpha()
            for character in line
        )

        if letters < 4:
            continue

        return line.strip()

    return "Unknown Merchant"


def detect_category(text):
    text = text.lower()

    categories = {

        "Taxi / Local Travel": [
            "uber",
            "ola",
            "rapido",
            "taxi",
            "cab",
            "auto ride",
            "auto rickshaw"
        ],

        "Meals": [
            "restaurant",
            "cafe",
            "coffee",
            "lunch",
            "dinner",
            "breakfast",
            "food",
            "pizza",
            "dominos",
            "swiggy",
            "zomato",
            "dine in",
            "table",
            "guests"
        ],

        "Travel": [
            "air india",
            "indigo",
            "flight",
            "airline",
            "railway",
            "irctc",
            "train ticket",
            "boarding pass"
        ],

        "Accommodation": [
            "hotel",
            "room",
            "check in",
            "check-in",
            "checkout",
            "check-out",
            "booking.com",
            "oyo"
        ],

        "Office Supplies": [
            "stationery",
            "printer",
            "paper",
            "cartridge",
            "office supplies",
            "notebook",
            "stapler",
            "pen"
        ]
    }

    scores = {}

    for category, keywords in categories.items():

        score = 0

        for keyword in keywords:

            if keyword in text:
                score += 1

        scores[category] = score

    best_category = max(
        scores,
        key=scores.get
    )

    if scores[best_category] == 0:
        return "Other"

    return best_category


def parse_receipt(text):

    merchant = extract_merchant(
        text
    )

    expense_date = extract_date(
        text
    )

    (
        amount,
        amount_source,
        amount_needs_review
    ) = extract_amount(text)

    category = detect_category(
        text
    )
    currency = detect_currency(text)

    needs_review = False

    review_reasons = []

    if not expense_date:

        needs_review = True

        review_reasons.append(
            "Date could not be detected."
        )

    if amount is None:

        needs_review = True

        review_reasons.append(
            "Amount could not be detected."
        )

    if amount_needs_review:

        needs_review = True

        review_reasons.append(
            "Final total was not clearly detected."
        )

    if merchant == "Unknown Merchant":

        needs_review = True

        review_reasons.append(
            "Merchant could not be identified."
        )

    if category == "Other":

        needs_review = True

        review_reasons.append(
            "Expense category could not be confidently identified."
        )

    return {
    "merchant": merchant,
    "expense_date": expense_date,
    "amount": amount,
    "currency": currency,
    "category": category,
    "amount_source": amount_source,
    "needs_review": needs_review,
    "review_reasons": review_reasons
}

from pathlib import Path


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp"
}


def find_receipt_images(folder_path, limit=10):
    """
    Find receipt/invoice images recursively
    inside a folder.
    """

    folder = Path(folder_path)

    if not folder.exists():
        raise FileNotFoundError(
            f"Folder not found: {folder_path}"
        )

    images = []

    for file_path in folder.rglob("*"):

        if (
            file_path.is_file()
            and file_path.suffix.lower()
            in IMAGE_EXTENSIONS
        ):
            images.append(file_path)

    return images[:limit]


def test_multiple_receipts(folder_path, limit=10):
    """
    Run OCR + structured extraction on
    multiple receipt images.
    """

    images = find_receipt_images(
        folder_path,
        limit
    )

    if not images:

        print(
            "No receipt images found."
        )

        return

    print(
        f"\nTesting {len(images)} receipt images\n"
    )

    print(
        "=" * 100
    )

    for index, image_path in enumerate(
        images,
        start=1
    ):

        print(
            f"\nReceipt {index}"
        )

        print(
            "File:",
            image_path.name
        )

        try:

            receipt_text = (
                extract_text_from_receipt(
                    str(image_path)
                )
            )

            result = parse_receipt(
                receipt_text
            )

            print(
                "Merchant:",
                result["merchant"]
            )

            print(
                "Date:",
                result["expense_date"]
            )

            print(
                "Amount:",
                result["amount"]
            )

            print(
                "Category:",
                result["category"]
            )

            print(
                "Amount Source:",
                result["amount_source"]
            )

            print(
                "Needs Review:",
                result["needs_review"]
            )

            if result["review_reasons"]:

                print(
                    "Review Reasons:"
                )

                for reason in (
                    result["review_reasons"]
                ):

                    print(
                        " -",
                        reason
                    )

        except Exception as error:

            print(
                "Processing Error:",
                error
            )

        print(
            "-" * 100
        )

def preprocess_receipt(image_path):
    image = cv2.imread(image_path)

    if image is None:
        raise FileNotFoundError(
            f"Could not read image: {image_path}"
        )

    # Increase image size because many dataset invoices
    # contain very small printed text
    image = cv2.resize(
        image,
        None,
        fx=3,
        fy=3,
        interpolation=cv2.INTER_CUBIC
    )

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    # Improve local contrast
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    enhanced = clahe.apply(gray)

    # Remove noise while preserving text edges
    denoised = cv2.bilateralFilter(
        enhanced,
        9,
        75,
        75
    )

    # Otsu threshold
    _, otsu = cv2.threshold(
        denoised,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    # Adaptive threshold
    adaptive = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11
    )

    return {
        "gray": gray,
        "enhanced": enhanced,
        "otsu": otsu,
        "adaptive": adaptive
    }


def score_ocr_text(text):
    """
    Give higher scores to OCR outputs that look
    more like useful invoices or receipts.
    """

    if not text:
        return 0

    score = 0

    cleaned = text.lower()

    # Reward readable text length
    score += len(
        re.findall(
            r"[a-zA-Z]{3,}",
            text
        )
    )

    important_words = [
        "invoice",
        "receipt",
        "total",
        "subtotal",
        "tax",
        "amount",
        "date",
        "bill",
        "qty",
        "price",
        "cash",
        "card"
    ]

    for word in important_words:
        if word in cleaned:
            score += 10

    # Reward possible monetary values
    money_matches = re.findall(
        r"(?:₹|\$|rs\.?|inr)?\s*\d+[.,]\d{2}",
        cleaned,
        flags=re.IGNORECASE
    )

    score += len(money_matches) * 5

    # Reward possible dates
    date_matches = re.findall(
        r"\b\d{1,4}[/-]\d{1,2}[/-]\d{1,4}\b",
        cleaned
    )

    score += len(date_matches) * 5

    return score


def extract_text_from_receipt(image_path):
    """
    Try several image-processing styles and
    Tesseract page segmentation modes.

    The OCR result with the highest quality score
    is returned.
    """

    processed_versions = preprocess_receipt(
        image_path
    )

    psm_modes = [
        6,   # Uniform block of text
        11,  # Sparse text
        4,   # Column-style text
        3    # Automatic page segmentation
    ]

    best_text = ""
    best_score = -1

    for image_name, processed_image in (
        processed_versions.items()
    ):

        for psm in psm_modes:

            config = (
                f"--oem 3 --psm {psm}"
            )

            text = pytesseract.image_to_string(
                processed_image,
                config=config
            ).strip()

            score = score_ocr_text(
                text
            )

            if score > best_score:

                best_score = score
                best_text = text

    return best_text


if __name__ == "__main__":

    image_path = input(
        "Enter receipt image path: "
    ).strip('"')

    if not os.path.exists(image_path):

        print(
            "Image file was not found."
        )

    else:

        receipt_text = extract_text_from_receipt(
            image_path
        )

        print(
            "\nExtracted Receipt Text\n"
        )

        print(receipt_text)

        result = parse_receipt(
            receipt_text
        )

        print(
            "\nStructured Claim Preview\n"
        )

        print(
            "Merchant:",
            result["merchant"]
        )

        print(
            "Date:",
            result["expense_date"]
        )

        print(
            "Amount:",
            result["amount"]
        )
        print(
            "Currency:",
            result["currency"]
        )
        print(
            "Category:",
            result["category"]
        )

        print(
            "Amount Source:",
            result["amount_source"]
        )

        print(
            "Needs User Review:",
            result["needs_review"]
        )

        if result["review_reasons"]:

            print(
                "\nReview Reasons:"
            )

            for reason in result["review_reasons"]:
                print(
                    "-",
                    reason
                )