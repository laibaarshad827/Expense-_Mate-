"""
reports_screen.py
==================
Day 5: Reports — filterable transaction table, category breakdown chart,
and CSV import/export.
"""

import customtkinter as ctk
from tkinter import filedialog
import backend_interface as backend
import theme
import widgets


class ReportsScreen(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        shell, self.content = widgets.make_app_page(self, controller, "ReportsScreen")
        shell.pack(fill="both", expand=True)

        header_row = ctk.CTkFrame(self.content, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, 20))
        widgets.make_page_header(
            header_row, "Reports", "Filter, review, and export your transaction history"
        ).pack(side="left")

        csv_btn_row = ctk.CTkFrame(header_row, fg_color="transparent")
        csv_btn_row.pack(side="right")
        widgets.make_primary_button(csv_btn_row, "Export CSV", self._export_csv).pack(side="left", padx=(0, 10))
        widgets.make_primary_button(csv_btn_row, "Import CSV", self._import_csv).pack(side="left")

        self.import_result_label = widgets.make_success_label(self.content)
        self.import_result_label.pack(anchor="w", pady=(0, 10))

        self._build_filters()

        self.breakdown_frame = ctk.CTkFrame(
            self.content, fg_color=theme.COLOR_CARD_BG, corner_radius=12,
            border_width=1, border_color=theme.COLOR_BORDER,
        )
        self.breakdown_frame.pack(fill="x", pady=(0, 20))

        self.table_frame = ctk.CTkFrame(
            self.content, fg_color=theme.COLOR_CARD_BG, corner_radius=12,
            border_width=1, border_color=theme.COLOR_BORDER,
        )
        self.table_frame.pack(fill="both", expand=True)

    # -----------------------------------------------------------------
    # Filters
    # -----------------------------------------------------------------

    def _build_filters(self):
        bar = ctk.CTkFrame(self.content, fg_color=theme.COLOR_CARD_BG, corner_radius=12,
                            border_width=1, border_color=theme.COLOR_BORDER)
        bar.pack(fill="x", pady=(0, 20))
        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=14)

        start_wrap, self.start_entry = widgets.make_field(inner, "From", "YYYY-MM-DD")
        start_wrap.pack(side="left", padx=(0, 14))
        end_wrap, self.end_entry = widgets.make_field(inner, "To", "YYYY-MM-DD")
        end_wrap.pack(side="left", padx=(0, 14))

        type_col = ctk.CTkFrame(inner, fg_color="transparent")
        type_col.pack(side="left", padx=(0, 14))
        widgets.make_field_label(type_col, "Type").pack(anchor="w", pady=(0, 4))
        self.type_menu, self.type_var = widgets.make_dropdown(
            type_col, ["All", "income", "expense"], width=140
        )
        self.type_menu.pack()

        cat_col = ctk.CTkFrame(inner, fg_color="transparent")
        cat_col.pack(side="left", padx=(0, 14))
        widgets.make_field_label(cat_col, "Category").pack(anchor="w", pady=(0, 4))
        self.cat_menu, self.cat_var = widgets.make_dropdown(cat_col, ["All"], width=160)
        self.cat_menu.pack()

        apply_col = ctk.CTkFrame(inner, fg_color="transparent")
        apply_col.pack(side="left", padx=(14, 0))
        ctk.CTkLabel(apply_col, text="", font=theme.FONT_SMALL).pack(pady=(0, 4))  # spacer to align button
        apply_button = widgets.make_primary_button(apply_col, "Apply", self._refresh)
        apply_button.configure(width=110, height=theme.ENTRY_HEIGHT)
        apply_button.pack()

    def _refresh_category_options(self):
        cats = ["All"] + backend.get_categories("income") + backend.get_categories("expense")
        self.cat_menu.configure(values=cats)

    # -----------------------------------------------------------------
    # CSV
    # -----------------------------------------------------------------

    def _export_csv(self):
        email = self._current_email()
        if not email:
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv")],
            title="Export transactions to CSV",
        )
        if not file_path:
            return
        success, message, _ = backend.export_transactions_csv(email, file_path)
        self.import_result_label.configure(
            text=message, text_color=theme.COLOR_PRIMARY if success else theme.COLOR_DANGER
        )

    def _import_csv(self):
        email = self._current_email()
        if not email:
            return
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv")], title="Import transactions from CSV",
        )
        if not file_path:
            return
        success, message, data = backend.import_transactions_csv(email, file_path)
        if data and data.get("errors"):
            message += "\n" + "\n".join(data["errors"][:5])
            if len(data["errors"]) > 5:
                message += f"\n...and {len(data['errors']) - 5} more."
        self.import_result_label.configure(
            text=message, text_color=theme.COLOR_PRIMARY if success else theme.COLOR_DANGER
        )
        self._refresh()

    # -----------------------------------------------------------------
    # Data / rendering
    # -----------------------------------------------------------------

    def _current_email(self):
        user = self.controller.session.get("current_user")
        return user["email"] if user else None

    def on_show(self):
        self._refresh_category_options()
        self.import_result_label.configure(text="")
        self._refresh()

    def _refresh(self):
        for widget in self.breakdown_frame.winfo_children():
            widget.destroy()
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        email = self._current_email()
        if not email:
            return

        start = self.start_entry.get().strip() or None
        end = self.end_entry.get().strip() or None
        txn_type = self.type_var.get()
        category = self.cat_var.get()

        rows = backend.get_report_transactions(email, start, end, txn_type, category)

        # --- Category breakdown (expenses only, ignores the type filter so it's always meaningful)
        breakdown = backend.get_category_breakdown(email, start, end, "expense")
        inner = ctk.CTkFrame(self.breakdown_frame, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=16)
        ctk.CTkLabel(
            inner, text="Spending by Category", font=theme.FONT_SECTION_TITLE,
            text_color=theme.COLOR_TEXT_DARK, anchor="w",
        ).pack(anchor="w", pady=(0, 10))

        if not breakdown:
            ctk.CTkLabel(
                inner, text="No expense data for this filter.", font=theme.FONT_LABEL,
                text_color=theme.COLOR_TEXT_MUTED,
            ).pack(anchor="w")
        else:
            max_amount = breakdown[0]["total"]
            for item in breakdown:
                widgets.make_category_bar_row(
                    inner, item["category"], item["total"], max_amount, theme.COLOR_EXPENSE
                )

        # --- Transaction table
        table_inner = ctk.CTkFrame(self.table_frame, fg_color="transparent")
        table_inner.pack(fill="both", expand=True, padx=18, pady=16)

        header = ctk.CTkFrame(table_inner, fg_color="transparent")
        header.pack(fill="x", pady=(0, 8))
        for text, width in (("Date", 100), ("Type", 80), ("Category", 140), ("Amount", 100), ("Note", 200)):
            ctk.CTkLabel(
                header, text=text, font=theme.FONT_TABLE_HEADER, text_color=theme.COLOR_TEXT_MUTED,
                width=width, anchor="w",
            ).pack(side="left")

        if not rows:
            ctk.CTkLabel(
                table_inner, text="No transactions match this filter.", font=theme.FONT_LABEL,
                text_color=theme.COLOR_TEXT_MUTED,
            ).pack(pady=20)
            return

        for r in rows:
            row_frame = ctk.CTkFrame(table_inner, fg_color="transparent")
            row_frame.pack(fill="x", pady=3)
            color = theme.COLOR_INCOME if r["type"] == "income" else theme.COLOR_EXPENSE
            ctk.CTkLabel(row_frame, text=r["date"], font=theme.FONT_TABLE_CELL, width=100, anchor="w").pack(side="left")
            ctk.CTkLabel(row_frame, text=r["type"], font=theme.FONT_TABLE_CELL, text_color=color, width=80, anchor="w").pack(side="left")
            ctk.CTkLabel(row_frame, text=r["category"], font=theme.FONT_TABLE_CELL, width=140, anchor="w").pack(side="left")
            ctk.CTkLabel(row_frame, text=f"Rs. {r['amount']:,.2f}", font=theme.FONT_TABLE_CELL, width=100, anchor="w").pack(side="left")
            ctk.CTkLabel(row_frame, text=r["note"] or "-", font=theme.FONT_TABLE_CELL, width=200, anchor="w").pack(side="left")