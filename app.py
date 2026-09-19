import tkinter as tk

from tkinter import ttk

from ui.login import LoginFrame
from ui.staff_dashboard import StaffDashboard
from ui.manager_dashboard import ManagerDashboard
from ui.finance_dashboard import FinanceDashboard


class ExpenseClaimsApp(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title(
            "Expense Claims - VSP TECHVERSE"
        )

        self.geometry(
            "1200x720"
        )

        self.minsize(
            1000,
            650
        )

        self.current_frame = None
        self.current_user = None

        self.setup_style()

        self.show_login()


    def setup_style(self):

        style = ttk.Style(self)

        try:
            style.theme_use(
                "clam"
            )
        except tk.TclError:
            pass

        style.configure(
            "TButton",
            font=(
                "Segoe UI",
                11
            )
        )

        style.configure(
            "TLabel",
            font=(
                "Segoe UI",
                11
            )
        )


    def clear_screen(self):

        if self.current_frame:

            self.current_frame.destroy()

            self.current_frame = None


    def show_login(self):

        self.clear_screen()

        self.current_user = None

        self.current_frame = LoginFrame(
            self,
            self.login_success
        )


    def login_success(self, user):

        self.current_user = user

        self.clear_screen()

        role = user["role"]

        if role == "Staff":

            self.current_frame = StaffDashboard(
                self,
                user,
                self.show_login
            )

        elif role == "Manager":

            self.current_frame = ManagerDashboard(
                self,
                user,
                self.show_login
            )

        elif role == "Finance":

            self.current_frame = FinanceDashboard(
                self,
                user,
                self.show_login
            )

        else:

            self.show_login()


if __name__ == "__main__":

    app = ExpenseClaimsApp()

    app.mainloop()