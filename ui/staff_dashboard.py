import tkinter as tk

from tkinter import ttk
from tkinter import messagebox

from ui.claim_form import ClaimForm

from services.claim_service import (
    get_employee_claims,
    get_employee_unpaid_claims
)


class StaffDashboard(ttk.Frame):

    def __init__(
        self,
        parent,
        user,
        logout_callback
    ):
        super().__init__(
            parent,
            padding=30
        )

        self.user = user
        self.logout_callback = logout_callback

        self.pack(
            fill="both",
            expand=True
        )

        self.create_widgets()


    def create_widgets(self):

        header = ttk.Frame(
            self
        )

        header.pack(
            fill="x"
        )

        ttk.Label(
            header,
            text="Staff Dashboard",
            font=(
                "Segoe UI",
                24,
                "bold"
            )
        ).pack(
            side="left"
        )

        ttk.Button(
            header,
            text="Logout",
            command=self.logout_callback
        ).pack(
            side="right"
        )

        ttk.Label(
            self,
            text=(
                f"Welcome, "
                f"{self.user['full_name']}"
            ),
            font=(
                "Segoe UI",
                13
            )
        ).pack(
            anchor="w",
            pady=(25, 5)
        )

        ttk.Label(
            self,
            text=(
                f"Employee ID: "
                f"{self.user['employee_id']}"
            )
        ).pack(
            anchor="w"
        )

        ttk.Separator(
            self
        ).pack(
            fill="x",
            pady=25
        )

        actions = ttk.LabelFrame(
            self,
            text="Expense Claims",
            padding=25
        )

        actions.pack(
            fill="x"
        )

        ttk.Button(
            actions,
            text="Upload Receipt / New Claim",
            command=self.open_claim_form
        ).grid(
            row=0,
            column=0,
            padx=10,
            pady=10,
            ipadx=20,
            ipady=12
        )

        ttk.Button(
            actions,
            text="My Claims",
            command=self.show_my_claims
        ).grid(
            row=0,
            column=1,
            padx=10,
            pady=10,
            ipadx=25,
            ipady=12
        )

        ttk.Button(
            actions,
            text="Unpaid Claims",
            command=self.show_unpaid_claims
        ).grid(
            row=0,
            column=2,
            padx=10,
            pady=10,
            ipadx=20,
            ipady=12
        )


    def open_claim_form(self):

        ClaimForm(
            self,
            self.user
        )


    def show_my_claims(self):

        try:

            claims = get_employee_claims(
                self.user["employee_id"]
            )

        except Exception as error:

            messagebox.showerror(
                "My Claims",
                str(error)
            )

            return

        window = tk.Toplevel(
            self
        )

        window.title(
            "My Claims"
        )

        window.geometry(
            "1100x550"
        )

        window.minsize(
            900,
            450
        )

        ttk.Label(
            window,
            text="My Expense Claims",
            font=(
                "Segoe UI",
                20,
                "bold"
            )
        ).pack(
            anchor="w",
            padx=20,
            pady=(20, 5)
        )

        ttk.Label(
            window,
            text=(
                f"{self.user['full_name']} "
                f"({self.user['employee_id']})"
            )
        ).pack(
            anchor="w",
            padx=20,
            pady=(0, 15)
        )

        table_frame = ttk.Frame(
            window
        )

        table_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 20)
        )

        columns = (
            "claim_id",
            "date",
            "merchant",
            "category",
            "amount",
            "status"
        )

        table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        table.heading(
            "claim_id",
            text="Claim ID"
        )

        table.heading(
            "date",
            text="Expense Date"
        )

        table.heading(
            "merchant",
            text="Merchant"
        )

        table.heading(
            "category",
            text="Category"
        )

        table.heading(
            "amount",
            text="Amount"
        )

        table.heading(
            "status",
            text="Status"
        )

        table.column(
            "claim_id",
            width=190,
            anchor="center"
        )

        table.column(
            "date",
            width=120,
            anchor="center"
        )

        table.column(
            "merchant",
            width=220
        )

        table.column(
            "category",
            width=170
        )

        table.column(
            "amount",
            width=130,
            anchor="e"
        )

        table.column(
            "status",
            width=120,
            anchor="center"
        )

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=table.yview
        )

        table.configure(
            yscrollcommand=scrollbar.set
        )

        table.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        for claim in claims:

            currency = (
                claim["currency"]
                or "INR"
            )

            amount = (
                claim["amount"]
                or 0
            )

            table.insert(
                "",
                "end",
                values=(
                    claim["claim_id"],
                    claim["expense_date"],
                    claim["merchant_name"],
                    claim["category_name"],
                    f"{currency} {amount:.2f}",
                    claim["status"]
                )
            )

        if not claims:

            ttk.Label(
                window,
                text=(
                    "You have not created "
                    "any expense claims yet."
                ),
                font=(
                    "Segoe UI",
                    12
                )
            ).pack(
                pady=20
            )


    def show_unpaid_claims(self):

        try:

            claims = get_employee_unpaid_claims(
                self.user["employee_id"]
            )

        except Exception as error:

            messagebox.showerror(
                "Unpaid Claims",
                str(error)
            )

            return

        window = tk.Toplevel(
            self
        )

        window.title(
            "Unpaid Claims"
        )

        window.geometry(
            "1100x550"
        )

        window.minsize(
            900,
            450
        )

        ttk.Label(
            window,
            text="Claims Awaiting Payment",
            font=(
                "Segoe UI",
                20,
                "bold"
            )
        ).pack(
            anchor="w",
            padx=20,
            pady=(20, 5)
        )

        ttk.Label(
            window,
            text=(
                "Submitted and approved claims "
                "that Finance has not paid yet."
            )
        ).pack(
            anchor="w",
            padx=20,
            pady=(0, 15)
        )

        table_frame = ttk.Frame(
            window
        )

        table_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 20)
        )

        columns = (
            "claim_id",
            "date",
            "merchant",
            "category",
            "amount",
            "status"
        )

        table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        headings = {
            "claim_id": "Claim ID",
            "date": "Expense Date",
            "merchant": "Merchant",
            "category": "Category",
            "amount": "Amount",
            "status": "Current Status"
        }

        for column in columns:

            table.heading(
                column,
                text=headings[column]
            )

        table.column(
            "claim_id",
            width=190,
            anchor="center"
        )

        table.column(
            "date",
            width=120,
            anchor="center"
        )

        table.column(
            "merchant",
            width=220
        )

        table.column(
            "category",
            width=170
        )

        table.column(
            "amount",
            width=130,
            anchor="e"
        )

        table.column(
            "status",
            width=130,
            anchor="center"
        )

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=table.yview
        )

        table.configure(
            yscrollcommand=scrollbar.set
        )

        table.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        for claim in claims:

            currency = (
                claim["currency"]
                or "INR"
            )

            amount = (
                claim["amount"]
                or 0
            )

            table.insert(
                "",
                "end",
                values=(
                    claim["claim_id"],
                    claim["expense_date"],
                    claim["merchant_name"],
                    claim["category_name"],
                    f"{currency} {amount:.2f}",
                    claim["status"]
                )
            )

        if not claims:

            ttk.Label(
                window,
                text=(
                    "No claims are currently "
                    "waiting for payment."
                ),
                font=(
                    "Segoe UI",
                    12
                )
            ).pack(
                pady=20
            )