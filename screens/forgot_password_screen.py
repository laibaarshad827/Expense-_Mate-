"""
forgot_password_screen.py
==========================
First step of the "forgot password" flow: user enters their email,
we send them an OTP, then move to the shared OTPScreen.
"""

import customtkinter as ctk
import backend_interface as backend
import theme
import widgets


class ForgotPasswordScreen(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=theme.COLOR_PRIMARY_LIGHT)
        self.controller = controller

        card = ctk.CTkFrame(self, fg_color=theme.COLOR_CARD_BG, corner_radius=16)
        card.place(relx=0.5, rely=0.5, anchor="center")

        wrapper = ctk.CTkFrame(card, fg_color="transparent")
        wrapper.pack(padx=60, pady=50)

        widgets.make_mini_header(wrapper).pack(pady=(0, 24))

        widgets.make_title(wrapper, "Forgot Password").pack(pady=(0, 4))
        widgets.make_subtitle(
            wrapper, "Enter your email to receive a reset code"
        ).pack(pady=(0, 20))

        email_field, self.email_entry = widgets.make_field(
            wrapper, "Email Address", "Enter your registered email"
        )
        email_field.pack(pady=8, fill="x")

        self.error_label = widgets.make_error_label(wrapper)
        self.error_label.pack(pady=(6, 0))

        widgets.make_primary_button(wrapper, "Send Reset Code", self.handle_send).pack(
            pady=(18, 6)
        )

        widgets.make_link_button(wrapper, "Back to login", self.go_to_login).pack()

    def go_to_login(self):
        self.controller.show_screen("LoginScreen")

    def handle_send(self):
        self.error_label.configure(text="")
        email = self.email_entry.get().strip()

        success, message, _ = backend.request_password_reset(email)
        if not success:
            self.error_label.configure(text=message)
            return

        self.controller.session["pending_email"] = email
        self.controller.session["otp_purpose"] = "forgot_password"
        self.controller.show_screen("OTPScreen")

    def on_show(self):
        self.email_entry.delete(0, "end")
        self.error_label.configure(text="")
