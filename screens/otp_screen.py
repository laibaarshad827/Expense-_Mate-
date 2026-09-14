"""
otp_screen.py
=============
One shared OTP screen reused by three different flows:
  - "register"        -> after this, go to LoginScreen
  - "forgot_password"  -> after this, go to ResetPasswordScreen
  - "update_email"     -> after this, finishes the email change right here

Which flow we're in is stored in controller.session["otp_purpose"], set by
whichever screen sent the user here. This avoids duplicating the OTP UI
three times.
"""

import customtkinter as ctk
import backend_interface as backend
import theme
import widgets


class OTPScreen(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=theme.COLOR_PRIMARY_LIGHT)
        self.controller = controller

        card = ctk.CTkFrame(self, fg_color=theme.COLOR_CARD_BG, corner_radius=16)
        card.place(relx=0.5, rely=0.5, anchor="center")

        wrapper = ctk.CTkFrame(card, fg_color="transparent")
        wrapper.pack(padx=60, pady=50)

        widgets.make_mini_header(wrapper).pack(pady=(0, 24))

        widgets.make_title(wrapper, "Verify OTP").pack(pady=(0, 4))
        self.subtitle_label = widgets.make_subtitle(wrapper, "")
        self.subtitle_label.pack(pady=(0, 20))

        otp_field, self.otp_entry = widgets.make_field(
            wrapper, "Verification Code", "Enter the 6-digit OTP"
        )
        otp_field.pack(pady=8, fill="x")

        self.error_label = widgets.make_error_label(wrapper)
        self.error_label.pack(pady=(6, 0))

        widgets.make_primary_button(wrapper, "Verify", self.handle_verify).pack(pady=(18, 6))

        widgets.make_link_button(wrapper, "Resend OTP", self.handle_resend).pack()

    def handle_verify(self):
        self.error_label.configure(text="")
        email = self.controller.session.get("pending_email")
        otp_code = self.otp_entry.get().strip()
        purpose = self.controller.session.get("otp_purpose")

        if not otp_code:
            self.error_label.configure(text="Please enter the OTP.")
            return

        if purpose == "forgot_password":
            # Don't consume the OTP here. ResetPasswordScreen still needs
            # the user to type a NEW password, so it verifies + consumes
            # this same OTP together with that new password in one
            # atomic backend call.
            self.controller.session["otp_code"] = otp_code
            self.controller.show_screen("ResetPasswordScreen")
            return

        if purpose == "update_email":
            # We already collected the new email in UpdateEmailScreen, so
            # we have everything we need -> finish the change right here.
            old_email = self.controller.session["current_user"]["email"]
            new_email = self.controller.session.get("pending_new_email")
            success, message, data = backend.update_email(old_email, new_email, otp_code)
            if not success:
                self.error_label.configure(text=message)
                return
            self.controller.session["current_user"]["email"] = data["email"]
            self.controller.show_screen("DashboardScreen")
            return

        # "register" purpose: verify immediately, nothing further needs the code.
        success, message, _ = backend.verify_otp(email, otp_code)
        if not success:
            self.error_label.configure(text=message)
            return
        self.controller.show_screen("LoginScreen")

    def handle_resend(self):
        self.error_label.configure(text="")
        email = self.controller.session.get("pending_email")
        success, message, _ = backend.send_otp(email)
        self.error_label.configure(text=message)

    def on_show(self):
        self.otp_entry.delete(0, "end")
        self.error_label.configure(text="")
        email = self.controller.session.get("pending_email", "")
        self.subtitle_label.configure(text=f"We sent a code to {email}")
