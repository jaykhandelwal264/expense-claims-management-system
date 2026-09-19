import tkinter as tk

from tkinter import ttk
from tkinter import messagebox
from tkinter import simpledialog

from ui.claim_form import ClaimForm

from services.claim_service import (
    get_employee_claims,
    get_employee_unpaid_claims,
    get_manager_pending_claims,
    approve_claim,
    reject_claim
)


class ManagerDashboard(ttk.Frame):

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
            text="Manager Dashboard",
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

        ttk.Label(
            self,
            text=(
                f"Manager Level: "
                f"{self.user['manager_level']}"
            )
        ).pack(
            anchor="w",
            pady=(5, 0)
        )

        ttk.Separator(
            self
        ).pack(
            fill="x",
            pady=25
        )

        # Level 1, 2 and 3 managers can create
        # and track their own expense claims.
        if self.user["manager_level"] < 4:

            own_claims_frame = ttk.LabelFrame(
                self,
                text="My Expense Claims",
                padding=25
            )

            own_claims_frame.pack(
                fill="x",
                pady=(0, 20)
            )

            ttk.Button(
                own_claims_frame,
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
                own_claims_frame,
                text="My Claims",
                command=self.show_my_claims
            ).grid(
                row=0,
                column=1,
                padx=10,
                pady=10,
                ipadx=30,
                ipady=12
            )

            ttk.Button(
                own_claims_frame,
                text="My Unpaid Claims",
                command=self.show_unpaid_claims
            ).grid(
                row=0,
                column=2,
                padx=10,
                pady=10,
                ipadx=20,
                ipady=12
            )

        # Every manager can review assigned claims.
        approval_frame = ttk.LabelFrame(
            self,
            text="Manager Responsibilities",
            padding=25
        )

        approval_frame.pack(
            fill="x"
        )

        ttk.Button(
            approval_frame,
            text="Team Claims To Approve",
            command=self.show_pending_claims
        ).grid(
            row=0,
            column=0,
            padx=10,
            pady=10,
            ipadx=30,
            ipady=12
        )


    def open_claim_form(self):

        # Extra protection even though the button
        # is hidden for Level 4 managers.
        if self.user["manager_level"] >= 4:

            messagebox.showwarning(
                "Not Allowed",
                "This manager cannot create personal claims."
            )

            return

        ClaimForm(
            self,
            self.user
        )


    def show_my_claims(self):

        if self.user["manager_level"] >= 4:
            return

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

        headings = {
            "claim_id": "Claim ID",
            "date": "Expense Date",
            "merchant": "Merchant",
            "category": "Category",
            "amount": "Amount",
            "status": "Status"
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
                text="You have not created any claims yet."
            ).pack(
                pady=20
            )


    def show_unpaid_claims(self):

        if self.user["manager_level"] >= 4:
            return

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
            "My Unpaid Claims"
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
            text="My Claims Awaiting Payment",
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
                "Submitted or approved claims "
                "that have not been paid yet."
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
                    "You currently have no claims "
                    "waiting for payment."
                )
            ).pack(
                pady=20
            )


    def show_pending_claims(self):

        try:

            claims = get_manager_pending_claims(
                self.user["employee_id"]
            )

        except Exception as error:

            messagebox.showerror(
                "Pending Claims",
                str(error)
            )

            return

        window = tk.Toplevel(
            self
        )

        window.title(
            "Team Claims To Approve"
        )

        window.geometry(
            "1200x600"
        )

        window.minsize(
            1000,
            500
        )

        ttk.Label(
            window,
            text="Team Claims Awaiting Approval",
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
                "Select a claim below and "
                "approve or reject it."
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
            pady=(0, 10)
        )

        columns = (
            "claim_id",
            "employee",
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
            "employee": "Employee",
            "date": "Expense Date",
            "merchant": "Merchant",
            "category": "Category",
            "amount": "Amount",
            "status": "Status"
        }

        for column in columns:

            table.heading(
                column,
                text=headings[column]
            )

        table.column(
            "claim_id",
            width=180
        )

        table.column(
            "employee",
            width=180
        )

        table.column(
            "date",
            width=110
        )

        table.column(
            "merchant",
            width=180
        )

        table.column(
            "category",
            width=150
        )

        table.column(
            "amount",
            width=120,
            anchor="e"
        )

        table.column(
            "status",
            width=100,
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

        claim_lookup = {}

        for claim in claims:

            claim_lookup[
                claim["claim_id"]
            ] = claim

            table.insert(
                "",
                "end",
                values=(
                    claim["claim_id"],
                    (
                        f"{claim['employee_id']} - "
                        f"{claim['employee_name']}"
                    ),
                    claim["expense_date"],
                    claim["merchant_name"],
                    claim["category_name"],
                    f"{claim['amount']:.2f}",
                    claim["status"]
                )
            )

        button_frame = ttk.Frame(
            window
        )

        button_frame.pack(
            fill="x",
            padx=20,
            pady=(5, 20)
        )


        def get_selected_claim():

            selected = table.selection()

            if not selected:

                messagebox.showwarning(
                    "Select Claim",
                    "Please select a claim first.",
                    parent=window
                )

                return None

            values = table.item(
                selected[0],
                "values"
            )

            return values[0]


        def approve_selected():

            claim_id = get_selected_claim()

            if not claim_id:
                return

            claim = claim_lookup[
                claim_id
            ]

            confirm = messagebox.askyesno(
                "Approve Claim",
                (
                    f"Approve claim {claim_id}?\n\n"
                    f"Employee: "
                    f"{claim['employee_name']}\n"
                    f"Merchant: "
                    f"{claim['merchant_name']}\n"
                    f"Amount: "
                    f"{claim['amount']:.2f}"
                ),
                parent=window
            )

            if not confirm:
                return

            try:

                approve_claim(
                    claim_id=claim_id,
                    manager_id=self.user[
                        "employee_id"
                    ],
                    remarks=(
                        "Claim reviewed and approved "
                        "by manager."
                    )
                )

                messagebox.showinfo(
                    "Claim Approved",
                    (
                        f"{claim_id} approved successfully.\n\n"
                        "The claim is now available "
                        "to Finance for payment."
                    ),
                    parent=window
                )

                selected = table.selection()

                if selected:

                    table.delete(
                        selected[0]
                    )

            except Exception as error:

                messagebox.showerror(
                    "Approval Failed",
                    str(error),
                    parent=window
                )


        def reject_selected():

            claim_id = get_selected_claim()

            if not claim_id:
                return

            remarks = simpledialog.askstring(
                "Reject Claim",
                (
                    "Enter the reason for rejecting "
                    f"{claim_id}:"
                ),
                parent=window
            )

            if remarks is None:
                return

            if not remarks.strip():

                messagebox.showwarning(
                    "Reason Required",
                    (
                        "Please provide a reason "
                        "for rejection."
                    ),
                    parent=window
                )

                return

            try:

                reject_claim(
                    claim_id=claim_id,
                    manager_id=self.user[
                        "employee_id"
                    ],
                    remarks=remarks.strip()
                )

                messagebox.showinfo(
                    "Claim Rejected",
                    (
                        f"{claim_id} has been rejected."
                    ),
                    parent=window
                )

                selected = table.selection()

                if selected:

                    table.delete(
                        selected[0]
                    )

            except Exception as error:

                messagebox.showerror(
                    "Rejection Failed",
                    str(error),
                    parent=window
                )


        ttk.Button(
            button_frame,
            text="Approve Selected Claim",
            command=approve_selected
        ).pack(
            side="left",
            padx=(0, 10),
            ipadx=15,
            ipady=8
        )

        ttk.Button(
            button_frame,
            text="Reject Selected Claim",
            command=reject_selected
        ).pack(
            side="left",
            ipadx=15,
            ipady=8
        )

        if not claims:

            messagebox.showinfo(
                "Team Claims",
                (
                    "There are currently no team "
                    "claims awaiting your approval."
                ),
                parent=window
            )