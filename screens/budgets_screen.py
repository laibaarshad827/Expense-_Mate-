"""
budgets_screen.py
==================
Day 3 of the roadmap - Budgets:
    FR-7  - manually set a monthly budget limit per expense category
    FR-8  - suggest a monthly budget from the last 3 months' average
    FR-9  - alert when spending in a category exceeds its budget
    FR-10 - show remaining budget per category in real time

Most of the visual work lives in widgets.make_alert_banner/make_budget_row
so this file just wires backend data to those helpers.
"""

import customtkinter as ctk
import backend_interface as backend
import theme
import widgets


class BudgetModal(ctk.CTkToplevel):
    """FR-7/FR-8: set (or edit) a category's monthly limit, with a
    one-click 'Use suggested' shortcut when history is available."""

    def __init__(self, parent_screen, category):
        super().__init__(parent_screen)
        self.parent_screen = parent_screen
        self.category = category

        self.title(f"Set Budget - {category}")
        self.geometry("380x300")
        self.resizable(False, False)
        self.configure(fg_color=theme.COLOR_CARD_BG)
        self.grab_set()

        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=26, pady=22)

        ctk.CTkLabel(wrapper, text=f"Monthly budget for {category}", font=theme.FONT_SECTION_TITLE,
                     text_color=theme.COLOR_TEXT_DARK, wraplength=320).pack(anchor="w", pady=(0, 14))

        widgets.make_field_label(wrapper, "Amount (Rs. / month)").pack(fill="x", pady=(0, 4))
        self.amount_entry = widgets.make_entry(wrapper, "e.g. 8000")
        self.amount_entry.configure(width=320)
        self.amount_entry.pack()

        email = parent_screen.controller.session.get("current_user", {}).get("email")
        current = backend.get_budget(email, category)
        suggested = backend.suggest_budget(email, category)
        if current:
            self.amount_entry.insert(0, str(current))
        if suggested and suggested != current:
            ctk.CTkButton(
                wrapper, text=f"Use suggested: Rs. {suggested:,.2f}", height=28, font=theme.FONT_SMALL,
                fg_color="transparent", hover_color=theme.COLOR_PRIMARY_LIGHT, text_color=theme.COLOR_PRIMARY,
                command=lambda: (self.amount_entry.delete(0, "end"), self.amount_entry.insert(0, str(suggested))),
            ).pack(pady=(8, 0))

        self.error_label = widgets.make_error_label(wrapper)
        self.error_label.pack(pady=(8, 0))

        ctk.CTkButton(
            wrapper, text="Save Budget", command=self.save, width=320, height=theme.BUTTON_HEIGHT,
            corner_radius=theme.CORNER_RADIUS, font=theme.FONT_BUTTON, fg_color=theme.COLOR_PRIMARY,
            hover_color=theme.COLOR_PRIMARY_HOVER,
        ).pack(pady=(14, 0))

    def save(self):
        email = self.parent_screen.controller.session.get("current_user", {}).get("email")
        ok, message, _ = backend.set_budget(email, self.category, self.amount_entry.get().strip())
        if not ok:
            self.error_label.configure(text=message)
            return
        self.parent_screen.refresh()
        self.destroy()


class BudgetsScreen(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=theme.COLOR_BG_APP)
        self.controller = controller
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        shell, content = widgets.make_app_page(self, controller, "BudgetsScreen")
        shell.grid(row=0, column=0, sticky="nsew")
        self.content = content

        widgets.make_page_header(
            content, "Budgets", "Set monthly limits per category and track spending in real time."
        ).pack(fill="x", pady=(0, 18))

        self.body = ctk.CTkFrame(content, fg_color="transparent")
        self.body.pack(fill="both", expand=True)

    def open_modal(self, category):
        BudgetModal(self, category)

    def refresh(self):
        for w in self.body.winfo_children():
            w.destroy()

        email = self.controller.session.get("current_user", {}).get("email")
        if not email:
            return
        statuses = backend.get_budget_status(email)

        banner = widgets.make_alert_banner(self.body, backend.get_budget_alerts(email))
        if banner:
            banner.pack(fill="x", pady=(0, 14))

        for status in statuses:
            widgets.make_budget_row(self.body, status, self.open_modal)

    def on_show(self):
        self.refresh()
