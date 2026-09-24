"""
savings_screen.py
==================
Day 4: Savings goals — create, view, contribute to, edit, and delete
savings goals, plus an overall progress summary.
"""

import customtkinter as ctk
import backend_interface as backend
import theme
import widgets


class SavingsScreen(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self._form_visible = False

        shell, self.content = widgets.make_app_page(self, controller, "SavingsScreen")
        shell.pack(fill="both", expand=True)

        header_row = ctk.CTkFrame(self.content, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, 20))
        widgets.make_page_header(
            header_row, "Savings Goals", "Track progress toward what you're saving for"
        ).pack(side="left")
        widgets.make_primary_button(
            header_row, "+ Add Goal", self._toggle_form
        ).pack(side="right")

        self.summary_row = ctk.CTkFrame(self.content, fg_color="transparent")
        self.summary_row.pack(fill="x", pady=(0, 20))

        self.form_frame = ctk.CTkFrame(
            self.content, fg_color=theme.COLOR_CARD_BG, corner_radius=12,
            border_width=1, border_color=theme.COLOR_BORDER,
        )
        self._build_form()

        self.goals_container = ctk.CTkFrame(self.content, fg_color="transparent")
        self.goals_container.pack(fill="both", expand=True)

        self.editing_goal_id = None

    # -----------------------------------------------------------------
    # Form (add / edit)
    # -----------------------------------------------------------------

    def _build_form(self):
        inner = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        inner.pack(fill="x", padx=24, pady=20)

        self.form_title = ctk.CTkLabel(
            inner, text="New Savings Goal", font=theme.FONT_SECTION_TITLE,
            text_color=theme.COLOR_TEXT_DARK, anchor="w",
        )
        self.form_title.pack(anchor="w", pady=(0, 14))

        row1 = ctk.CTkFrame(inner, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 12))
        name_wrap, self.name_entry = widgets.make_field(row1, "Goal Name", "e.g. New Laptop")
        name_wrap.pack(side="left", padx=(0, 16))
        target_wrap, self.target_entry = widgets.make_field(row1, "Target Amount", "e.g. 150000")
        target_wrap.pack(side="left")

        row2 = ctk.CTkFrame(inner, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 14))
        deadline_wrap, self.deadline_entry = widgets.make_field(
            row2, "Deadline (optional)", "YYYY-MM-DD"
        )
        deadline_wrap.pack(side="left")

        self.form_error = widgets.make_error_label(inner)
        self.form_error.pack(anchor="w", pady=(0, 10))

        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(anchor="w")
        widgets.make_primary_button(btn_row, "Save Goal", self._save_goal).pack(side="left", padx=(0, 10))
        widgets.make_link_button(btn_row, "Cancel", self._toggle_form).pack(side="left")

    def _toggle_form(self):
        self._form_visible = not self._form_visible
        if self._form_visible:
            self.editing_goal_id = None
            self.form_title.configure(text="New Savings Goal")
            self.name_entry.delete(0, "end")
            self.target_entry.delete(0, "end")
            self.deadline_entry.delete(0, "end")
            self.form_error.configure(text="")
            self.form_frame.pack(fill="x", pady=(0, 20), before=self.goals_container)
        else:
            self.form_frame.pack_forget()

    def _save_goal(self):
        email = self._current_email()
        name = self.name_entry.get()
        target = self.target_entry.get()
        deadline = self.deadline_entry.get().strip() or None

        if self.editing_goal_id:
            success, message, _ = backend.update_savings_goal(email, self.editing_goal_id, name, target, deadline)
        else:
            success, message, _ = backend.create_savings_goal(email, name, target, deadline)

        if not success:
            self.form_error.configure(text=message)
            return

        self._toggle_form()
        self._refresh()

    def _edit_goal(self, goal):
        self._form_visible = False  # force it open fresh below
        self.editing_goal_id = goal["goal_id"]
        self.form_title.configure(text="Edit Savings Goal")
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, goal["goal_name"])
        self.target_entry.delete(0, "end")
        self.target_entry.insert(0, str(goal["target_amount"]))
        self.deadline_entry.delete(0, "end")
        if goal["deadline"]:
            self.deadline_entry.insert(0, goal["deadline"])
        self.form_error.configure(text="")
        self._toggle_form()

    def _delete_goal(self, goal):
        email = self._current_email()
        backend.delete_savings_goal(email, goal["goal_id"])
        self._refresh()

    def _contribute(self, goal):
        # Simple inline dialog for the contribution amount.
        dialog = ctk.CTkInputDialog(
            text=f"How much are you adding to '{goal['goal_name']}'?",
            title="Add Contribution",
        )
        amount = dialog.get_input()
        if amount:
            email = self._current_email()
            backend.add_savings_contribution(email, goal["goal_id"], amount)
            self._refresh()

    # -----------------------------------------------------------------
    # Data / rendering
    # -----------------------------------------------------------------

    def _current_email(self):
        user = self.controller.session.get("current_user")
        return user["email"] if user else None

    def on_show(self):
        self._refresh()

    def _refresh(self):
        for widget in self.summary_row.winfo_children():
            widget.destroy()
        for widget in self.goals_container.winfo_children():
            widget.destroy()

        email = self._current_email()
        if not email:
            return

        summary = backend.get_savings_summary(email)
        widgets.make_stat_card(
            self.summary_row, "🎯", "Total Saved", f"Rs. {summary['total_saved']:,.2f}", theme.COLOR_INCOME
        ).pack(side="left", fill="x", expand=True, padx=(0, 12))
        widgets.make_stat_card(
            self.summary_row, "🏁", "Total Target", f"Rs. {summary['total_target']:,.2f}", theme.COLOR_TEXT_DARK
        ).pack(side="left", fill="x", expand=True, padx=(0, 12))
        widgets.make_stat_card(
            self.summary_row, "📈", "Overall Progress", f"{summary['overall_percent']}%", theme.COLOR_ACCENT
        ).pack(side="left", fill="x", expand=True)

        goals = backend.get_savings_goals(email)
        if not goals:
            ctk.CTkLabel(
                self.goals_container, text="No savings goals yet — click \"+ Add Goal\" to create one.",
                font=theme.FONT_LABEL, text_color=theme.COLOR_TEXT_MUTED,
            ).pack(pady=30)
            return

        for goal in goals:
            widgets.make_goal_card(
                self.goals_container, goal, self._contribute, self._edit_goal, self._delete_goal
            )