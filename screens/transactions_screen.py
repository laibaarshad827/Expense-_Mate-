"""
transactions_screen.py
=======================
Day 2 of the roadmap:
    Build: Dashboard shell, Transaction screen, Add income, Add expense,
    Transaction list, Edit/delete, Category selection.

Covers:
    FR-3  - add a new income/expense entry with amount, date, category, note
    FR-4  - edit or delete an existing entry
    FR-5  - categorize each transaction
    FR-6  - create custom categories
    FR-13 - filter transactions by type / category
"""

from datetime import date
import tkinter.messagebox as messagebox

import customtkinter as ctk
import backend_interface as backend
import theme
import widgets


class TransactionModal(ctk.CTkToplevel):
    """Popup form used for BOTH 'Add' and 'Edit'. If `existing` is given,
    the form is pre-filled and Save calls update_transaction instead of
    add_transaction.
    """

    def __init__(self, parent_screen, txn_type, existing=None):
        super().__init__(parent_screen)
        self.parent_screen = parent_screen
        self.txn_type = txn_type          # "income" | "expense"
        self.existing = existing          # transaction dict or None

        is_income = txn_type == "income"
        accent = theme.COLOR_INCOME if is_income else theme.COLOR_EXPENSE

        self.title(("Edit " if existing else "Add ") + txn_type.capitalize())
        self.geometry("420x520")
        self.resizable(False, False)
        self.configure(fg_color=theme.COLOR_CARD_BG)
        self.grab_set()  # modal behavior

        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=28, pady=24)

        ctk.CTkLabel(
            wrapper,
            text=("Edit " if existing else "Add ") + ("Income" if is_income else "Expense"),
            font=theme.FONT_SECTION_TITLE, text_color=accent,
        ).pack(anchor="w", pady=(0, 16))

        # Amount
        widgets.make_field_label(wrapper, "Amount (Rs.)").pack(fill="x", pady=(0, 4))
        self.amount_entry = widgets.make_entry(wrapper, "e.g. 1500")
        self.amount_entry.configure(width=360)
        self.amount_entry.pack(pady=(0, 12))

        # Category (+ add new)
        cat_label_row = ctk.CTkFrame(wrapper, fg_color="transparent")
        cat_label_row.pack(fill="x")
        widgets.make_field_label(cat_label_row, "Category").pack(side="left")
        ctk.CTkButton(
            cat_label_row, text="+ New category", width=100, height=22, font=theme.FONT_SMALL,
            fg_color="transparent", hover_color=theme.COLOR_PRIMARY_LIGHT, text_color=theme.COLOR_PRIMARY,
            command=self.add_new_category,
        ).pack(side="right")

        categories = backend.get_categories(txn_type)
        self.category_menu, self.category_var = widgets.make_dropdown(wrapper, categories, width=360)
        self.category_menu.pack(pady=(4, 12))

        # Date
        widgets.make_field_label(wrapper, "Date (YYYY-MM-DD)").pack(fill="x", pady=(0, 4))
        self.date_entry = widgets.make_entry(wrapper, "YYYY-MM-DD")
        self.date_entry.configure(width=360)
        self.date_entry.pack(pady=(0, 12))

        # Note
        widgets.make_field_label(wrapper, "Note (optional)").pack(fill="x", pady=(0, 4))
        self.note_entry = widgets.make_entry(wrapper, "e.g. Grocery run")
        self.note_entry.configure(width=360)
        self.note_entry.pack(pady=(0, 8))

        self.error_label = widgets.make_error_label(wrapper)
        self.error_label.pack(pady=(4, 0))

        # Prefill if editing
        if existing:
            self.amount_entry.insert(0, str(existing["amount"]))
            self.category_var.set(existing["category"])
            self.date_entry.insert(0, existing["date"])
            self.note_entry.insert(0, existing["note"])
        else:
            self.date_entry.insert(0, date.today().isoformat())

        hover = "#166B44" if is_income else "#992E23"
        save_btn = ctk.CTkButton(
            wrapper, text="Save", command=self.save,
            width=360, height=theme.BUTTON_HEIGHT, corner_radius=theme.CORNER_RADIUS,
            font=theme.FONT_BUTTON, fg_color=accent, hover_color=hover,
        )
        save_btn.pack(pady=(14, 0))

    def add_new_category(self):
        dialog = ctk.CTkInputDialog(text="New category name:", title="New Category")
        name = dialog.get_input()
        if not name:
            return
        ok, message, data = backend.add_category(name, self.txn_type)
        if not ok:
            messagebox.showerror("Category", message)
            return
        updated = backend.get_categories(self.txn_type)
        self.category_menu.configure(values=updated)
        self.category_var.set(data["name"])

    def save(self):
        self.error_label.configure(text="")
        amount = self.amount_entry.get().strip()
        category = self.category_var.get()
        txn_date = self.date_entry.get().strip()
        note = self.note_entry.get().strip()

        email = self.parent_screen.controller.session.get("current_user", {}).get("email")

        if self.existing:
            ok, message, _ = backend.update_transaction(
                email, self.existing["id"], amount, category, txn_date, note
            )
        else:
            ok, message, _ = backend.add_transaction(
                email, self.txn_type, amount, category, txn_date, note
            )

        if not ok:
            self.error_label.configure(text=message)
            return

        self.parent_screen.refresh_transactions()
        self.destroy()


class TransactionsScreen(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=theme.COLOR_BG_APP)
        self.controller = controller

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        shell, content = widgets.make_app_page(self, controller, "TransactionsScreen")
        shell.grid(row=0, column=0, sticky="nsew")
        self.content = content

        # Header + add buttons
        header_row = ctk.CTkFrame(content, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, 20))

        widgets.make_page_header(header_row, "Transactions", "Track every income and expense in one place.").pack(
            side="left"
        )

        actions = ctk.CTkFrame(header_row, fg_color="transparent")
        actions.pack(side="right")

        ctk.CTkButton(
            actions, text="+ Add Income", command=lambda: self.open_modal("income"),
            fg_color=theme.COLOR_INCOME, hover_color="#166B44", font=theme.FONT_BUTTON,
            height=40, corner_radius=theme.CORNER_RADIUS,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            actions, text="+ Add Expense", command=lambda: self.open_modal("expense"),
            fg_color=theme.COLOR_EXPENSE, hover_color="#992E23", font=theme.FONT_BUTTON,
            height=40, corner_radius=theme.CORNER_RADIUS,
        ).pack(side="left")

        # Filters
        filter_row = ctk.CTkFrame(content, fg_color="transparent")
        filter_row.pack(fill="x", pady=(0, 16))

        widgets.make_field_label(filter_row, "Type").pack(side="left", padx=(0, 8))
        self.type_menu, self.type_var = widgets.make_dropdown(
            filter_row, ["All", "income", "expense"], command=lambda _=None: self.on_type_filter_change(), width=140
        )
        self.type_menu.pack(side="left", padx=(0, 20))

        widgets.make_field_label(filter_row, "Category").pack(side="left", padx=(0, 8))
        self.category_menu, self.category_var = widgets.make_dropdown(
            filter_row, ["All"], command=lambda _=None: self.refresh_transactions(), width=180
        )
        self.category_menu.pack(side="left")

        # Table card
        self.table_card = ctk.CTkFrame(
            content, fg_color=theme.COLOR_CARD_BG, corner_radius=14,
            border_width=1, border_color=theme.COLOR_BORDER,
        )
        self.table_card.pack(fill="both", expand=True)

        self.table_header = ctk.CTkFrame(self.table_card, fg_color="transparent")
        self.table_header.pack(fill="x", padx=20, pady=(16, 6))
        for text, w in (("Date", 100), ("Category", 160), ("Note", 220), ("Amount", 130), ("", 110)):
            ctk.CTkLabel(
                self.table_header, text=text, font=theme.FONT_TABLE_HEADER, text_color=theme.COLOR_TEXT_MUTED,
                width=w, anchor="w",
            ).pack(side="left")

        self.rows_container = ctk.CTkFrame(self.table_card, fg_color="transparent")
        self.rows_container.pack(fill="both", expand=True, padx=12, pady=(0, 16))

    # -- helpers -------------------------------------------------------
    def open_modal(self, txn_type, existing=None):
        TransactionModal(self, txn_type, existing=existing)

    def on_type_filter_change(self):
        txn_type = self.type_var.get()
        if txn_type == "All":
            categories = ["All"] + backend.get_categories("income") + backend.get_categories("expense")
        else:
            categories = ["All"] + backend.get_categories(txn_type)
        self.category_menu.configure(values=categories)
        self.category_var.set("All")
        self.refresh_transactions()

    def _clear_rows(self):
        for widget in self.rows_container.winfo_children():
            widget.pack_forget()
            widget.destroy()

    def refresh_transactions(self):
        email = self.controller.session.get("current_user", {}).get("email")
        txn_type = self.type_var.get()
        category = self.category_var.get()

        rows = backend.get_transactions(email, txn_type=txn_type, category=category) if email else []

        self._clear_rows()
        if not rows:
            ctk.CTkLabel(
                self.rows_container,
                text="No transactions match this filter yet.\nUse the buttons above to add your first one.",
                font=theme.FONT_LABEL, text_color=theme.COLOR_TEXT_MUTED, justify="center",
            ).pack(pady=30)
            return

        for r in rows:
            self._build_row(r)

    def _build_row(self, r):
        is_income = r["type"] == "income"
        color = theme.COLOR_INCOME if is_income else theme.COLOR_EXPENSE

        row = ctk.CTkFrame(self.rows_container, fg_color=theme.COLOR_BG_APP, corner_radius=8)
        row.pack(fill="x", pady=3, padx=4)

        ctk.CTkLabel(row, text=r["date"], font=theme.FONT_TABLE_CELL, width=100, anchor="w",
                     text_color=theme.COLOR_TEXT_DARK).pack(side="left", pady=10, padx=(12, 0))

        cat_col = ctk.CTkFrame(row, width=160, height=32, fg_color="transparent")
        cat_col.pack(side="left", pady=10)
        cat_col.pack_propagate(False)
        widgets.make_pill(
            cat_col, r["category"],
            theme.COLOR_INCOME_LIGHT if is_income else theme.COLOR_EXPENSE_LIGHT, color,
        ).pack(anchor="w")

        note_text = r["note"] if r["note"] else "—"
        ctk.CTkLabel(row, text=note_text, font=theme.FONT_TABLE_CELL, width=220, anchor="w",
                     text_color=theme.COLOR_TEXT_MUTED).pack(side="left", pady=10)

        sign = "+" if is_income else "-"
        ctk.CTkLabel(
            row, text=f"{sign} Rs. {r['amount']:,.2f}", font=theme.FONT_FIELD_LABEL, width=130,
            anchor="w", text_color=color,
        ).pack(side="left", pady=10)

        action_col = ctk.CTkFrame(row, width=110, fg_color="transparent")
        action_col.pack(side="left", pady=10, padx=(0, 12))
        widgets.make_icon_button(
            action_col, "✎", lambda: self.open_modal(r["type"], existing=r),
            theme.COLOR_PRIMARY, theme.COLOR_PRIMARY_HOVER,
        ).pack(side="left", padx=(0, 6))
        widgets.make_icon_button(
            action_col, "🗑", lambda: self.confirm_delete(r),
            theme.COLOR_DANGER, theme.COLOR_DANGER_HOVER,
        ).pack(side="left")

    def confirm_delete(self, r):
        if messagebox.askyesno("Delete transaction", "Delete this transaction? This cannot be undone."):
            email = self.controller.session.get("current_user", {}).get("email")
            backend.delete_transaction(email, r["id"])
            self.refresh_transactions()

    def on_show(self):
        self.type_var.set("All")
        self.type_menu.configure(values=["All", "income", "expense"])
        self.category_menu.configure(values=["All"] + backend.get_categories("income") + backend.get_categories("expense"))
        self.category_var.set("All")
        self.refresh_transactions()
