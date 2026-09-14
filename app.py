"""
app.py
======
Entry point. Run this file: `python app.py`

Handles switching between screens (Register, OTP, Login, Forgot Password,
Reset Password, Update Password, Update Email). Every screen is a
CTkFrame; only one is shown at a time, stacked in the same window using
.tkraise() — this is the standard multi-frame Tkinter/CTk pattern.
"""

import customtkinter as ctk

from screens.login_screen import LoginScreen
from screens.register_screen import RegisterScreen
from screens.otp_screen import OTPScreen
from screens.forgot_password_screen import ForgotPasswordScreen
from screens.reset_password_screen import ResetPasswordScreen
from screens.update_password_screen import UpdatePasswordScreen
from screens.update_email_screen import UpdateEmailScreen
from screens.dashboard_screen import DashboardScreen
from screens.transactions_screen import TransactionsScreen
from screens.budgets_screen import BudgetsScreen

import theme

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")


class ExpenseMateApp(ctk.CTk):
    """Main application window. Acts as the navigation controller."""

    def __init__(self):
        super().__init__()
        self.title("ExpenseMate - Personal Expense Manager")
        self.minsize(*theme.WINDOW_MIN_SIZE)
        self.resizable(True, True)
        self._open_maximized()

        # Holds data that needs to travel between screens
        # e.g. which email is being verified/reset right now, or the
        # logged-in user's info once auth is done.
        self.session = {
            "pending_email": None,   # email currently going through OTP flow
            "otp_purpose": None,     # "register" | "forgot_password" | "update_email"
            "current_user": None,    # set after successful login
        }

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True)

        self.frames = {}
        screen_classes = (
            LoginScreen,
            RegisterScreen,
            OTPScreen,
            ForgotPasswordScreen,
            ResetPasswordScreen,
            UpdatePasswordScreen,
            UpdateEmailScreen,
            DashboardScreen,
            TransactionsScreen,
            BudgetsScreen,
        )

        for ScreenClass in screen_classes:
            frame = ScreenClass(parent=container, controller=self)
            self.frames[ScreenClass.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.show_screen("LoginScreen")

    def _open_maximized(self):
        """Open the window filling the screen. 'zoomed' works on Windows;
        Linux window managers use the '-zoomed' attribute instead; if
        neither is supported we fall back to a large centered window so
        the app still opens full rather than as a small box.
        """
        try:
            self.state("zoomed")
        except Exception:
            try:
                self.attributes("-zoomed", True)
            except Exception:
                w, h = theme.WINDOW_MIN_SIZE
                self.geometry(f"{w}x{h}")

    def show_screen(self, screen_name: str):
        """Raise the requested screen to the top of the stack.

        Also calls an optional `on_show()` hook on the screen so it can
        refresh itself (e.g. clear input fields, pre-fill an email) every
        time it becomes visible.
        """
        frame = self.frames[screen_name]
        if hasattr(frame, "on_show"):
            frame.on_show()
        frame.tkraise()


if __name__ == "__main__":
    app = ExpenseMateApp()
    app.mainloop()
