import tkinter as tk

from datetime import datetime
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

from PIL import Image
from PIL import ImageTk

from services.claim_service import (
    save_reviewed_receipt_draft,
    update_draft_claim,
    submit_claim as submit_claim_service
)

from services.receipt_processor import (
    extract_text_from_receipt,
    parse_receipt
)


class ClaimForm(tk.Toplevel):

    def __init__(
        self,
        parent,
        user
    ):
        super().__init__(parent)

        self.user = user

        self.title(
            "New Expense Claim"
        )

        self.geometry(
            "1150x720"
        )

        self.minsize(
            1000,
            650
        )

        # Selected receipt image paths
        self.selected_files = []

        # Current receipt being displayed
        self.current_index = 0

        # Keeps Tkinter image alive
        self.image_reference = None

        # Store OCR text separately for every image
        self.ocr_results = {}

        # Store extracted/editable form values
        # separately for every uploaded receipt
        self.receipt_data = {}

        # Image path -> Claim ID
        self.claim_ids = {}

        # Submitted image paths
        self.submitted_files = set()

        self.create_widgets()


    def create_widgets(self):

        main_frame = ttk.Frame(
            self,
            padding=20
        )

        main_frame.pack(
            fill="both",
            expand=True
        )

        header_frame = ttk.Frame(
            main_frame
        )

        header_frame.pack(
            fill="x",
            pady=(0, 15)
        )

        ttk.Label(
            header_frame,
            text="Create Expense Claim",
            font=(
                "Segoe UI",
                22,
                "bold"
            )
        ).pack(
            side="left"
        )

        ttk.Label(
            header_frame,
            text=(
                f"{self.user['full_name']} "
                f"({self.user['employee_id']})"
            )
        ).pack(
            side="right"
        )

        ttk.Separator(
            main_frame
        ).pack(
            fill="x",
            pady=(0, 15)
        )

        body = ttk.Frame(
            main_frame
        )

        body.pack(
            fill="both",
            expand=True
        )

        body.columnconfigure(
            0,
            weight=1
        )

        body.columnconfigure(
            1,
            weight=1
        )

        body.rowconfigure(
            0,
            weight=1
        )

        self.create_receipt_section(
            body
        )

        self.create_form_section(
            body
        )


    def create_receipt_section(
        self,
        parent
    ):

        receipt_frame = ttk.LabelFrame(
            parent,
            text="Receipt",
            padding=15
        )

        receipt_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 10)
        )

        ttk.Button(
            receipt_frame,
            text="Upload Receipt Images",
            command=self.select_receipts
        ).pack(
            fill="x",
            pady=(0, 10)
        )

        self.file_counter = ttk.Label(
            receipt_frame,
            text="No receipts selected"
        )

        self.file_counter.pack(
            pady=(0, 10)
        )

        self.claim_status_label = ttk.Label(
            receipt_frame,
            text="",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        )

        self.claim_status_label.pack(
            pady=(0, 8)
        )

        self.image_label = ttk.Label(
            receipt_frame,
            text=(
                "Upload JPG, JPEG, PNG, BMP "
                "or WEBP receipt images"
            ),
            anchor="center"
        )

        self.image_label.pack(
            fill="both",
            expand=True
        )

        navigation = ttk.Frame(
            receipt_frame
        )

        navigation.pack(
            fill="x",
            pady=(10, 0)
        )

        self.previous_button = ttk.Button(
            navigation,
            text="Previous",
            command=self.previous_receipt,
            state="disabled"
        )

        self.previous_button.pack(
            side="left"
        )

        self.next_button = ttk.Button(
            navigation,
            text="Next",
            command=self.next_receipt,
            state="disabled"
        )

        self.next_button.pack(
            side="right"
        )


    def create_form_section(
        self,
        parent
    ):

        form = ttk.LabelFrame(
            parent,
            text="Extracted Claim Details",
            padding=20
        )

        form.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(10, 0)
        )

        form.columnconfigure(
            1,
            weight=1
        )

        self.merchant_var = tk.StringVar()

        self.date_var = tk.StringVar()

        self.amount_var = tk.StringVar()

        self.currency_var = tk.StringVar(
            value="INR"
        )

        self.category_var = tk.StringVar(
            value="Other"
        )

        row = 0

        ttk.Label(
            form,
            text="Merchant"
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=8
        )

        self.merchant_entry = ttk.Entry(
            form,
            textvariable=self.merchant_var
        )

        self.merchant_entry.grid(
            row=row,
            column=1,
            sticky="ew",
            padx=(15, 0),
            pady=8
        )

        row += 1

        ttk.Label(
            form,
            text="Expense Date"
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=8
        )

        self.date_entry = ttk.Entry(
            form,
            textvariable=self.date_var
        )

        self.date_entry.grid(
            row=row,
            column=1,
            sticky="ew",
            padx=(15, 0),
            pady=8
        )

        row += 1

        ttk.Label(
            form,
            text="Amount"
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=8
        )

        self.amount_entry = ttk.Entry(
            form,
            textvariable=self.amount_var
        )

        self.amount_entry.grid(
            row=row,
            column=1,
            sticky="ew",
            padx=(15, 0),
            pady=8
        )

        row += 1

        ttk.Label(
            form,
            text="Currency"
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=8
        )

        self.currency_box = ttk.Combobox(
            form,
            textvariable=self.currency_var,
            state="readonly",
            values=[
                "INR",
                "USD",
                "IDR",
                "EUR",
                "GBP",
                "Unknown"
            ]
        )

        self.currency_box.grid(
            row=row,
            column=1,
            sticky="ew",
            padx=(15, 0),
            pady=8
        )

        row += 1

        ttk.Label(
            form,
            text="Category"
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=8
        )

        self.category_box = ttk.Combobox(
            form,
            textvariable=self.category_var,
            state="readonly",
            values=[
                "Taxi / Local Travel",
                "Meals",
                "Travel",
                "Accommodation",
                "Office Supplies",
                "Other"
            ]
        )

        self.category_box.grid(
            row=row,
            column=1,
            sticky="ew",
            padx=(15, 0),
            pady=8
        )

        row += 1

        ttk.Label(
            form,
            text="Description"
        ).grid(
            row=row,
            column=0,
            sticky="nw",
            pady=8
        )

        self.description_text = tk.Text(
            form,
            height=4,
            wrap="word"
        )

        self.description_text.grid(
            row=row,
            column=1,
            sticky="ew",
            padx=(15, 0),
            pady=8
        )

        row += 1

        self.review_label = ttk.Label(
            form,
            text=(
                "Upload a receipt to extract "
                "claim information."
            ),
            wraplength=430
        )

        self.review_label.grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w",
            pady=15
        )

        row += 1

        ttk.Separator(
            form
        ).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=10
        )

        row += 1

        button_frame = ttk.Frame(
            form
        )

        button_frame.grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="ew"
        )

        self.save_button = ttk.Button(
            button_frame,
            text="Save Draft",
            command=self.save_draft,
            state="disabled"
        )

        self.save_button.pack(
            side="left",
            padx=(0, 10)
        )

        self.submit_button = ttk.Button(
            button_frame,
            text="Submit Claim",
            command=self.submit_claim,
            state="disabled"
        )

        self.submit_button.pack(
            side="left"
        )


    def select_receipts(self):

        files = filedialog.askopenfilenames(
            title="Select Receipt Images",
            filetypes=[
                (
                    "Receipt Images",
                    "*.jpg *.jpeg *.png *.bmp *.webp"
                )
            ]
        )

        if not files:
            return

        self.selected_files = list(
            files
        )

        self.current_index = 0

        messagebox.showinfo(
            "Receipts Selected",
            (
                f"{len(self.selected_files)} receipt(s) "
                "selected successfully.\n\n"
                "The system will extract information "
                "from each receipt separately."
            ),
            parent=self
        )

        self.load_current_receipt()


    def load_current_receipt(self):

        if not self.selected_files:
            return

        image_path = self.selected_files[
            self.current_index
        ]

        self.file_counter.config(
            text=(
                f"Receipt "
                f"{self.current_index + 1} "
                f"of "
                f"{len(self.selected_files)}"
            )
        )

        self.show_image(
            image_path
        )

        # Process image only once
        if image_path not in self.receipt_data:

            self.process_receipt(
                image_path
            )

        else:

            self.restore_receipt_data(
                image_path
            )

        self.update_navigation()

        self.update_claim_status()


    def show_image(
        self,
        image_path
    ):

        try:

            image = Image.open(
                image_path
            )

            image.thumbnail(
                (480, 480)
            )

            photo = ImageTk.PhotoImage(
                image
            )

            self.image_reference = photo

            self.image_label.config(
                image=photo,
                text=""
            )

        except Exception as error:

            self.image_label.config(
                text=(
                    "Unable to preview image.\n"
                    f"{error}"
                ),
                image=""
            )


    def process_receipt(
        self,
        image_path
    ):

        self.config(
            cursor="wait"
        )

        self.update_idletasks()

        try:

            text = extract_text_from_receipt(
                image_path
            )

            self.ocr_results[
                image_path
            ] = text

            result = parse_receipt(
                text
            )

            data = {
                "merchant":
                    result["merchant"],

                "expense_date":
                    result["expense_date"] or "",

                "amount":
                    (
                        ""
                        if result["amount"] is None
                        else str(
                            result["amount"]
                        )
                    ),

                "currency":
                    result["currency"],

                "category":
                    result["category"],

                "description":
                    "",

                "review_reasons":
                    result["review_reasons"]
            }

            self.receipt_data[
                image_path
            ] = data

            self.restore_receipt_data(
                image_path
            )

            self.save_button.config(
                state="normal"
            )

            self.submit_button.config(
                state="normal"
            )

            messagebox.showinfo(
                "Receipt Processed",
                (
                    "Receipt uploaded and processed "
                    "successfully.\n\n"
                    "Please verify the extracted "
                    "details before saving or submitting."
                ),
                parent=self
            )

        except Exception as error:

            self.save_button.config(
                state="disabled"
            )

            self.submit_button.config(
                state="disabled"
            )

            messagebox.showerror(
                "Receipt Processing Failed",
                (
                    "The receipt could not be processed.\n\n"
                    f"{error}"
                ),
                parent=self
            )

        finally:

            self.config(
                cursor=""
            )


    def restore_receipt_data(
        self,
        image_path
    ):

        data = self.receipt_data.get(
            image_path
        )

        if not data:
            return

        self.merchant_var.set(
            data["merchant"]
        )

        self.date_var.set(
            data["expense_date"]
        )

        self.amount_var.set(
            data["amount"]
        )

        self.currency_var.set(
            data["currency"]
        )

        self.category_var.set(
            data["category"]
        )

        self.description_text.delete(
            "1.0",
            "end"
        )

        self.description_text.insert(
            "1.0",
            data["description"]
        )

        review_reasons = data.get(
            "review_reasons",
            []
        )

        if review_reasons:

            self.review_label.config(
                text=(
                    "Please review: "
                    + " ".join(
                        review_reasons
                    )
                )
            )

        else:

            self.review_label.config(
                text=(
                    "Receipt information was extracted "
                    "successfully. Verify it before "
                    "submitting."
                )
            )

        if image_path in self.submitted_files:

            self.save_button.config(
                state="disabled"
            )

            self.submit_button.config(
                state="disabled"
            )

        else:

            self.save_button.config(
                state="normal"
            )

            self.submit_button.config(
                state="normal"
            )


    def save_current_form_state(self):

        if not self.selected_files:
            return

        image_path = self.selected_files[
            self.current_index
        ]

        if image_path not in self.receipt_data:
            return

        self.receipt_data[
            image_path
        ]["merchant"] = (
            self.merchant_var
            .get()
            .strip()
        )

        self.receipt_data[
            image_path
        ]["expense_date"] = (
            self.date_var
            .get()
            .strip()
        )

        self.receipt_data[
            image_path
        ]["amount"] = (
            self.amount_var
            .get()
            .strip()
        )

        self.receipt_data[
            image_path
        ]["currency"] = (
            self.currency_var
            .get()
            .strip()
        )

        self.receipt_data[
            image_path
        ]["category"] = (
            self.category_var
            .get()
            .strip()
        )

        self.receipt_data[
            image_path
        ]["description"] = (
            self.description_text
            .get(
                "1.0",
                "end"
            )
            .strip()
        )


    def update_navigation(self):

        self.previous_button.config(
            state=(
                "normal"
                if self.current_index > 0
                else "disabled"
            )
        )

        self.next_button.config(
            state=(
                "normal"
                if (
                    self.current_index
                    < len(self.selected_files) - 1
                )
                else "disabled"
            )
        )


    def previous_receipt(self):

        if self.current_index > 0:

            self.save_current_form_state()

            self.current_index -= 1

            self.load_current_receipt()


    def next_receipt(self):

        if (
            self.current_index
            < len(self.selected_files) - 1
        ):

            self.save_current_form_state()

            self.current_index += 1

            self.load_current_receipt()


    def validate_form(self):

        merchant = (
            self.merchant_var
            .get()
            .strip()
        )

        expense_date = (
            self.date_var
            .get()
            .strip()
        )

        amount = (
            self.amount_var
            .get()
            .strip()
        )

        currency = (
            self.currency_var
            .get()
            .strip()
        )

        category = (
            self.category_var
            .get()
            .strip()
        )

        if not merchant:

            messagebox.showwarning(
                "Missing Merchant",
                "Please enter the merchant name.",
                parent=self
            )

            return False

        if (
            not expense_date
        ):

            messagebox.showwarning(
                "Missing Date",
                "Please enter the expense date.",
                parent=self
            )

            return False

        try:

            datetime.strptime(
                expense_date,
                "%Y-%m-%d"
            )

        except ValueError:

            messagebox.showwarning(
                "Invalid Date",
                (
                    "Expense Date must be in "
                    "YYYY-MM-DD format."
                ),
                parent=self
            )

            return False

        try:

            amount_value = float(
                amount
            )

            if amount_value <= 0:
                raise ValueError

        except ValueError:

            messagebox.showwarning(
                "Invalid Amount",
                (
                    "Please enter a valid amount "
                    "greater than zero."
                ),
                parent=self
            )

            return False

        if not currency:

            messagebox.showwarning(
                "Missing Currency",
                "Please select a currency.",
                parent=self
            )

            return False

        if not category:

            messagebox.showwarning(
                "Missing Category",
                "Please select an expense category.",
                parent=self
            )

            return False

        return True


    def save_draft(
        self,
        show_popup=True
    ):

        if not self.selected_files:

            messagebox.showwarning(
                "No Receipt",
                "Please upload a receipt first.",
                parent=self
            )

            return None

        if not self.validate_form():
            return None

        self.save_current_form_state()

        image_path = self.selected_files[
            self.current_index
        ]

        data = self.receipt_data[
            image_path
        ]

        try:

            # Existing Draft -> update same Claim ID
            if image_path in self.claim_ids:

                claim_id = self.claim_ids[
                    image_path
                ]

                update_draft_claim(
                    claim_id=claim_id,
                    employee_id=self.user[
                        "employee_id"
                    ],
                    merchant_name=data[
                        "merchant"
                    ],
                    expense_date=data[
                        "expense_date"
                    ],
                    amount=data[
                        "amount"
                    ],
                    currency=data[
                        "currency"
                    ],
                    category_name=data[
                        "category"
                    ],
                    description=data[
                        "description"
                    ]
                )

                if show_popup:

                    messagebox.showinfo(
                        "Draft Updated",
                        (
                            "Claim updated successfully.\n\n"
                            f"Claim ID: {claim_id}\n"
                            "Status: Draft"
                        ),
                        parent=self
                    )

            # New receipt -> create new Claim ID
            else:

                claim_id = (
                    save_reviewed_receipt_draft(
                        employee_id=self.user[
                            "employee_id"
                        ],
                        image_path=image_path,
                        merchant_name=data[
                            "merchant"
                        ],
                        expense_date=data[
                            "expense_date"
                        ],
                        amount=data[
                            "amount"
                        ],
                        currency=data[
                            "currency"
                        ],
                        category_name=data[
                            "category"
                        ],
                        description=data[
                            "description"
                        ],
                        ocr_text=self.ocr_results.get(
                            image_path,
                            ""
                        )
                    )
                )

                self.claim_ids[
                    image_path
                ] = claim_id

                if show_popup:

                    messagebox.showinfo(
                        "Draft Saved",
                        (
                            "Receipt and claim saved "
                            "successfully.\n\n"
                            f"Claim ID: {claim_id}\n"
                            "Status: Draft"
                        ),
                        parent=self
                    )

            self.update_claim_status()

            return claim_id

        except Exception as error:

            messagebox.showerror(
                "Save Failed",
                str(error),
                parent=self
            )

            return None


    def submit_claim(self):

        if not self.selected_files:
            return

        image_path = self.selected_files[
            self.current_index
        ]

        if image_path in self.submitted_files:

            messagebox.showinfo(
                "Already Submitted",
                "This receipt has already been submitted.",
                parent=self
            )

            return

        # Save or update Draft first,
        # without showing an extra Draft popup
        claim_id = self.save_draft(
            show_popup=False
        )

        if not claim_id:
            return

        try:

            result = submit_claim_service(
                claim_id=claim_id,
                employee_id=self.user[
                    "employee_id"
                ]
            )

            self.submitted_files.add(
                image_path
            )

            message = (
                "Claim submitted successfully.\n\n"
                f"Claim ID: {claim_id}\n"
                "Status: Submitted"
            )

            if result.get(
                "possible_duplicate"
            ):

                message += (
                    "\n\nWarning: possible duplicate "
                    "receipt detected."
                )

                if result.get(
                    "matched_claim_id"
                ):

                    message += (
                        "\nMatched Claim: "
                        f"{result['matched_claim_id']}"
                    )

                message += (
                    "\nSimilarity Score: "
                    f"{result['duplicate_score']}%"
                )

            if result.get(
                "limit_exceeded"
            ):

                message += (
                    "\n\nMonthly category limit "
                    "has been exceeded by "
                    f"₹{result['limit_exceeded_by']:.2f}."
                )

            elif result.get(
                "near_limit"
            ):

                message += (
                    "\n\nWarning: you are close "
                    "to your monthly category limit."
                )

            if result.get(
                "foreign_currency"
            ):

                message += (
                    "\n\nForeign-currency claim will "
                    "require Finance review for "
                    "monthly limit analysis."
                )

            messagebox.showinfo(
                "Claim Submitted",
                message,
                parent=self
            )

            self.save_button.config(
                state="disabled"
            )

            self.submit_button.config(
                state="disabled"
            )

            self.update_claim_status()

        except Exception as error:

            messagebox.showerror(
                "Submission Failed",
                str(error),
                parent=self
            )


    def update_claim_status(self):

        if not self.selected_files:

            self.claim_status_label.config(
                text=""
            )

            return

        image_path = self.selected_files[
            self.current_index
        ]

        if image_path in self.submitted_files:

            claim_id = self.claim_ids.get(
                image_path,
                ""
            )

            self.claim_status_label.config(
                text=(
                    f"Claim: {claim_id} | "
                    "Status: Submitted"
                )
            )

        elif image_path in self.claim_ids:

            claim_id = self.claim_ids[
                image_path
            ]

            self.claim_status_label.config(
                text=(
                    f"Claim: {claim_id} | "
                    "Status: Draft"
                )
            )

        else:

            self.claim_status_label.config(
                text="Not saved yet"
            )