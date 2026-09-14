"""
update_email_screen.py
=======================
For a logged-in user changing their email. For security, the OTP is sent
to their CURRENT (old) email to confirm they still own that inbox, then
otp_screen.py finishes the actual change (see purpose="update_email"
handling there).
"""

import customtkinter as ctk
import backend_interface as backend
import theme
import widgets


class UpdateEmailScreen(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=theme.COLOR_PRIMARY_LIGHT)
        self.controller = controller

        card = ctk.CTkFrame(self, fg_color=theme.COLOR_CARD_BG, corner_radius=16)
        card.place(relx=0.5, rely=0.5, anchor="center")

        wrapper = ctk.CTkFrame(card, fg_color="transparent")
        wrapper.pack(padx=60, pady=50)

        widgets.make_mini_header(wrapper).pack(pady=(0, 24))
        widgets.make_title(wrapper, "Update Email").pack(pady=(0, 4))
        self.current_email_label = widgets.make_subtitle(wrapper, "")
        self.current_email_label.pack(pady=(0, 20))

        new_email_field, self.new_email_entry = widgets.make_field(
            wrapper, "New Email Address", "Enter your new email"
        )
        new_email_field.pack(pady=8, fill="x")

        self.error_label = widgets.make_error_label(wrapper)
        self.error_label.pack(pady=(6, 0))

        widgets.make_primary_button(
            wrapper, "Send Verification Code", self.handle_send
        ).pack(pady=(16, 6))

        widgets.make_link_button(
            wrapper, "Back to Dashboard", lambda: controller.show_screen("DashboardScreen")
        ).pack()

    def handle_send(self):
        self.error_label.configure(text="")
        old_email = self.controller.session["current_user"]["email"]
        new_email = self.new_email_entry.get().strip()

        if not backend.is_valid_email(new_email):
            self.error_label.configure(text="Please enter a valid email address.")
            return

        # OTP is sent to the OLD email address (security check).
        success, message, _ = backend.send_otp(old_email)
        if not success:
            self.error_label.configure(text=message)
            return

        self.controller.session["pending_email"] = old_email
        self.controller.session["pending_new_email"] = new_email
        self.controller.session["otp_purpose"] = "update_email"
        self.controller.show_screen("OTPScreen")

    def on_show(self):
        self.new_email_entry.delete(0, "end")
        self.error_label.configure(text="")
        current_email = self.controller.session["current_user"]["email"]
        self.current_email_label.configure(text=f"Current email: {current_email}")
