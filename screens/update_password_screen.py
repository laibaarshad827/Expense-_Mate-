"""
update_password_screen.py
==========================
For an already logged-in user who wants to change their password from
their account settings (different from the "forgot password" flow,
which is for a user who is locked out).
"""

import customtkinter as ctk
import backend_interface as backend
import theme
import widgets


class UpdatePasswordScreen(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=theme.COLOR_PRIMARY_LIGHT)
        self.controller = controller

        card = ctk.CTkFrame(self, fg_color=theme.COLOR_CARD_BG, corner_radius=16)
        card.place(relx=0.5, rely=0.5, anchor="center")

        wrapper = ctk.CTkFrame(card, fg_color="transparent")
        wrapper.pack(padx=60, pady=50)

        widgets.make_mini_header(wrapper).pack(pady=(0, 24))
        widgets.make_title(wrapper, "Update Password").pack(pady=(0, 20))

        old_pw_field, self.old_password_entry = widgets.make_field(
            wrapper, "Current Password", "Enter your current password", show="*"
        )
        old_pw_field.pack(pady=8, fill="x")

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

        self.success_label = widgets.make_success_label(wrapper)
        self.success_label.pack()

        widgets.make_primary_button(wrapper, "Update Password", self.handle_update).pack(
            pady=(16, 6)
        )

        widgets.make_link_button(
            wrapper, "Back to Dashboard", lambda: controller.show_screen("DashboardScreen")
        ).pack()

    def handle_update(self):
        self.error_label.configure(text="")
        self.success_label.configure(text="")

        email = self.controller.session["current_user"]["email"]
        old_password = self.old_password_entry.get()
        new_password = self.new_password_entry.get()
        confirm_password = self.confirm_password_entry.get()

        success, message, _ = backend.update_password(
            email, old_password, new_password, confirm_password
        )
        if not success:
            self.error_label.configure(text=message)
            return

        self.success_label.configure(text=message)
        self.old_password_entry.delete(0, "end")
        self.new_password_entry.delete(0, "end")
        self.confirm_password_entry.delete(0, "end")

    def on_show(self):
        self.old_password_entry.delete(0, "end")
        self.new_password_entry.delete(0, "end")
        self.confirm_password_entry.delete(0, "end")
        self.error_label.configure(text="")
        self.success_label.configure(text="")
