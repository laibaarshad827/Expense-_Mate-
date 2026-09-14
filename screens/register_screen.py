"""
register_screen.py
===================
FR-1: The system shall allow a user to create an account with a
username and password.
"""

import customtkinter as ctk
import backend_interface as backend
import theme
import widgets


class RegisterScreen(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=theme.COLOR_BG)
        self.controller = controller

        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        brand_panel = widgets.make_brand_panel(
            self, tagline="Join thousands taking control\nof their money."
        )
        brand_panel.grid(row=0, column=0, sticky="nsew")

        form_panel = ctk.CTkFrame(self, fg_color=theme.COLOR_CARD_BG, corner_radius=0)
        form_panel.grid(row=0, column=1, sticky="nsew")

        form = ctk.CTkFrame(form_panel, fg_color="transparent")
        form.place(relx=0.5, rely=0.5, anchor="center")

        widgets.make_title(form, "Create Account").pack(pady=(0, 4))
        widgets.make_subtitle(form, "Start tracking your expenses today").pack(pady=(0, 24))

        username_field, self.username_entry = widgets.make_field(
            form, "Username", "Enter your username"
        )
        username_field.pack(pady=6, fill="x")

        email_field, self.email_entry = widgets.make_field(
            form, "Email Address", "Enter your email"
        )
        email_field.pack(pady=6, fill="x")

        password_field, self.password_entry = widgets.make_field(
            form, "Password", "Enter your password (min. 6 characters)", show="*"
        )
        password_field.pack(pady=6, fill="x")

        confirm_field, self.confirm_password_entry = widgets.make_field(
            form, "Confirm Password", "Re-enter your password", show="*"
        )
        confirm_field.pack(pady=6, fill="x")

        self.error_label = widgets.make_error_label(form)
        self.error_label.pack(pady=(6, 0))

        widgets.make_primary_button(form, "Register", self.handle_register).pack(pady=(18, 6))

        widgets.make_link_button(
            form, "Already have an account? Log in", self.go_to_login
        ).pack()

    def go_to_login(self):
        self.controller.show_screen("LoginScreen")

    def handle_register(self):
        self.error_label.configure(text="")
        username = self.username_entry.get()
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        confirm = self.confirm_password_entry.get()

        success, message, data = backend.register_user(username, email, password, confirm)
        if not success:
            self.error_label.configure(text=message)
            return

        # Registration succeeded -> backend already sent an OTP.
        # Move to the OTP screen to verify before allowing login.
        self.controller.session["pending_email"] = email
        self.controller.session["otp_purpose"] = "register"
        self.controller.show_screen("OTPScreen")

    def on_show(self):
        self.username_entry.delete(0, "end")
        self.email_entry.delete(0, "end")
        self.password_entry.delete(0, "end")
        self.confirm_password_entry.delete(0, "end")
        self.error_label.configure(text="")
