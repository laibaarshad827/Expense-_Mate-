"""
app.py
======
Entry point. Run this file: `python app.py`

Handles switching between screens (Register, OTP, Login, Forgot Password,
Reset Password, Update Password, Update Email). Every screen is a
CTkFrame; only one is shown at a time, stacked in the same window using
.tkraise() — this is the standard multi-frame Tkinter/CTk pattern.
"""

import time

import customtkinter as ctk

import theme
import widgets

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
from screens.savings_screen import SavingsScreen
from screens.reports_screen import ReportsScreen

# "system" makes the app open in whatever light/dark mode the OS is
# currently set to (adaptive maintenance: the UI now adapts to the user's
# actual display environment instead of assuming a fixed light theme).
# The toggle built in ExpenseMateApp._build_theme_toggle() lets the user
# override this manually at any time.
ctk.set_appearance_mode("system")
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

        # Build the (still-empty) container FIRST...
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True)

        # ...THEN create the "Loading..." overlay. In Tkinter a newly
        # created sibling widget is stacked on top of siblings that already
        # exist, so creating the overlay after `container` (rather than
        # before it) is what actually keeps it on top of `container` and
        # everything built inside it below. All 12 screens are constructed
        # one after another and none of that is instant, so without the
        # overlay genuinely on top the user briefly sees each screen
        # mid-construction. It's removed once Login is ready -- nothing
        # about how screens work or navigate changes.
        loading_screen = self._build_loading_screen()
        loading_screen.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.update()  # force the overlay to actually paint right now,
                        # before the synchronous screen-building below runs

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
            SavingsScreen,
            ReportsScreen,
        )

        for ScreenClass in screen_classes:
            frame = ScreenClass(parent=container, controller=self)
            self.frames[ScreenClass.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.show_screen("LoginScreen")

        # CustomTkinter finishes some of its own drawing (rounded corners,
        # images) via a callback queued slightly *after* a widget is
        # created, not instantly. The whole build above just ran as one
        # uninterrupted burst with no turn of the event loop in between, so
        # those finishing-touch callbacks are still backed up for all 12
        # screens' worth of widgets. Pump the event loop a few times, with a
        # tiny real wait each time so those short delays actually become
        # due, so all of that catches up while still hidden behind the
        # overlay -- instead of finishing just after it's removed.
        for _ in range(6):
            self.update()
            time.sleep(0.02)

        # Login is fully built AND fully drawn -> safe to remove the
        # overlay now and reveal it.
        loading_screen.destroy()

        # Floating light/dark toggle. Placed on `self` (the window itself)
        # rather than inside `container`, so it floats above whichever
        # screen is currently shown without needing changes to any of the
        # 12 individual screen files -- every widget's color was already
        # defined in theme.py as a (light, dark) tuple, so CustomTkinter
        # re-renders the whole app automatically when the mode changes.
        self._build_theme_toggle()

    def _build_theme_toggle(self):
        """Small Light/Dark switch shown in the top-right corner on every
        screen. Defaults to whatever set_appearance_mode() resolved to
        at startup (the OS setting, when mode is "system")."""
        current = ctk.get_appearance_mode()  # "Light" or "Dark"

        toggle = ctk.CTkSegmentedButton(
            self, values=["Light", "Dark"],
            command=self._on_theme_toggle,
            width=140, height=30,
        )
        toggle.set(current)
        toggle.place(relx=0.99, rely=0.015, anchor="ne")
        self._theme_toggle = toggle  # kept as an attribute so it isn't garbage-collected

    def _on_theme_toggle(self, selected: str):
        ctk.set_appearance_mode("dark" if selected == "Dark" else "light")

    def _build_loading_screen(self):
        """A minimal full-window overlay shown only while screens are
        being constructed at startup. Purely cosmetic -- it isn't one of
        the app.frames screens and isn't part of navigation."""
        overlay = ctk.CTkFrame(self, fg_color=theme.COLOR_BG_APP, corner_radius=0)

        wrapper = ctk.CTkFrame(overlay, fg_color="transparent")
        wrapper.place(relx=0.5, rely=0.5, anchor="center")

        try:
            logo_image = widgets.get_logo_image(size=72)
            ctk.CTkLabel(wrapper, image=logo_image, text="").pack(pady=(0, 14))
        except Exception:
            pass  # the logo is a nice-to-have; never block startup on it

        ctk.CTkLabel(
            wrapper, text="Loading ExpenseMate...",
            font=theme.FONT_SECTION_TITLE, text_color=theme.COLOR_TEXT_DARK,
        ).pack()

        return overlay

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