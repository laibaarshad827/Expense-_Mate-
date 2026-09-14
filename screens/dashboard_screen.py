"""
dashboard_screen.py
====================
Day 2 (dashboard shell) + FR-12: the real landing page after login.

Shows the app shell (sidebar navigation) plus:
  - Welcome header
  - Stat cards: Total Income, Total Expense, Net Savings, Transactions
  - A "Recent Transactions" preview (last 5) with a shortcut into the
    full Transactions screen.

The financial numbers/charts side of this (Day 4 on the roadmap) will
build on top of get_dashboard_summary(); for now the shell + live
totals from the Day 2 transaction data are wired up.
"""

import customtkinter as ctk
import backend_interface as backend
import theme
import widgets


class DashboardScreen(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=theme.COLOR_BG_APP)
        self.controller = controller

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        shell, content = widgets.make_app_page(self, controller, "DashboardScreen")
        shell.grid(row=0, column=0, sticky="nsew")
        self.content = content

        self.header = widgets.make_page_header(content, "Welcome back!", "Here's your financial snapshot.")
        self.header.pack(fill="x", pady=(0, 24))

        # Stat cards row
        stats_row = ctk.CTkFrame(content, fg_color="transparent")
        stats_row.pack(fill="x", pady=(0, 30))
        for i in range(4):
            stats_row.grid_columnconfigure(i, weight=1, uniform="stats")

        self.card_income = widgets.make_stat_card(stats_row, "💰", "Total Income", "Rs. 0.00", theme.COLOR_INCOME)
        self.card_income.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        self.card_expense = widgets.make_stat_card(stats_row, "💸", "Total Expense", "Rs. 0.00", theme.COLOR_EXPENSE)
        self.card_expense.grid(row=0, column=1, sticky="nsew", padx=6)

        self.card_savings = widgets.make_stat_card(stats_row, "🏦", "Net Savings", "Rs. 0.00", theme.COLOR_PRIMARY)
        self.card_savings.grid(row=0, column=2, sticky="nsew", padx=6)

        self.card_count = widgets.make_stat_card(stats_row, "🧾", "Transactions", "0", theme.COLOR_ACCENT)
        self.card_count.grid(row=0, column=3, sticky="nsew", padx=(12, 0))

        # Recent transactions card
        recent_card = ctk.CTkFrame(
            content, fg_color=theme.COLOR_CARD_BG, corner_radius=14,
            border_width=1, border_color=theme.COLOR_BORDER,
        )
        recent_card.pack(fill="both", expand=True)

        recent_header = ctk.CTkFrame(recent_card, fg_color="transparent")
        recent_header.pack(fill="x", padx=24, pady=(20, 6))
        ctk.CTkLabel(
            recent_header, text="Recent Transactions", font=theme.FONT_SECTION_TITLE,
            text_color=theme.COLOR_TEXT_DARK,
        ).pack(side="left")
        ctk.CTkButton(
            recent_header, text="View All →", fg_color="transparent", hover_color=theme.COLOR_PRIMARY_LIGHT,
            text_color=theme.COLOR_PRIMARY, font=theme.FONT_LABEL, width=90, height=28,
            command=lambda: controller.show_screen("TransactionsScreen"),
        ).pack(side="right")

        self.recent_list = ctk.CTkFrame(recent_card, fg_color="transparent")
        self.recent_list.pack(fill="both", expand=True, padx=24, pady=(4, 20))

    def _clear_recent_list(self):
        for widget in self.recent_list.winfo_children():
            widget.pack_forget()
            widget.destroy()

    def _refresh(self):
        user = self.controller.session.get("current_user") or {}
        username = user.get("username", "there")
        email = user.get("email")

        title_label = self.header.winfo_children()[0]
        title_label.configure(text=f"Welcome back, {username}!")

        summary = backend.get_dashboard_summary(email) if email else {
            "total_income": 0, "total_expense": 0, "net_savings": 0, "transaction_count": 0
        }

        self.card_income.value_label.configure(text=f"Rs. {summary['total_income']:,.2f}")
        self.card_expense.value_label.configure(text=f"Rs. {summary['total_expense']:,.2f}")
        savings_color = theme.COLOR_INCOME if summary["net_savings"] >= 0 else theme.COLOR_EXPENSE
        self.card_savings.value_label.configure(
            text=f"Rs. {summary['net_savings']:,.2f}", text_color=savings_color
        )
        self.card_count.value_label.configure(text=str(summary["transaction_count"]))

        self._clear_recent_list()
        rows = backend.get_transactions(email)[:5] if email else []
        if not rows:
            ctk.CTkLabel(
                self.recent_list,
                text="No transactions yet. Add your first income or expense from the\nTransactions page to see it here.",
                font=theme.FONT_LABEL, text_color=theme.COLOR_TEXT_MUTED, justify="center",
            ).pack(pady=20)
            return

        for r in rows:
            row = ctk.CTkFrame(self.recent_list, fg_color=theme.COLOR_BG_APP, corner_radius=10)
            row.pack(fill="x", pady=4)

            is_income = r["type"] == "income"
            color = theme.COLOR_INCOME if is_income else theme.COLOR_EXPENSE
            bg = theme.COLOR_INCOME_LIGHT if is_income else theme.COLOR_EXPENSE_LIGHT

            ctk.CTkLabel(
                row, text="▲" if is_income else "▼", text_color=color, fg_color=bg,
                width=32, height=32, corner_radius=16, font=("Segoe UI", 12, "bold"),
            ).pack(side="left", padx=12, pady=10)

            text_col = ctk.CTkFrame(row, fg_color="transparent")
            text_col.pack(side="left", fill="x", expand=True, pady=10)
            ctk.CTkLabel(
                text_col, text=r["category"], font=theme.FONT_LABEL, text_color=theme.COLOR_TEXT_DARK, anchor="w"
            ).pack(anchor="w")
            ctk.CTkLabel(
                text_col, text=f"{r['date']}" + (f" · {r['note']}" if r["note"] else ""),
                font=theme.FONT_SMALL, text_color=theme.COLOR_TEXT_MUTED, anchor="w",
            ).pack(anchor="w")

            sign = "+" if is_income else "-"
            ctk.CTkLabel(
                row, text=f"{sign} Rs. {r['amount']:,.2f}", font=theme.FONT_FIELD_LABEL, text_color=color,
            ).pack(side="right", padx=16)

    def on_show(self):
        self._refresh()
