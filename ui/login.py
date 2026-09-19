import tkinter as tk

from tkinter import ttk
from tkinter import messagebox

from services.auth_service import authenticate_user


class LoginFrame(ttk.Frame):

    def __init__(
        self,
        parent,
        login_success_callback
    ):
        super().__init__(
            parent,
            padding=0
        )

        self.parent = parent
        self.login_success_callback = (
            login_success_callback
        )

        self.login_popup = None

        self.pack(
            fill="both",
            expand=True
        )

        self.setup_styles()
        self.build_ui()


    # =====================================================
    # STYLES
    # =====================================================

    def setup_styles(self):

        style = ttk.Style()

        try:
            style.theme_use("clam")

        except tk.TclError:
            pass

        style.configure(
            "Landing.TButton",
            font=(
                "Segoe UI",
                10,
                "bold"
            ),
            padding=10
        )

        style.configure(
            "Secondary.TButton",
            font=(
                "Segoe UI",
                10
            ),
            padding=10
        )

        style.configure(
            "PopupLogin.TButton",
            font=(
                "Segoe UI",
                11,
                "bold"
            ),
            padding=10
        )


    # =====================================================
    # MAIN HOMEPAGE
    # =====================================================

    def build_ui(self):

        outer = tk.Frame(
            self,
            bg="#EDEBE9"
        )

        outer.pack(
            fill="both",
            expand=True
        )

        card = tk.Frame(
            outer,
            bg="#FFFFFF",
            bd=1,
            relief="solid"
        )

        card.place(
            relx=0.5,
            rely=0.5,
            anchor="center",
            relwidth=0.93,
            relheight=0.86
        )

        self.build_topbar(
            card
        )

        self.build_body(
            card
        )


    # =====================================================
    # TOP NAVIGATION
    # =====================================================

    def build_topbar(
        self,
        parent
    ):

        topbar = tk.Frame(
            parent,
            bg="#FFFFFF",
            height=60
        )

        topbar.pack(
            fill="x",
            padx=22,
            pady=(14, 4)
        )

        topbar.pack_propagate(
            False
        )

        brand = tk.Frame(
            topbar,
            bg="#FFFFFF"
        )

        brand.pack(
            side="left",
            fill="y"
        )

        tk.Label(
            brand,
            text="Expense Claims",
            font=(
                "Segoe UI",
                14,
                "bold"
            ),
            bg="#FFFFFF",
            fg="#111827"
        ).pack(
            anchor="w"
        )

        tk.Label(
            brand,
            text="VSP TECHVERSE",
            font=(
                "Segoe UI",
                8
            ),
            bg="#FFFFFF",
            fg="#6B7280"
        ).pack(
            anchor="w"
        )

        nav = tk.Frame(
            topbar,
            bg="#FFFFFF"
        )

        nav.pack(
            side="left",
            padx=(60, 0)
        )

        for item in [
            "Home",
            "Claims Flow",
            "Roles"
        ]:

            tk.Label(
                nav,
                text=item,
                font=(
                    "Segoe UI",
                    9
                ),
                bg="#FFFFFF",
                fg="#6B7280",
                padx=14
            ).pack(
                side="left"
            )

        # Top-right Login button
        ttk.Button(
            topbar,
            text="Login",
            style="Landing.TButton",
            command=self.open_login_popup
        ).pack(
            side="right"
        )


    # =====================================================
    # MAIN BODY
    # =====================================================

    def build_body(
        self,
        parent
    ):

        body = tk.Frame(
            parent,
            bg="#FFFFFF"
        )

        body.pack(
            fill="both",
            expand=True,
            padx=26,
            pady=(6, 24)
        )

        body.grid_columnconfigure(
            0,
            weight=5
        )

        body.grid_columnconfigure(
            1,
            weight=5
        )

        body.grid_rowconfigure(
            0,
            weight=1
        )

        left = tk.Frame(
            body,
            bg="#FFFFFF"
        )

        left.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(8, 28)
        )

        right = tk.Frame(
            body,
            bg="#FFFFFF"
        )

        right.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        self.build_hero_section(
            left
        )

        self.build_illustration_section(
            right
        )


    # =====================================================
    # LEFT HERO
    # =====================================================

    def build_hero_section(
        self,
        parent
    ):

        content = tk.Frame(
            parent,
            bg="#FFFFFF"
        )

        content.place(
            relx=0.05,
            rely=0.20,
            anchor="nw"
        )

        tk.Label(
            content,
            text="SMART EXPENSE WORKFLOW",
            font=(
                "Segoe UI",
                8,
                "bold"
            ),
            bg="#FFFFFF",
            fg="#6B7280"
        ).pack(
            anchor="w",
            pady=(0, 12)
        )

        tk.Label(
            content,
            text=(
                "Streamline your\n"
                "expense claim management."
            ),
            font=(
                "Segoe UI",
                16,
                "bold"
            ),
            bg="#FFFFFF",
            fg="#111827",
            justify="left"
        ).pack(
            anchor="w"
        )

        tk.Label(
            content,
            text=(
                "Upload receipts, extract claim details, "
                "route \n them to managers for approval and \n "
                "let Finance complete reimbursement and \n "
                "analyse company spending."
            ),
            font=(
                "Segoe UI",
                10
            ),
            bg="#FFFFFF",
            fg="#6B7280",
            wraplength=510,
            justify="left"
        ).pack(
            anchor="w",
            pady=(18, 20)
        )

        button_frame = tk.Frame(
            content,
            bg="#FFFFFF"
        )

        button_frame.pack(
            anchor="w",
            pady=(0, 24)
        )

        # Opens login popup
        ttk.Button(
            button_frame,
            text="Login Now",
            style="Landing.TButton",
            command=self.open_login_popup
        ).pack(
            side="left",
            padx=(0, 10)
        )

        ttk.Button(
            button_frame,
            text="How It Works",
            style="Secondary.TButton",
            command=self.show_how_it_works
        ).pack(
            side="left"
        )

        features = tk.Frame(
            content,
            bg="#FFFFFF"
        )

        features.pack(
            anchor="w"
        )

        feature_texts = [
            "Receipt upload and OCR extraction",
            "Manager approval hierarchy",
            "Duplicate receipt protection",
            "Finance payment and analytics"
        ]

        for feature in feature_texts:

            row = tk.Frame(
                features,
                bg="#FFFFFF"
            )

            row.pack(
                anchor="w",
                pady=5
            )

            tk.Label(
                row,
                text="●",
                font=(
                    "Segoe UI",
                    9
                ),
                bg="#FFFFFF",
                fg="#2563EB"
            ).pack(
                side="left"
            )

            tk.Label(
                row,
                text=feature,
                font=(
                    "Segoe UI",
                    9
                ),
                bg="#FFFFFF",
                fg="#374151",
                padx=8
            ).pack(
                side="left"
            )


    # =====================================================
    # RIGHT ILLUSTRATION
    # =====================================================

    def build_illustration_section(
        self,
        parent
    ):

        card = tk.Frame(
            parent,
            bg="#F8FAFC",
            bd=1,
            relief="solid"
        )

        card.pack(
            fill="both",
            expand=True,
            padx=8,
            pady=8
        )

        tk.Label(
            card,
            text="Expense workflow",
            font=(
                "Segoe UI",
                14,
                "bold"
            ),
            bg="#F8FAFC",
            fg="#111827"
        ).pack(
            anchor="w",
            padx=24,
            pady=(25, 4)
        )

        tk.Label(
            card,
            text="Receipt → Approval → Payment → Analysis",
            font=(
                "Segoe UI",
                9
            ),
            bg="#F8FAFC",
            fg="#6B7280"
        ).pack(
            anchor="w",
            padx=24
        )

        canvas = tk.Canvas(
            card,
            bg="#F8FAFC",
            highlightthickness=0
        )

        canvas.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=15
        )

        # Platform
        canvas.create_oval(
            210,
            330,
            500,
            390,
            fill="#E5E7EB",
            outline=""
        )

        # Decorative people / workflow graphic
        canvas.create_oval(
            300,
            175,
            365,
            350,
            fill="#FBBF24",
            outline=""
        )

        canvas.create_oval(
            365,
            195,
            430,
            355,
            fill="#2563EB",
            outline=""
        )

        canvas.create_oval(
            245,
            235,
            315,
            365,
            fill="#60A5FA",
            outline=""
        )

        canvas.create_oval(
            330,
            245,
            400,
            370,
            fill="#93C5FD",
            outline=""
        )

        canvas.create_oval(
            415,
            255,
            485,
            365,
            fill="#FCD34D",
            outline=""
        )

        # Receipt/mobile device
        canvas.create_rectangle(
            340,
            90,
            395,
            225,
            fill="#111827",
            outline=""
        )

        canvas.create_rectangle(
            351,
            110,
            384,
            180,
            fill="#FBBF24",
            outline=""
        )

        canvas.create_text(
            367,
            198,
            text="₹",
            font=(
                "Segoe UI",
                14,
                "bold"
            ),
            fill="#FFFFFF"
        )

        self.draw_workflow_badge(
            canvas,
            70,
            160,
            "1",
            "Upload"
        )

        self.draw_workflow_badge(
            canvas,
            70,
            220,
            "2",
            "Approve"
        )

        self.draw_workflow_badge(
            canvas,
            70,
            280,
            "3",
            "Pay"
        )

        self.draw_workflow_badge(
            canvas,
            70,
            340,
            "4",
            "Analyse"
        )


    def draw_workflow_badge(
        self,
        canvas,
        x,
        y,
        number,
        text
    ):

        canvas.create_oval(
            x,
            y,
            x + 30,
            y + 30,
            fill="#2563EB",
            outline=""
        )

        canvas.create_text(
            x + 15,
            y + 15,
            text=number,
            font=(
                "Segoe UI",
                8,
                "bold"
            ),
            fill="#FFFFFF"
        )

        canvas.create_rectangle(
            x + 40,
            y,
            x + 140,
            y + 30,
            fill="#FFFFFF",
            outline="#D1D5DB"
        )

        canvas.create_text(
            x + 90,
            y + 15,
            text=text,
            font=(
                "Segoe UI",
                8,
                "bold"
            ),
            fill="#374151"
        )


    # =====================================================
    # LOGIN POPUP
    # =====================================================

    def open_login_popup(self):

        # If popup is already open, bring it forward
        if (
            self.login_popup is not None
            and self.login_popup.winfo_exists()
        ):

            self.login_popup.lift()
            self.login_popup.focus_force()

            return

        self.login_popup = tk.Toplevel(
            self
        )

        self.login_popup.title(
            "Login - Expense Claims"
        )

        self.login_popup.geometry(
            "460x430"
        )

        self.login_popup.resizable(
            False,
            False
        )

        self.login_popup.configure(
            bg="#FFFFFF"
        )

        # Keep popup above homepage
        self.login_popup.transient(
            self.parent
        )

        self.login_popup.grab_set()

        # Center popup
        self.login_popup.update_idletasks()

        screen_width = (
            self.login_popup.winfo_screenwidth()
        )

        screen_height = (
            self.login_popup.winfo_screenheight()
        )

        popup_width = 460
        popup_height = 430

        x = (
            screen_width
            // 2
            - popup_width
            // 2
        )

        y = (
            screen_height
            // 2
            - popup_height
            // 2
        )

        self.login_popup.geometry(
            f"{popup_width}x{popup_height}"
            f"+{x}+{y}"
        )

        self.popup_login_var = (
            tk.StringVar()
        )

        self.popup_password_var = (
            tk.StringVar()
        )

        container = tk.Frame(
            self.login_popup,
            bg="#FFFFFF"
        )

        container.pack(
            fill="both",
            expand=True,
            padx=42,
            pady=32
        )

        tk.Label(
            container,
            text="Welcome Back",
            font=(
                "Segoe UI",
                22,
                "bold"
            ),
            bg="#FFFFFF",
            fg="#111827"
        ).pack(
            anchor="w"
        )

        tk.Label(
            container,
            text=(
                "Login to access your expense workspace."
            ),
            font=(
                "Segoe UI",
                9
            ),
            bg="#FFFFFF",
            fg="#6B7280"
        ).pack(
            anchor="w",
            pady=(5, 25)
        )

        tk.Label(
            container,
            text="Employee ID / Email",
            font=(
                "Segoe UI",
                9,
                "bold"
            ),
            bg="#FFFFFF",
            fg="#374151"
        ).pack(
            anchor="w"
        )

        self.popup_login_entry = tk.Entry(
            container,
            textvariable=self.popup_login_var,
            font=(
                "Segoe UI",
                11
            ),
            relief="solid",
            bd=1
        )

        self.popup_login_entry.pack(
            fill="x",
            pady=(7, 18),
            ipady=8
        )

        tk.Label(
            container,
            text="Password",
            font=(
                "Segoe UI",
                9,
                "bold"
            ),
            bg="#FFFFFF",
            fg="#374151"
        ).pack(
            anchor="w"
        )

        self.popup_password_entry = tk.Entry(
            container,
            textvariable=self.popup_password_var,
            font=(
                "Segoe UI",
                11
            ),
            relief="solid",
            bd=1,
            show="*"
        )

        self.popup_password_entry.pack(
            fill="x",
            pady=(7, 22),
            ipady=8
        )

        ttk.Button(
            container,
            text="Login",
            style="PopupLogin.TButton",
            command=self.attempt_popup_login
        ).pack(
            fill="x"
        )

        ttk.Button(
            container,
            text="Cancel",
            style="Secondary.TButton",
            command=self.close_login_popup
        ).pack(
            fill="x",
            pady=(10, 0)
        )

        self.popup_login_entry.focus_set()

        # Enter key login
        self.login_popup.bind(
            "<Return>",
            lambda event:
            self.attempt_popup_login()
        )

        # Proper close
        self.login_popup.protocol(
            "WM_DELETE_WINDOW",
            self.close_login_popup
        )


    # =====================================================
    # POPUP AUTHENTICATION
    # =====================================================

    def attempt_popup_login(self):

        login_value = (
            self.popup_login_var
            .get()
            .strip()
        )

        password = (
            self.popup_password_var
            .get()
        )

        if not login_value:

            messagebox.showwarning(
                "Login",
                "Enter Employee ID or Email.",
                parent=self.login_popup
            )

            self.popup_login_entry.focus_set()

            return

        if not password:

            messagebox.showwarning(
                "Login",
                "Enter password.",
                parent=self.login_popup
            )

            self.popup_password_entry.focus_set()

            return

        try:

            user = authenticate_user(
                login_value,
                password
            )

        except Exception as error:

            messagebox.showerror(
                "Login Error",
                str(error),
                parent=self.login_popup
            )

            return

        if not user:

            messagebox.showerror(
                "Login Failed",
                (
                    "Invalid Employee ID, "
                    "email or password."
                ),
                parent=self.login_popup
            )

            return

        # Save callback before destroying popup
        callback = (
            self.login_success_callback
        )

        self.close_login_popup()

        callback(
            user
        )


    def close_login_popup(self):

        if (
            self.login_popup is not None
            and self.login_popup.winfo_exists()
        ):

            try:
                self.login_popup.grab_release()

            except tk.TclError:
                pass

            self.login_popup.destroy()

        self.login_popup = None


    # =====================================================
    # HOW IT WORKS
    # =====================================================

    def show_how_it_works(self):

        messagebox.showinfo(
            "How It Works",
            (
                "1. Staff uploads receipt or invoice.\n\n"
                "2. OCR extracts merchant, date, amount "
                "and category.\n\n"
                "3. Employee reviews and submits the claim.\n\n"
                "4. Manager approves or rejects it.\n\n"
                "5. Finance pays approved claims.\n\n"
                "6. Finance analyses expenses, categories, "
                "limits and duplicate alerts."
            ),
            parent=self
        )