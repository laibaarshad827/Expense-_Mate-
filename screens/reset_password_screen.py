"""
reset_password_screen.py
=========================
Final step of the "forgot password" flow. Takes the OTP already entered
on OTPScreen (stored in session["otp_code"]) together with a brand new
password, and finishes the reset in one backend call.
"""

import customtkinter as ctk
import backend_interface as backend
import theme
import widgets


class ResetPasswordScreen(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=theme.COLOR_PRIMARY_LIGHT)
        self.controller = controller

        card = ctk.CTkFrame(self, fg_color=theme.COLOR_CARD_BG, corner_radius=16)
        card.place(relx=0.5, rely=0.5, anchor="center")

        wrapper = ctk.CTkFrame(card, fg_color="transparent")
        wrapper.pack(padx=60, pady=50)

        widgets.make_mini_header(wrapper).pack(pady=(0, 24))

        widgets.make_title(wrapper, "Reset Password").pack(pady=(0, 4))
        widgets.make_subtitle(wrapper, "Choose a new password").pack(pady=(0, 20))

        new_pw_field, self.new_password_entry = widgets.make_field(
            wrapper, "New Password", "Enter your new password", show="*"
        )
        new_pw_field.pack(pady=8, fill="x")

        confirm_pw_field, self.confirm_password_entry = widgets.make_field(
            wrapper, "Confirm New Password", "Re-enter your new password", show="*"
        )
        confirm_pw_field.pack(pady=8, fill="x")

        self.error_label = widgets.make_error_label(wrapper)
        self.error_label.pack(pady=(6, 0))

        widgets.make_primary_button(wrapper, "Reset Password", self.handle_reset).pack(
            pady=(18, 6)
        )

    def handle_reset(self):
        self.error_label.configure(text="")
        email = self.controller.session.get("pending_email")
        otp_code = self.controller.session.get("otp_code")
        new_password = self.new_password_entry.get()
        confirm_password = self.confirm_password_entry.get()

        success, message, _ = backend.reset_password(
            email, otp_code, new_password, confirm_password
        )
        if not success:
            self.error_label.configure(text=message)
            return

        # Clean up the temporary session data used for this flow.
        self.controller.session["otp_code"] = None
        self.controller.session["pending_email"] = None
        self.controller.show_screen("LoginScreen")

    def on_show(self):
        self.new_password_entry.delete(0, "end")
        self.confirm_password_entry.delete(0, "end")
        self.error_label.configure(text="")
