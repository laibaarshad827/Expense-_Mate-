"""
login_screen.py
================
FR-2: The system shall allow a registered user to log in and log out securely.
"""

import customtkinter as ctk
import backend_interface as backend
import theme
import widgets


class LoginScreen(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=theme.COLOR_BG)
        self.controller = controller

        # Split layout: green brand panel (left) + form (right). Both
        # columns stretch with the window since it opens maximized.
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        brand_panel = widgets.make_brand_panel(self, tagline="Track. Budget. Save.")
        brand_panel.grid(row=0, column=0, sticky="nsew")

        form_panel = ctk.CTkFrame(self, fg_color=theme.COLOR_CARD_BG, corner_radius=0)
        form_panel.grid(row=0, column=1, sticky="nsew")

        form = ctk.CTkFrame(form_panel, fg_color="transparent")
        form.place(relx=0.5, rely=0.5, anchor="center")

        widgets.make_title(form, "Welcome Back").pack(pady=(0, 4))
        widgets.make_subtitle(form, "Log in to continue managing your expenses").pack(
            pady=(0, 28)
        )

        email_field, self.email_entry = widgets.make_field(
            form, "Email Address", "Enter your email"
        )
        email_field.pack(pady=8, fill="x")

        password_field, self.password_entry = widgets.make_field(
            form, "Password", "Enter your password", show="*"
        )
        password_field.pack(pady=8, fill="x")

        self.error_label = widgets.make_error_label(form)
        self.error_label.pack(pady=(6, 0))

        widgets.make_primary_button(form, "Log In", self.handle_login).pack(pady=(20, 6))

        widgets.make_link_button(
            form, "Forgot password?", lambda: controller.show_screen("ForgotPasswordScreen")
        ).pack()

        widgets.make_link_button(
            form, "Don't have an account? Register", self.go_to_register
        ).pack(pady=(4, 0))

    def go_to_register(self):
        self.controller.show_screen("RegisterScreen")

    def handle_login(self):
        self.error_label.configure(text="")
        email = self.email_entry.get().strip()
        password = self.password_entry.get()

        success, message, data = backend.login_user(email, password)
        if not success:
            self.error_label.configure(text=message)
            return

        self.controller.session["current_user"] = data
        self.controller.show_screen("DashboardScreen")

    def on_show(self):
        """Called every time this screen becomes visible."""
        self.email_entry.delete(0, "end")
        self.password_entry.delete(0, "end")
        self.error_label.configure(text="")
