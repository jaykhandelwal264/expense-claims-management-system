import tkinter as tk

from datetime import datetime
from pathlib import Path

from tkinter import ttk
from tkinter import messagebox

from PIL import Image
from PIL import ImageTk

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from services.claim_service import (
    get_finance_approved_claims,
    get_finance_paid_claims,
    get_claim_receipt_path,
    mark_claim_paid
)

from services.analytics_service import (
    get_finance_filter_options,
    get_finance_analysis
)


class FinanceDashboard(ttk.Frame):

    def __init__(
        self,
        parent,
        user,
        logout_callback
    ):
        super().__init__(
            parent,
            padding=0
        )

        self.user = user
        self.logout_callback = logout_callback

        self.employee_map = {}
        self.category_map = {}
        self.month_map = {}

        self.pack(
            fill="both",
            expand=True
        )

        self.setup_styles()

        self.create_main_header()

        self.create_main_notebook()

        self.load_filter_options()

        self.refresh_payments()

        # Do not show no-data popup on first load
        self.refresh_analysis(
            show_no_data_popup=False
        )


    # =====================================================
    # STYLES
    # =====================================================

    def setup_styles(self):

        style = ttk.Style()

        try:
            style.theme_use(
                "clam"
            )
        except tk.TclError:
            pass

        style.configure(
            "Finance.TNotebook",
            borderwidth=0
        )

        style.configure(
            "Finance.TNotebook.Tab",
            font=(
                "Segoe UI",
                10,
                "bold"
            ),
            padding=(
                15,
                7
            )
        )

        style.configure(
            "Finance.Treeview",
            rowheight=30,
            font=(
                "Segoe UI",
                10
            )
        )

        style.configure(
            "Finance.Treeview.Heading",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        )

        style.configure(
            "Primary.TButton",
            font=(
                "Segoe UI",
                9,
                "bold"
            ),
            padding=7
        )


    # =====================================================
    # MAIN HEADER
    # =====================================================

    def create_main_header(self):

        header = tk.Frame(
            self,
            bg="#FFFFFF",
            height=64
        )

        header.pack(
            fill="x"
        )

        header.pack_propagate(
            False
        )

        left = tk.Frame(
            header,
            bg="#FFFFFF"
        )

        left.pack(
            side="left",
            padx=22,
            pady=6
        )

        tk.Label(
            left,
            text="Finance Dashboard",
            font=(
                "Segoe UI",
                19,
                "bold"
            ),
            bg="#FFFFFF",
            fg="#1F2937"
        ).pack(
            anchor="w"
        )

        tk.Label(
            left,
            text=(
                f"Welcome, {self.user['full_name']} "
                f"({self.user['employee_id']})"
            ),
            font=(
                "Segoe UI",
                8
            ),
            bg="#FFFFFF",
            fg="#6B7280"
        ).pack(
            anchor="w",
            pady=(1, 0)
        )

        ttk.Button(
            header,
            text="Logout",
            command=self.logout_callback
        ).pack(
            side="right",
            padx=22,
            pady=13
        )


    # =====================================================
    # MAIN NOTEBOOK
    # =====================================================

    def create_main_notebook(self):

        self.main_notebook = ttk.Notebook(
            self,
            style="Finance.TNotebook"
        )

        self.main_notebook.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(5, 8)
        )

        self.payment_page = ttk.Frame(
            self.main_notebook
        )

        self.analysis_page = ttk.Frame(
            self.main_notebook
        )

        self.main_notebook.add(
            self.payment_page,
            text="Payment Management"
        )

        self.main_notebook.add(
            self.analysis_page,
            text="Analysis Dashboard"
        )

        self.create_payment_page()

        self.create_analysis_page()


    # =====================================================
    # PAYMENT MANAGEMENT
    # =====================================================

    def create_payment_page(self):

        container = ttk.Frame(
            self.payment_page,
            padding=18
        )

        container.pack(
            fill="both",
            expand=True
        )

        top = ttk.Frame(
            container
        )

        top.pack(
            fill="x",
            pady=(0, 12)
        )

        ttk.Label(
            top,
            text="Expense Reimbursement",
            font=(
                "Segoe UI",
                18,
                "bold"
            )
        ).pack(
            side="left"
        )

        ttk.Button(
            top,
            text="Refresh",
            command=self.refresh_payments
        ).pack(
            side="right"
        )

        self.payment_notebook = ttk.Notebook(
            container
        )

        self.payment_notebook.pack(
            fill="both",
            expand=True
        )

        self.ready_page = ttk.Frame(
            self.payment_notebook,
            padding=10
        )

        self.paid_page = ttk.Frame(
            self.payment_notebook,
            padding=10
        )

        self.payment_notebook.add(
            self.ready_page,
            text="Ready To Pay"
        )

        self.payment_notebook.add(
            self.paid_page,
            text="Paid History"
        )

        self.create_ready_to_pay_table()

        self.create_paid_history_table()


    def create_ready_to_pay_table(self):

        frame = ttk.Frame(
            self.ready_page
        )

        frame.pack(
            fill="both",
            expand=True
        )

        columns = (
            "claim",
            "employee",
            "date",
            "merchant",
            "category",
            "amount",
            "duplicate",
            "limit",
            "approved"
        )

        self.ready_table = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
            selectmode="extended",
            style="Finance.Treeview"
        )

        headings = {
            "claim": "Claim ID",
            "employee": "Employee",
            "date": "Expense Date",
            "merchant": "Merchant",
            "category": "Category",
            "amount": "Amount",
            "duplicate": "Duplicate",
            "limit": "Limit",
            "approved": "Approved By"
        }

        widths = {
            "claim": 180,
            "employee": 190,
            "date": 110,
            "merchant": 180,
            "category": 155,
            "amount": 120,
            "duplicate": 120,
            "limit": 150,
            "approved": 170
        }

        for column in columns:

            self.ready_table.heading(
                column,
                text=headings[column]
            )

            self.ready_table.column(
                column,
                width=widths[column]
            )

        scrollbar = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=self.ready_table.yview
        )

        self.ready_table.configure(
            yscrollcommand=scrollbar.set
        )

        self.ready_table.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        buttons = ttk.Frame(
            self.ready_page
        )

        buttons.pack(
            fill="x",
            pady=(10, 0)
        )

        ttk.Button(
            buttons,
            text="View Receipt",
            command=self.view_selected_receipt
        ).pack(
            side="left",
            padx=(0, 10)
        )

        ttk.Button(
            buttons,
            text="Mark Selected Paid",
            command=self.pay_selected_claims,
            style="Primary.TButton"
        ).pack(
            side="left"
        )


    def create_paid_history_table(self):

        frame = ttk.Frame(
            self.paid_page
        )

        frame.pack(
            fill="both",
            expand=True
        )

        columns = (
            "claim",
            "employee",
            "date",
            "merchant",
            "category",
            "amount",
            "paid"
        )

        self.paid_table = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
            style="Finance.Treeview"
        )

        headings = {
            "claim": "Claim ID",
            "employee": "Employee",
            "date": "Expense Date",
            "merchant": "Merchant",
            "category": "Category",
            "amount": "Amount",
            "paid": "Paid At"
        }

        widths = {
            "claim": 180,
            "employee": 200,
            "date": 110,
            "merchant": 200,
            "category": 170,
            "amount": 130,
            "paid": 190
        }

        for column in columns:

            self.paid_table.heading(
                column,
                text=headings[column]
            )

            self.paid_table.column(
                column,
                width=widths[column]
            )

        scrollbar = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=self.paid_table.yview
        )

        self.paid_table.configure(
            yscrollcommand=scrollbar.set
        )

        self.paid_table.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )


    def refresh_payments(self):

        for item in self.ready_table.get_children():

            self.ready_table.delete(
                item
            )

        try:

            claims = (
                get_finance_approved_claims()
            )

        except Exception as error:

            messagebox.showerror(
                "Payment Queue Error",
                str(error)
            )

            return

        for claim in claims:

            currency = (
                claim["currency"]
                or "INR"
            )

            duplicate = "Clear"

            if claim["duplicate_flag"]:

                duplicate = (
                    f"Review "
                    f"{claim['duplicate_score']:.0f}%"
                )

            limit = "Within Limit"

            if claim["limit_flag"]:

                limit = (
                    "Exceeded "
                    f"{claim['limit_exceeded_by']:.2f}"
                )

            self.ready_table.insert(
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

                    (
                        f"{currency} "
                        f"{claim['amount']:,.2f}"
                    ),

                    duplicate,

                    limit,

                    claim["approver_name"]
                )
            )

        self.payment_notebook.tab(
            self.ready_page,
            text=(
                f"Ready To Pay "
                f"({len(claims)})"
            )
        )

        for item in self.paid_table.get_children():

            self.paid_table.delete(
                item
            )

        try:

            paid_claims = (
                get_finance_paid_claims()
            )

        except Exception as error:

            messagebox.showerror(
                "Paid History Error",
                str(error)
            )

            return

        for claim in paid_claims:

            currency = (
                claim["currency"]
                or "INR"
            )

            self.paid_table.insert(
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

                    (
                        f"{currency} "
                        f"{claim['amount']:,.2f}"
                    ),

                    claim["paid_at"]
                )
            )

        self.payment_notebook.tab(
            self.paid_page,
            text=(
                f"Paid History "
                f"({len(paid_claims)})"
            )
        )


    def get_selected_ready_claims(self):

        selected = (
            self.ready_table.selection()
        )

        if not selected:

            messagebox.showwarning(
                "Select Claim",
                "Please select at least one claim."
            )

            return []

        return [
            self.ready_table.item(
                row,
                "values"
            )[0]

            for row in selected
        ]


    def pay_selected_claims(self):

        claim_ids = (
            self.get_selected_ready_claims()
        )

        if not claim_ids:

            return

        confirm = messagebox.askyesno(
            "Confirm Payment",
            (
                f"Mark {len(claim_ids)} "
                "claim(s) as Paid?\n\n"
                "Paid claims cannot be reversed."
            )
        )

        if not confirm:

            return

        success = 0
        errors = []

        for claim_id in claim_ids:

            try:

                mark_claim_paid(
                    claim_id=claim_id,
                    finance_employee_id=self.user[
                        "employee_id"
                    ]
                )

                success += 1

            except Exception as error:

                errors.append(
                    f"{claim_id}: {error}"
                )

        if success:

            messagebox.showinfo(
                "Payment Completed",
                (
                    f"{success} claim(s) "
                    "successfully marked Paid."
                )
            )

        if errors:

            messagebox.showerror(
                "Payment Error",
                "\n".join(
                    errors
                )
            )

        self.refresh_payments()

        self.refresh_analysis(
            show_no_data_popup=False
        )


    def view_selected_receipt(self):

        selected = (
            self.ready_table.selection()
        )

        if len(selected) != 1:

            messagebox.showwarning(
                "View Receipt",
                "Select exactly one claim."
            )

            return

        claim_id = self.ready_table.item(
            selected[0],
            "values"
        )[0]

        image_path = (
            get_claim_receipt_path(
                claim_id
            )
        )

        if not image_path:

            messagebox.showwarning(
                "Receipt",
                "Receipt image not available."
            )

            return

        path = Path(
            image_path
        )

        if not path.exists():

            messagebox.showerror(
                "Receipt",
                "Receipt file is missing."
            )

            return

        window = tk.Toplevel(
            self
        )

        window.title(
            f"Receipt - {claim_id}"
        )

        window.geometry(
            "850x700"
        )

        image = Image.open(
            path
        )

        image.thumbnail(
            (
                790,
                620
            )
        )

        photo = ImageTk.PhotoImage(
            image
        )

        label = ttk.Label(
            window,
            image=photo
        )

        label.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

        window.image_reference = photo


    # =====================================================
    # ANALYSIS DASHBOARD
    # =====================================================

    def create_analysis_page(self):

        self.analysis_background = tk.Frame(
            self.analysis_page,
            bg="#F3F4F6"
        )

        self.analysis_background.pack(
            fill="both",
            expand=True
        )

        # 25% Filters / 75% Analysis
        self.analysis_background.grid_columnconfigure(
            0,
            weight=2
        )

        self.analysis_background.grid_columnconfigure(
            1,
            weight=8
        )

        self.analysis_background.grid_rowconfigure(
            0,
            weight=1
        )

        self.filter_sidebar = tk.Frame(
            self.analysis_background,
            bg="#FFFFFF"
        )

        self.filter_sidebar.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 8)
        )

        right_area = tk.Frame(
            self.analysis_background,
            bg="#F3F4F6"
        )

        right_area.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        self.create_left_filters(
            self.filter_sidebar
        )

        self.create_scrollable_report(
            right_area
        )


    # =====================================================
    # LEFT FILTERS
    # =====================================================

    def create_left_filters(
        self,
        parent
    ):

        tk.Label(
            parent,
            text="FILTERS",
            font=(
                "Segoe UI",
                14,
                "bold"
            ),
            bg="#FFFFFF",
            fg="#111827"
        ).pack(
            anchor="w",
            padx=14,
            pady=(
                20,
                3
            )
        )

        tk.Label(
            parent,
            text="Refine expense analysis",
            font=(
                "Segoe UI",
                8
            ),
            bg="#FFFFFF",
            fg="#6B7280"
        ).pack(
            anchor="w",
            padx=14,
            pady=(
                0,
                18
            )
        )

        self.month_var = tk.StringVar(
            value="All Months"
        )

        self.employee_var = tk.StringVar(
            value="All Employees"
        )

        self.category_var = tk.StringVar(
            value="All Categories"
        )

        self.currency_var = tk.StringVar(
            value="INR"
        )

        self.create_filter_control(
            parent,
            "Month",
            self.month_var,
            "month"
        )

        self.create_filter_control(
            parent,
            "Employee ID",
            self.employee_var,
            "employee"
        )

        self.create_filter_control(
            parent,
            "Expense Category",
            self.category_var,
            "category"
        )

        self.create_filter_control(
            parent,
            "Currency",
            self.currency_var,
            "currency"
        )

        ttk.Button(
            parent,
            text="Apply Filters",
            command=lambda: self.refresh_analysis(
                show_no_data_popup=True
            ),
            style="Primary.TButton"
        ).pack(
            fill="x",
            padx=14,
            pady=(
                17,
                7
            )
        )

        ttk.Button(
            parent,
            text="Reset Filters",
            command=self.reset_filters
        ).pack(
            fill="x",
            padx=14
        )

        ttk.Separator(
            parent
        ).pack(
            fill="x",
            padx=14,
            pady=20
        )

        tk.Label(
            parent,
            text="TIP",
            font=(
                "Segoe UI",
                8,
                "bold"
            ),
            bg="#FFFFFF",
            fg="#374151"
        ).pack(
            anchor="w",
            padx=14
        )

        tk.Label(
            parent,
            text=(
                "Select filters to drill down "
                "into company spending."
            ),
            font=(
                "Segoe UI",
                8
            ),
            bg="#FFFFFF",
            fg="#6B7280",
            justify="left",
            wraplength=180
        ).pack(
            anchor="w",
            padx=14,
            pady=(4, 0)
        )


    def create_filter_control(
        self,
        parent,
        label,
        variable,
        filter_type
    ):

        tk.Label(
            parent,
            text=label,
            font=(
                "Segoe UI",
                9,
                "bold"
            ),
            bg="#FFFFFF",
            fg="#374151"
        ).pack(
            anchor="w",
            padx=14,
            pady=(
                7,
                4
            )
        )

        box = ttk.Combobox(
            parent,
            textvariable=variable,
            state="readonly",
            width=21
        )

        box.pack(
            fill="x",
            padx=14,
            pady=(0, 7)
        )

        if filter_type == "month":

            self.month_box = box

        elif filter_type == "employee":

            self.employee_box = box

        elif filter_type == "category":

            self.category_box = box

        elif filter_type == "currency":

            self.finance_currency_box = box


    # =====================================================
    # SCROLLABLE REPORT
    # =====================================================

    def create_scrollable_report(
        self,
        parent
    ):

        parent.grid_rowconfigure(
            0,
            weight=1
        )

        parent.grid_columnconfigure(
            0,
            weight=1
        )

        self.report_canvas = tk.Canvas(
            parent,
            bg="#F3F4F6",
            highlightthickness=0
        )

        self.report_scrollbar = ttk.Scrollbar(
            parent,
            orient="vertical",
            command=self.report_canvas.yview
        )

        self.report_canvas.configure(
            yscrollcommand=(
                self.report_scrollbar.set
            )
        )

        self.report_canvas.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.report_scrollbar.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        self.report_frame = tk.Frame(
            self.report_canvas,
            bg="#F3F4F6"
        )

        self.report_window_id = (
            self.report_canvas.create_window(
                (
                    0,
                    0
                ),
                window=self.report_frame,
                anchor="nw"
            )
        )

        self.report_frame.bind(
            "<Configure>",
            self.update_report_scrollregion
        )

        self.report_canvas.bind(
            "<Configure>",
            self.resize_report_frame
        )

        # Windows mouse wheel
        self.report_canvas.bind_all(
            "<MouseWheel>",
            self.on_report_mousewheel,
            add="+"
        )

        # Linux mouse wheel
        self.report_canvas.bind_all(
            "<Button-4>",
            self.on_report_mousewheel_linux,
            add="+"
        )

        self.report_canvas.bind_all(
            "<Button-5>",
            self.on_report_mousewheel_linux,
            add="+"
        )

        self.create_report_content()


    def update_report_scrollregion(
        self,
        event=None
    ):

        try:

            self.report_canvas.configure(
                scrollregion=(
                    self.report_canvas.bbox(
                        "all"
                    )
                )
            )

        except tk.TclError:

            pass


    def resize_report_frame(
        self,
        event
    ):

        try:

            self.report_canvas.itemconfigure(
                self.report_window_id,
                width=event.width
            )

        except tk.TclError:

            pass


    def mouse_is_over_report(self):

        try:

            if not self.report_canvas.winfo_exists():
                return False

            pointer_x = (
                self.report_canvas.winfo_pointerx()
                - self.report_canvas.winfo_rootx()
            )

            pointer_y = (
                self.report_canvas.winfo_pointery()
                - self.report_canvas.winfo_rooty()
            )

            width = (
                self.report_canvas.winfo_width()
            )

            height = (
                self.report_canvas.winfo_height()
            )

            return (
                0 <= pointer_x <= width
                and
                0 <= pointer_y <= height
            )

        except tk.TclError:

            return False


    def on_report_mousewheel(
        self,
        event
    ):

        if not self.mouse_is_over_report():

            return

        if event.delta > 0:

            direction = -3

        else:

            direction = 3

        try:

            self.report_canvas.yview_scroll(
                direction,
                "units"
            )

        except tk.TclError:

            pass

        return "break"


    def on_report_mousewheel_linux(
        self,
        event
    ):

        if not self.mouse_is_over_report():

            return

        direction = (
            -3
            if event.num == 4
            else 3
        )

        try:

            self.report_canvas.yview_scroll(
                direction,
                "units"
            )

        except tk.TclError:

            pass

        return "break"


    # =====================================================
    # REPORT CONTENT
    # =====================================================

    def create_report_content(self):

        top = tk.Frame(
            self.report_frame,
            bg="#F3F4F6"
        )

        top.pack(
            fill="x",
            padx=7,
            pady=(
                10,
                8
            )
        )

        tk.Label(
            top,
            text="Expense Analysis",
            font=(
                "Segoe UI",
                20,
                "bold"
            ),
            bg="#F3F4F6",
            fg="#111827"
        ).pack(
            anchor="w"
        )

        self.report_subtitle = tk.Label(
            top,
            text="Company expense overview",
            font=(
                "Segoe UI",
                9
            ),
            bg="#F3F4F6",
            fg="#6B7280"
        )

        self.report_subtitle.pack(
            anchor="w",
            pady=(2, 0)
        )

        self.create_kpi_area()

        self.create_business_insight_bar()

        self.create_chart_grid()

        self.create_alert_section()


    # =====================================================
    # KPI AREA
    # =====================================================

    def create_kpi_area(self):

        frame = tk.Frame(
            self.report_frame,
            bg="#F3F4F6"
        )

        frame.pack(
            fill="x",
            padx=6,
            pady=(
                4,
                11
            )
        )

        for column in range(6):

            frame.grid_columnconfigure(
                column,
                weight=1,
                uniform="kpi"
            )

        self.total_value = (
            self.create_kpi_card(
                frame,
                0,
                "Total Filed",
                "Submitted expenses"
            )
        )

        self.ready_value = (
            self.create_kpi_card(
                frame,
                1,
                "Ready To Pay",
                "Manager approved"
            )
        )

        self.paid_value = (
            self.create_kpi_card(
                frame,
                2,
                "Paid",
                "Reimbursements"
            )
        )

        self.claim_count_value = (
            self.create_kpi_card(
                frame,
                3,
                "Total Claims",
                "Claim volume"
            )
        )

        self.limit_value = (
            self.create_kpi_card(
                frame,
                4,
                "Over Limit",
                "Limit violations"
            )
        )

        self.duplicate_value = (
            self.create_kpi_card(
                frame,
                5,
                "Duplicate Alerts",
                "Receipt alerts"
            )
        )


    def create_kpi_card(
        self,
        parent,
        column,
        title,
        subtitle
    ):

        card = tk.Frame(
            parent,
            bg="#FFFFFF",
            highlightthickness=1,
            highlightbackground="#E5E7EB"
        )

        card.grid(
            row=0,
            column=column,
            sticky="nsew",
            padx=3,
            pady=4
        )

        inner = tk.Frame(
            card,
            bg="#FFFFFF"
        )

        inner.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        tk.Label(
            inner,
            text=title,
            font=(
                "Segoe UI",
                8,
                "bold"
            ),
            bg="#FFFFFF",
            fg="#4B5563"
        ).pack(
            anchor="w"
        )

        value = tk.Label(
            inner,
            text="0",
            font=(
                "Segoe UI",
                13,
                "bold"
            ),
            bg="#FFFFFF",
            fg="#111827"
        )

        value.pack(
            anchor="w",
            pady=(
                6,
                2
            )
        )

        tk.Label(
            inner,
            text=subtitle,
            font=(
                "Segoe UI",
                6
            ),
            bg="#FFFFFF",
            fg="#9CA3AF",
            wraplength=130,
            justify="left"
        ).pack(
            anchor="w"
        )

        return value


    # =====================================================
    # BUSINESS INSIGHTS
    # =====================================================

    def create_business_insight_bar(self):

        card = tk.Frame(
            self.report_frame,
            bg="#FFFFFF",
            highlightbackground="#E5E7EB",
            highlightthickness=1
        )

        card.pack(
            fill="x",
            padx=10,
            pady=(
                0,
                12
            )
        )

        tk.Label(
            card,
            text="Business Insight",
            font=(
                "Segoe UI",
                10,
                "bold"
            ),
            bg="#FFFFFF",
            fg="#111827"
        ).pack(
            anchor="w",
            padx=14,
            pady=(
                9,
                2
            )
        )

        self.insight_var = tk.StringVar(
            value="No analysis available."
        )

        tk.Label(
            card,
            textvariable=self.insight_var,
            font=(
                "Segoe UI",
                8
            ),
            bg="#FFFFFF",
            fg="#4B5563",
            justify="left",
            wraplength=1100
        ).pack(
            anchor="w",
            padx=14,
            pady=(
                0,
                9
            )
        )


    # =====================================================
    # CHART GRID
    # =====================================================

    def create_chart_grid(self):

        grid = tk.Frame(
            self.report_frame,
            bg="#F3F4F6"
        )

        grid.pack(
            fill="both",
            expand=True,
            padx=6
        )

        grid.grid_columnconfigure(
            0,
            weight=1
        )

        grid.grid_columnconfigure(
            1,
            weight=1
        )

        (
            self.trend_ax,
            self.trend_canvas
        ) = self.create_chart_card(
            grid,
            0,
            0,
            "Expense Trend",
            "Month-wise / day-wise spending"
        )

        (
            self.category_ax,
            self.category_canvas
        ) = self.create_chart_card(
            grid,
            0,
            1,
            "Expense Breakdown",
            "Contribution by category"
        )

        (
            self.employee_ax,
            self.employee_canvas
        ) = self.create_chart_card(
            grid,
            1,
            0,
            "Employee Spending",
            "Employees ranked by spend"
        )

        (
            self.status_ax,
            self.status_canvas
        ) = self.create_chart_card(
            grid,
            1,
            1,
            "Claim Status",
            "Current reimbursement workflow"
        )


    def create_chart_card(
        self,
        parent,
        row,
        column,
        title,
        subtitle
    ):

        card = tk.Frame(
            parent,
            bg="#FFFFFF",
            highlightbackground="#E5E7EB",
            highlightthickness=1
        )

        card.grid(
            row=row,
            column=column,
            sticky="nsew",
            padx=4,
            pady=4
        )

        tk.Label(
            card,
            text=title,
            font=(
                "Segoe UI",
                11,
                "bold"
            ),
            bg="#FFFFFF",
            fg="#111827"
        ).pack(
            anchor="w",
            padx=12,
            pady=(
                9,
                0
            )
        )

        tk.Label(
            card,
            text=subtitle,
            font=(
                "Segoe UI",
                7
            ),
            bg="#FFFFFF",
            fg="#9CA3AF"
        ).pack(
            anchor="w",
            padx=12,
            pady=(
                1,
                0
            )
        )

        figure = Figure(
            figsize=(
                5.3,
                3.1
            ),
            dpi=100
        )

        figure.patch.set_facecolor(
            "#FFFFFF"
        )

        axis = figure.add_subplot(
            111
        )

        canvas = FigureCanvasTkAgg(
            figure,
            master=card
        )

        canvas.get_tk_widget().pack(
            fill="both",
            expand=True,
            padx=6,
            pady=6
        )

        return (
            axis,
            canvas
        )


    # =====================================================
    # LIMIT ALERT SECTION
    # =====================================================

    def create_alert_section(self):

        card = tk.Frame(
            self.report_frame,
            bg="#FFFFFF",
            highlightbackground="#E5E7EB",
            highlightthickness=1
        )

        card.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(
                10,
                20
            )
        )

        tk.Label(
            card,
            text="Expense Limit Alerts",
            font=(
                "Segoe UI",
                12,
                "bold"
            ),
            bg="#FFFFFF",
            fg="#111827"
        ).pack(
            anchor="w",
            padx=12,
            pady=(
                10,
                7
            )
        )

        columns = (
            "claim",
            "employee",
            "category",
            "amount",
            "exceeded"
        )

        self.limit_table = ttk.Treeview(
            card,
            columns=columns,
            show="headings",
            height=5,
            style="Finance.Treeview"
        )

        headings = {
            "claim": "Claim ID",
            "employee": "Employee",
            "category": "Category",
            "amount": "Expense",
            "exceeded": "Exceeded By"
        }

        for column in columns:

            self.limit_table.heading(
                column,
                text=headings[column]
            )

        self.limit_table.column(
            "claim",
            width=180
        )

        self.limit_table.column(
            "employee",
            width=220
        )

        self.limit_table.column(
            "category",
            width=190
        )

        self.limit_table.column(
            "amount",
            width=130
        )

        self.limit_table.column(
            "exceeded",
            width=130
        )

        self.limit_table.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=(
                0,
                12
            )
        )


    # =====================================================
    # FILTER OPTIONS
    # =====================================================

    def load_filter_options(self):

        options = (
            get_finance_filter_options()
        )

        months = [
            "All Months"
        ]

        self.month_map = {
            "All Months": None
        }

        for month_key in options[
            "months"
        ]:

            try:

                display = datetime.strptime(
                    month_key,
                    "%Y-%m"
                ).strftime(
                    "%B %Y"
                )

            except ValueError:

                display = month_key

            months.append(
                display
            )

            self.month_map[
                display
            ] = month_key

        self.month_box[
            "values"
        ] = months

        employees = [
            "All Employees"
        ]

        self.employee_map = {
            "All Employees": None
        }

        for employee in options[
            "employees"
        ]:

            display = (
                f"{employee['employee_id']} - "
                f"{employee['full_name']}"
            )

            employees.append(
                display
            )

            self.employee_map[
                display
            ] = employee[
                "employee_id"
            ]

        self.employee_box[
            "values"
        ] = employees

        categories = [
            "All Categories"
        ]

        self.category_map = {
            "All Categories": None
        }

        for category in options[
            "categories"
        ]:

            name = category[
                "category_name"
            ]

            categories.append(
                name
            )

            self.category_map[
                name
            ] = category[
                "category_id"
            ]

        self.category_box[
            "values"
        ] = categories

        currencies = list(
            options[
                "currencies"
            ]
        )

        if "INR" not in currencies:

            currencies.insert(
                0,
                "INR"
            )

        self.finance_currency_box[
            "values"
        ] = currencies

        self.month_var.set(
            "All Months"
        )

        self.employee_var.set(
            "All Employees"
        )

        self.category_var.set(
            "All Categories"
        )

        self.currency_var.set(
            "INR"
        )


    def reset_filters(self):

        self.month_var.set(
            "All Months"
        )

        self.employee_var.set(
            "All Employees"
        )

        self.category_var.set(
            "All Categories"
        )

        self.currency_var.set(
            "INR"
        )

        self.refresh_analysis(
            show_no_data_popup=False
        )


    # =====================================================
    # ANALYSIS REFRESH
    # =====================================================

    def refresh_analysis(
        self,
        show_no_data_popup=True
    ):

        month_key = (
            self.month_map.get(
                self.month_var.get()
            )
        )

        employee_id = (
            self.employee_map.get(
                self.employee_var.get()
            )
        )

        category_id = (
            self.category_map.get(
                self.category_var.get()
            )
        )

        currency = (
            self.currency_var.get()
            or "INR"
        )

        try:

            data = get_finance_analysis(
                month_key=month_key,
                employee_id=employee_id,
                category_id=category_id,
                currency=currency
            )

        except Exception as error:

            messagebox.showerror(
                "Analytics Error",
                str(error)
            )

            return

        summary = data[
            "summary"
        ]

        claim_count = int(
            summary[
                "claim_count"
            ]
            or 0
        )

        self.total_value.config(
            text=(
                f"{currency} "
                f"{float(summary['total_claimed'] or 0):,.2f}"
            )
        )

        self.ready_value.config(
            text=(
                f"{currency} "
                f"{float(summary['approved_amount'] or 0):,.2f}"
            )
        )

        self.paid_value.config(
            text=(
                f"{currency} "
                f"{float(summary['paid_amount'] or 0):,.2f}"
            )
        )

        self.claim_count_value.config(
            text=str(
                claim_count
            )
        )

        self.limit_value.config(
            text=str(
                summary[
                    "over_limit_count"
                ]
                or 0
            )
        )

        self.duplicate_value.config(
            text=str(
                summary[
                    "duplicate_count"
                ]
                or 0
            )
        )

        self.draw_trend_chart(
            data[
                "trend"
            ],
            currency
        )

        self.draw_category_chart(
            data[
                "category_spend"
            ],
            currency
        )

        self.draw_employee_chart(
            data[
                "employee_spend"
            ],
            currency
        )

        self.draw_status_chart(
            data[
                "status_counts"
            ]
        )

        self.populate_limit_alerts(
            data[
                "limit_alerts"
            ]
        )

        self.update_insights(
            data,
            currency
        )

        self.update_report_subtitle()

        if (
            claim_count == 0
            and show_no_data_popup
        ):

            messagebox.showinfo(
                "No Data Found",
                (
                    "No expense data matches the "
                    "selected filters.\n\n"
                    "Please change one or more filters:\n\n"
                    "• Month\n"
                    "• Employee ID\n"
                    "• Expense Category\n"
                    "• Currency\n\n"
                    "Then click Apply Filters again."
                ),
                parent=self
            )


    def update_report_subtitle(self):

        self.report_subtitle.config(
            text=(
                f"{self.month_var.get()}  •  "
                f"{self.employee_var.get()}  •  "
                f"{self.category_var.get()}  •  "
                f"{self.currency_var.get()}"
            )
        )


    # =====================================================
    # GRAPH HELPERS
    # =====================================================

    def prepare_axis(
        self,
        axis
    ):

        axis.clear()

        axis.set_facecolor(
            "#FFFFFF"
        )

        axis.spines[
            "top"
        ].set_visible(
            False
        )

        axis.spines[
            "right"
        ].set_visible(
            False
        )

        axis.spines[
            "left"
        ].set_visible(
            False
        )

        axis.grid(
            axis="y",
            alpha=0.15
        )

        axis.tick_params(
            labelsize=8
        )


    def draw_trend_chart(
        self,
        rows,
        currency
    ):

        axis = self.trend_ax

        self.prepare_axis(
            axis
        )

        if not rows:

            self.show_no_data(
                axis
            )

            self.trend_canvas.draw()

            return

        periods = [
            row["period"]
            for row in rows
        ]

        values = [
            float(
                row["total"]
            )
            for row in rows
        ]

        axis.plot(
            periods,
            values,
            marker="o",
            linewidth=2.2
        )

        axis.fill_between(
            periods,
            values,
            alpha=0.12
        )

        axis.set_ylabel(
            currency,
            fontsize=8
        )

        axis.tick_params(
            axis="x",
            rotation=30
        )

        if len(values) == 1:

            axis.set_ylim(
                bottom=0
            )

        self.trend_canvas.figure.tight_layout(
            pad=2
        )

        self.trend_canvas.draw()


    def draw_category_chart(
        self,
        rows,
        currency
    ):

        axis = self.category_ax

        axis.clear()

        axis.set_facecolor(
            "#FFFFFF"
        )

        if not rows:

            self.show_no_data(
                axis
            )

            self.category_canvas.draw()

            return

        rows = sorted(
            rows,
            key=lambda row: row[
                "total"
            ],
            reverse=True
        )

        labels = [
            row[
                "category_name"
            ]
            or "Unknown"

            for row in rows
        ]

        values = [
            float(
                row[
                    "total"
                ]
            )

            for row in rows
        ]

        total = sum(
            values
        )

        if total <= 0:

            self.show_no_data(
                axis
            )

            self.category_canvas.draw()

            return

        wedges, _, autotexts = (
            axis.pie(
                values,
                autopct="%1.0f%%",
                startangle=90,
                pctdistance=0.78,
                wedgeprops={
                    "width": 0.42
                }
            )
        )

        for text in autotexts:

            text.set_fontsize(
                8
            )

        axis.text(
            0,
            0,
            (
                f"{currency}\n"
                f"{total:,.0f}"
            ),
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold"
        )

        axis.legend(
            wedges,
            labels,
            loc="center left",
            bbox_to_anchor=(
                0.9,
                0.5
            ),
            fontsize=7,
            frameon=False
        )

        self.category_canvas.figure.tight_layout(
            pad=2
        )

        self.category_canvas.draw()


    def draw_employee_chart(
        self,
        rows,
        currency
    ):

        axis = self.employee_ax

        axis.clear()

        axis.set_facecolor(
            "#FFFFFF"
        )

        axis.spines[
            "top"
        ].set_visible(
            False
        )

        axis.spines[
            "right"
        ].set_visible(
            False
        )

        if not rows:

            self.show_no_data(
                axis
            )

            self.employee_canvas.draw()

            return

        rows = sorted(
            rows,
            key=lambda row: row[
                "total"
            ]
        )

        rows = rows[
            -8:
        ]

        names = [
            (
                f"{row['employee_id']} "
                f"{row['full_name']}"
            )

            for row in rows
        ]

        values = [
            float(
                row[
                    "total"
                ]
            )

            for row in rows
        ]

        bars = axis.barh(
            names,
            values
        )

        axis.set_xlabel(
            currency,
            fontsize=8
        )

        axis.tick_params(
            labelsize=7
        )

        axis.grid(
            axis="x",
            alpha=0.15
        )

        for bar, value in zip(
            bars,
            values
        ):

            axis.text(
                value,
                (
                    bar.get_y()
                    + bar.get_height()
                    / 2
                ),
                (
                    f" {value:,.0f}"
                ),
                va="center",
                fontsize=7
            )

        self.employee_canvas.figure.tight_layout(
            pad=2
        )

        self.employee_canvas.draw()


    def draw_status_chart(
        self,
        rows
    ):

        axis = self.status_ax

        axis.clear()

        axis.set_facecolor(
            "#FFFFFF"
        )

        if not rows:

            self.show_no_data(
                axis
            )

            self.status_canvas.draw()

            return

        labels = [
            row["status"]
            for row in rows
        ]

        values = [
            int(
                row["total"]
            )
            for row in rows
        ]

        total = sum(
            values
        )

        wedges, _, autotexts = (
            axis.pie(
                values,
                autopct="%1.0f%%",
                startangle=90,
                pctdistance=0.78,
                wedgeprops={
                    "width": 0.42
                }
            )
        )

        for text in autotexts:

            text.set_fontsize(
                8
            )

        axis.text(
            0,
            0,
            str(
                total
            ),
            ha="center",
            va="center",
            fontsize=16,
            fontweight="bold"
        )

        axis.legend(
            wedges,
            [
                (
                    f"{label} "
                    f"({value})"
                )

                for label, value
                in zip(
                    labels,
                    values
                )
            ],
            loc="center left",
            bbox_to_anchor=(
                0.9,
                0.5
            ),
            fontsize=7,
            frameon=False
        )

        self.status_canvas.figure.tight_layout(
            pad=2
        )

        self.status_canvas.draw()


    def show_no_data(
        self,
        axis
    ):

        axis.clear()

        axis.text(
            0.5,
            0.5,
            (
                "No data available\n"
                "Change the filters"
            ),
            horizontalalignment="center",
            verticalalignment="center",
            transform=axis.transAxes,
            fontsize=10,
            color="#6B7280"
        )

        axis.set_xticks(
            []
        )

        axis.set_yticks(
            []
        )


    # =====================================================
    # LIMIT ALERTS
    # =====================================================

    def populate_limit_alerts(
        self,
        alerts
    ):

        for item in (
            self.limit_table.get_children()
        ):

            self.limit_table.delete(
                item
            )

        for alert in alerts:

            currency = (
                alert["currency"]
                or "INR"
            )

            self.limit_table.insert(
                "",
                "end",
                values=(
                    alert[
                        "claim_id"
                    ],

                    (
                        f"{alert['employee_id']} - "
                        f"{alert['full_name']}"
                    ),

                    alert[
                        "category_name"
                    ],

                    (
                        f"{currency} "
                        f"{alert['amount']:,.2f}"
                    ),

                    (
                        f"{currency} "
                        f"{alert['limit_exceeded_by']:,.2f}"
                    )
                )
            )


    # =====================================================
    # BUSINESS INSIGHTS
    # =====================================================

    def update_insights(
        self,
        data,
        currency
    ):

        summary = data[
            "summary"
        ]

        total = float(
            summary[
                "total_claimed"
            ]
            or 0
        )

        paid = float(
            summary[
                "paid_amount"
            ]
            or 0
        )

        ready = float(
            summary[
                "approved_amount"
            ]
            or 0
        )

        if total > 0:

            paid_percentage = (
                paid
                / total
                * 100
            )

        else:

            paid_percentage = 0

        category_text = (
            "No category spending available"
        )

        if data[
            "category_spend"
        ]:

            top_category = max(
                data[
                    "category_spend"
                ],
                key=lambda row: row[
                    "total"
                ]
            )

            category_text = (
                f"Highest category: "
                f"{top_category['category_name']} "
                f"({currency} "
                f"{float(top_category['total']):,.2f})"
            )

        employee_text = (
            "No employee spending available"
        )

        if data[
            "employee_spend"
        ]:

            top_employee = max(
                data[
                    "employee_spend"
                ],
                key=lambda row: row[
                    "total"
                ]
            )

            employee_text = (
                f"Highest spender: "
                f"{top_employee['full_name']} "
                f"({currency} "
                f"{float(top_employee['total']):,.2f})"
            )

        self.insight_var.set(
            (
                f"{category_text}   •   "
                f"{employee_text}   •   "
                f"Paid: {paid_percentage:.1f}%   •   "
                f"Waiting for payment: "
                f"{currency} {ready:,.2f}"
            )
        )