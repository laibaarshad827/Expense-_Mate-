"""
widgets.py
==========
Small helper functions that build consistently-styled widgets, so every
screen file stays short and every screen looks the same (NFR / Day 8:
"consistent UI, spacing, fonts, colors, buttons, forms").
"""

import customtkinter as ctk
from PIL import Image
import theme

# Cache so we don't reload/re-decode the logo file every time a screen is built.
_logo_image_cache = {}


def get_logo_image(size=120):
    """Returns a CTkImage of the app logo at the given pixel size (cached)."""
    if size not in _logo_image_cache:
        pil_img = Image.open(theme.LOGO_PATH)
        _logo_image_cache[size] = ctk.CTkImage(
            light_image=pil_img, dark_image=pil_img, size=(size, size)
        )
    return _logo_image_cache[size]


def make_title(parent, text):
    return ctk.CTkLabel(parent, text=text, font=theme.FONT_TITLE, text_color=theme.COLOR_TEXT_DARK)


def make_subtitle(parent, text):
    return ctk.CTkLabel(
        parent, text=text, font=theme.FONT_SUBTITLE, text_color=theme.COLOR_TEXT_MUTED
    )


def make_field_label(parent, text):
    return ctk.CTkLabel(
        parent, text=text, font=theme.FONT_FIELD_LABEL, text_color=theme.COLOR_TEXT_DARK, anchor="w"
    )


def make_entry(parent, placeholder, show=None):
    return ctk.CTkEntry(
        parent,
        placeholder_text=placeholder,
        width=theme.ENTRY_WIDTH,
        height=theme.ENTRY_HEIGHT,
        corner_radius=theme.CORNER_RADIUS,
        show=show,
        border_color=theme.COLOR_PRIMARY,
        border_width=1,
    )


def make_field(parent, label_text, placeholder, show=None):
    """A labeled input field: a bold label sitting directly above the entry
    box, plus placeholder text inside the box itself (e.g. label
    'Email Address' + placeholder 'Enter your email'). Returns
    (wrapper_frame, entry_widget) — pack the wrapper, use the entry to
    read/clear the value.
    """
    wrapper = ctk.CTkFrame(parent, fg_color="transparent")
    make_field_label(wrapper, label_text).pack(fill="x", padx=2, pady=(0, 4))
    entry = make_entry(wrapper, placeholder, show=show)
    entry.pack()
    return wrapper, entry


def make_brand_panel(parent, tagline="Track. Budget. Save."):
    """Left-hand green branding panel used on Login/Register: logo, app
    name, and a short tagline. Fills whatever space its caller grid/pack
    gives it, so it scales with the window.
    """
    panel = ctk.CTkFrame(parent, fg_color=theme.COLOR_PRIMARY, corner_radius=0)

    content = ctk.CTkFrame(panel, fg_color="transparent")
    content.place(relx=0.5, rely=0.5, anchor="center")

    logo_label = ctk.CTkLabel(content, image=get_logo_image(150), text="")
    logo_label.image = get_logo_image(150)  # keep a reference, just in case
    logo_label.pack(pady=(0, 24))

    ctk.CTkLabel(
        content, text="ExpenseMate", font=theme.FONT_APP_NAME, text_color="white"
    ).pack()
    ctk.CTkLabel(
        content, text=tagline, font=theme.FONT_SUBTITLE, text_color=theme.COLOR_PRIMARY_LIGHT
    ).pack(pady=(6, 0))

    return panel


def make_mini_header(parent):
    """A small logo + app name row used at the top of secondary screens
    (OTP, forgot/reset password, update password/email, dashboard) so the
    branding stays consistent without needing a full split layout.
    """
    header = ctk.CTkFrame(parent, fg_color="transparent")
    logo_label = ctk.CTkLabel(header, image=get_logo_image(44), text="")
    logo_label.image = get_logo_image(44)
    logo_label.pack(side="left", padx=(0, 10))
    ctk.CTkLabel(
        header, text="ExpenseMate", font=("Segoe UI", 18, "bold"), text_color=theme.COLOR_PRIMARY
    ).pack(side="left")
    return header


def make_primary_button(parent, text, command):
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        width=theme.BUTTON_WIDTH,
        height=theme.BUTTON_HEIGHT,
        corner_radius=theme.CORNER_RADIUS,
        font=theme.FONT_BUTTON,
        fg_color=theme.COLOR_PRIMARY,
        hover_color=theme.COLOR_PRIMARY_HOVER,
    )


def make_link_button(parent, text, command):
    """A button styled like a clickable text link (e.g. 'Forgot password?')."""
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        font=theme.FONT_LINK,
        fg_color="transparent",
        hover_color="#e8e8e8",
        text_color=theme.COLOR_PRIMARY,
        width=theme.BUTTON_WIDTH,
        height=28,
    )


def make_error_label(parent):
    """A label reserved for validation/error messages (NFR-6)."""
    return ctk.CTkLabel(
        parent, text="", font=theme.FONT_LABEL, text_color=theme.COLOR_DANGER, wraplength=320
    )


def make_success_label(parent):
    return ctk.CTkLabel(
        parent, text="", font=theme.FONT_LABEL, text_color=theme.COLOR_PRIMARY, wraplength=320
    )


# ---------------------------------------------------------------------------
# App shell: sidebar navigation used by Dashboard / Transactions / etc.
# ---------------------------------------------------------------------------
NAV_ITEMS = (
    # (label, icon, target_screen_name, enabled)
    ("Dashboard", "🏠", "DashboardScreen", True),
    ("Transactions", "💳", "TransactionsScreen", True),
    ("Budgets", "📊", "BudgetsScreen", True),
    ("Savings", "🎯", "SavingsScreen", True),
    ("Reports", "📁", "ReportsScreen", True),
)


def make_sidebar(parent, controller, active_screen):
    """Dark navigation rail shared by every 'inside the app' screen.

    `active_screen` is the class name of the currently visible screen
    (e.g. "DashboardScreen") so the matching nav item is highlighted.
    Items with no target screen are rendered disabled ("coming soon" -
    they belong to later days on the roadmap).
    """
    sidebar = ctk.CTkFrame(
        parent, fg_color=theme.COLOR_SIDEBAR_BG, corner_radius=0, width=theme.SIDEBAR_WIDTH
    )
    sidebar.pack_propagate(False)
    sidebar.grid_propagate(False)

    # Brand row
    brand = ctk.CTkFrame(sidebar, fg_color="transparent")
    brand.pack(fill="x", padx=20, pady=(26, 30))
    logo_label = ctk.CTkLabel(brand, image=get_logo_image(36), text="")
    logo_label.image = get_logo_image(36)
    logo_label.pack(side="left", padx=(0, 8))
    ctk.CTkLabel(
        brand, text="ExpenseMate", font=("Segoe UI", 16, "bold"), text_color="white"
    ).pack(side="left")

    nav_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
    nav_frame.pack(fill="x", padx=12)

    for label, icon, target, enabled in NAV_ITEMS:
        is_active = target == active_screen
        if not enabled:
            row = ctk.CTkFrame(nav_frame, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(
                row,
                text=f"{icon}  {label}",
                font=theme.FONT_SIDEBAR_ITEM,
                text_color=theme.COLOR_SIDEBAR_TEXT_MUTED,
                anchor="w",
            ).pack(fill="x", padx=14, pady=10)
            ctk.CTkLabel(
                row, text="soon", font=theme.FONT_SMALL, text_color=theme.COLOR_SIDEBAR_TEXT_MUTED
            ).place(relx=0.98, rely=0.5, anchor="e")
            continue

        btn = ctk.CTkButton(
            nav_frame,
            text=f"{icon}  {label}",
            anchor="w",
            font=theme.FONT_SIDEBAR_ITEM,
            fg_color=theme.COLOR_SIDEBAR_ACTIVE if is_active else "transparent",
            hover_color=theme.COLOR_SIDEBAR_HOVER,
            text_color="white" if is_active else theme.COLOR_SIDEBAR_TEXT,
            corner_radius=8,
            height=42,
            command=lambda t=target: controller.show_screen(t),
        )
        btn.pack(fill="x", pady=3)

    # Bottom account section: Update Password / Update Email / Logout
    bottom = ctk.CTkFrame(sidebar, fg_color="transparent")
    bottom.pack(side="bottom", fill="x", padx=12, pady=18)

    ctk.CTkFrame(bottom, fg_color=theme.COLOR_SIDEBAR_HOVER, height=1).pack(fill="x", pady=(0, 10))

    for label, icon, target in (
        ("Update Password", "🔑", "UpdatePasswordScreen"),
        ("Update Email", "✉️", "UpdateEmailScreen"),
    ):
        ctk.CTkButton(
            bottom,
            text=f"{icon}  {label}",
            anchor="w",
            font=theme.FONT_SMALL,
            fg_color="transparent",
            hover_color=theme.COLOR_SIDEBAR_HOVER,
            text_color=theme.COLOR_SIDEBAR_TEXT_MUTED,
            corner_radius=8,
            height=32,
            command=lambda t=target: controller.show_screen(t),
        ).pack(fill="x", pady=2)

    ctk.CTkButton(
        bottom,
        text="⎋  Log Out",
        anchor="w",
        font=theme.FONT_SIDEBAR_ITEM,
        fg_color="transparent",
        hover_color=theme.COLOR_DANGER,
        text_color="#F3B9B0",
        corner_radius=8,
        height=38,
        command=lambda: _do_logout(controller),
    ).pack(fill="x", pady=(10, 0))

    return sidebar


def _do_logout(controller):
    import backend_interface as backend

    backend.logout_user()
    controller.session["current_user"] = None
    controller.show_screen("LoginScreen")


def make_app_page(parent, controller, active_screen):
    """Standard 'inside the app' layout: dark sidebar (left) + light
    scrollable content area (right). Returns (shell_frame, content_frame).
    Screens pack/grid their own widgets into `content_frame`.
    """
    shell = ctk.CTkFrame(parent, fg_color=theme.COLOR_BG_APP, corner_radius=0)
    shell.grid_columnconfigure(1, weight=1)
    shell.grid_rowconfigure(0, weight=1)

    sidebar = make_sidebar(shell, controller, active_screen)
    sidebar.grid(row=0, column=0, sticky="nsw")

    content = ctk.CTkScrollableFrame(shell, fg_color=theme.COLOR_BG_APP, corner_radius=0)
    content.grid(row=0, column=1, sticky="nsew", padx=36, pady=28)
    content.grid_columnconfigure(0, weight=1)

    return shell, content


def make_page_header(parent, title, subtitle=None):
    header = ctk.CTkFrame(parent, fg_color="transparent")
    ctk.CTkLabel(
        header, text=title, font=theme.FONT_PAGE_TITLE, text_color=theme.COLOR_TEXT_DARK, anchor="w"
    ).pack(anchor="w")
    if subtitle:
        ctk.CTkLabel(
            header, text=subtitle, font=theme.FONT_SUBTITLE, text_color=theme.COLOR_TEXT_MUTED, anchor="w"
        ).pack(anchor="w", pady=(2, 0))
    return header


# ---------------------------------------------------------------------------
# Dashboard stat cards
# ---------------------------------------------------------------------------
def make_stat_card(parent, icon, label, value_text, accent_color):
    card = ctk.CTkFrame(
        parent, fg_color=theme.COLOR_CARD_BG, corner_radius=14, border_width=1,
        border_color=theme.COLOR_BORDER,
    )
    inner = ctk.CTkFrame(card, fg_color="transparent")
    inner.pack(fill="both", expand=True, padx=20, pady=18)

    top = ctk.CTkFrame(inner, fg_color="transparent")
    top.pack(fill="x")

    badge = ctk.CTkLabel(
        top, text=icon, font=("Segoe UI", 16), text_color=accent_color, fg_color=theme.COLOR_BG_APP,
        width=34, height=34, corner_radius=17,
    )
    badge.pack(side="left")

    ctk.CTkLabel(
        inner, text=label, font=theme.FONT_STAT_LABEL, text_color=theme.COLOR_TEXT_MUTED, anchor="w"
    ).pack(fill="x", pady=(14, 2))

    value_label = ctk.CTkLabel(
        inner, text=value_text, font=theme.FONT_STAT_VALUE, text_color=accent_color, anchor="w"
    )
    value_label.pack(fill="x")

    card.value_label = value_label  # so callers can update it later
    return card


# ---------------------------------------------------------------------------
# Category / type dropdowns
# ---------------------------------------------------------------------------
def make_dropdown(parent, values, command=None, width=200):
    var = ctk.StringVar(value=values[0] if values else "")
    menu = ctk.CTkOptionMenu(
        parent,
        variable=var,
        values=list(values),
        width=width,
        height=theme.ENTRY_HEIGHT,
        corner_radius=theme.CORNER_RADIUS,
        fg_color="white",
        button_color=theme.COLOR_PRIMARY,
        button_hover_color=theme.COLOR_PRIMARY_HOVER,
        text_color=theme.COLOR_TEXT_DARK,
        dropdown_fg_color="white",
        dropdown_text_color=theme.COLOR_TEXT_DARK,
        dropdown_hover_color=theme.COLOR_PRIMARY_LIGHT,
        command=command,
    )
    return menu, var


def make_pill(parent, text, bg_color, fg_color):
    """A small rounded 'chip' label (used for category tags). CTkLabel has
    no padx option, so the padding comes from a wrapping frame instead.
    """
    pill = ctk.CTkFrame(parent, fg_color=bg_color, corner_radius=10)
    ctk.CTkLabel(
        pill, text=text, font=("Segoe UI", 11, "bold"), text_color=fg_color, fg_color="transparent",
    ).pack(padx=10, pady=2)
    return pill


def make_icon_button(parent, text, command, color, hover_color, width=34):
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        width=width,
        height=30,
        corner_radius=8,
        font=("Segoe UI", 13),
        fg_color=color,
        hover_color=hover_color,
        text_color="white",
    )


# ---------------------------------------------------------------------------
# Budgets (Day 3 - FR-7..FR-10)
# ---------------------------------------------------------------------------
def make_alert_banner(parent, over_budget_statuses):
    """FR-9: a red banner listing every category currently over budget.
    Returns None (renders nothing) if the list is empty."""
    if not over_budget_statuses:
        return None
    names = ", ".join(s["category"] for s in over_budget_statuses)
    banner = ctk.CTkFrame(parent, fg_color=theme.COLOR_EXPENSE_LIGHT, corner_radius=12)
    ctk.CTkLabel(
        banner, text=f"⚠  Over budget this month: {names}", font=theme.FONT_FIELD_LABEL,
        text_color=theme.COLOR_EXPENSE, anchor="w",
    ).pack(fill="x", padx=18, pady=12)
    return banner


def make_budget_row(parent, status, on_set_budget):
    """One category's budget card: limit / spent / remaining + progress
    bar, and a Set/Edit button. `on_set_budget(category)` is called when
    that button is clicked. `status` is one dict from
    backend.get_budget_status().
    """
    cat, limit, spent = status["category"], status["limit"], status["spent"]
    card = ctk.CTkFrame(parent, fg_color=theme.COLOR_CARD_BG, corner_radius=12,
                         border_width=1, border_color=theme.COLOR_BORDER)
    card.pack(fill="x", pady=5)
    inner = ctk.CTkFrame(card, fg_color="transparent")
    inner.pack(fill="x", padx=18, pady=14)

    top = ctk.CTkFrame(inner, fg_color="transparent")
    top.pack(fill="x")
    make_pill(top, cat, theme.COLOR_EXPENSE_LIGHT, theme.COLOR_EXPENSE).pack(side="left")

    btn_text = "Edit Budget" if limit else "Set Budget"
    ctk.CTkButton(
        top, text=btn_text, width=100, height=28, font=theme.FONT_SMALL, corner_radius=8,
        fg_color=theme.COLOR_PRIMARY, hover_color=theme.COLOR_PRIMARY_HOVER,
        command=lambda: on_set_budget(cat),
    ).pack(side="right")

    if limit is None:
        msg = f"No budget set - spent Rs. {spent:,.2f} so far this month."
        if status["suggested"]:
            msg += f" Suggested: Rs. {status['suggested']:,.2f}/mo."
        ctk.CTkLabel(inner, text=msg, font=theme.FONT_SMALL, text_color=theme.COLOR_TEXT_MUTED,
                     anchor="w", wraplength=520).pack(fill="x", pady=(10, 0))
        return card

    over = status["over_budget"]
    bar_color = theme.COLOR_DANGER if over else (theme.COLOR_WARNING if status["percent"] >= 80 else theme.COLOR_INCOME)

    stats_row = ctk.CTkFrame(inner, fg_color="transparent")
    stats_row.pack(fill="x", pady=(10, 6))
    for label, value, color in (
        ("Budget", f"Rs. {limit:,.2f}", theme.COLOR_TEXT_DARK),
        ("Spent", f"Rs. {spent:,.2f}", theme.COLOR_TEXT_DARK),
        ("Remaining", f"Rs. {status['remaining']:,.2f}", theme.COLOR_DANGER if status["remaining"] < 0 else theme.COLOR_INCOME),
    ):
        col = ctk.CTkFrame(stats_row, fg_color="transparent")
        col.pack(side="left", padx=(0, 30))
        ctk.CTkLabel(col, text=label, font=theme.FONT_SMALL, text_color=theme.COLOR_TEXT_MUTED, anchor="w").pack(anchor="w")
        ctk.CTkLabel(col, text=value, font=theme.FONT_FIELD_LABEL, text_color=color, anchor="w").pack(anchor="w")

    bar = ctk.CTkProgressBar(inner, progress_color=bar_color, height=10, corner_radius=5)
    bar.set(min(spent / limit, 1.0))
    bar.pack(fill="x", pady=(2, 4))

    note = f"{status['percent']}% used" + ("  •  over budget!" if over else "")
    ctk.CTkLabel(inner, text=note, font=theme.FONT_SMALL,
                 text_color=theme.COLOR_DANGER if over else theme.COLOR_TEXT_MUTED, anchor="w").pack(fill="x")
    return card
# ---------------------------------------------------------------------------
# Savings goals (Day 4)
# ---------------------------------------------------------------------------

def make_goal_card(parent, goal, on_contribute, on_edit, on_delete):
    """One savings goal card: name / target / saved + progress bar, plus
    Contribute, Edit, and Delete buttons. `goal` is one dict from
    backend.get_savings_goals()."""
    card = ctk.CTkFrame(parent, fg_color=theme.COLOR_CARD_BG, corner_radius=12,
                         border_width=1, border_color=theme.COLOR_BORDER)
    card.pack(fill="x", pady=5)

    inner = ctk.CTkFrame(card, fg_color="transparent")
    inner.pack(fill="x", padx=18, pady=14)

    top = ctk.CTkFrame(inner, fg_color="transparent")
    top.pack(fill="x")

    ctk.CTkLabel(
        top, text=goal["goal_name"], font=theme.FONT_FIELD_LABEL,
        text_color=theme.COLOR_TEXT_DARK, anchor="w",
    ).pack(side="left")

    if goal["deadline"]:
        make_pill(top, f"Due {goal['deadline']}", theme.COLOR_WARNING_LIGHT, theme.COLOR_WARNING).pack(side="left", padx=(10, 0))
    if goal["is_complete"]:
        make_pill(top, "Complete!", theme.COLOR_INCOME_LIGHT, theme.COLOR_INCOME).pack(side="left", padx=(10, 0))

    btn_row = ctk.CTkFrame(top, fg_color="transparent")
    btn_row.pack(side="right")
    make_icon_button(btn_row, "💰", lambda: on_contribute(goal), theme.COLOR_PRIMARY, theme.COLOR_PRIMARY_HOVER).pack(side="left", padx=3)
    make_icon_button(btn_row, "✏️", lambda: on_edit(goal), theme.COLOR_ACCENT, "#B8862F").pack(side="left", padx=3)
    make_icon_button(btn_row, "🗑️", lambda: on_delete(goal), theme.COLOR_DANGER, theme.COLOR_DANGER_HOVER).pack(side="left", padx=3)

    stats_row = ctk.CTkFrame(inner, fg_color="transparent")
    stats_row.pack(fill="x", pady=(10, 6))
    for label, value, color in (
        ("Target", f"Rs. {goal['target_amount']:,.2f}", theme.COLOR_TEXT_DARK),
        ("Saved", f"Rs. {goal['current_amount']:,.2f}", theme.COLOR_INCOME),
        ("Remaining", f"Rs. {goal['remaining']:,.2f}", theme.COLOR_TEXT_DARK),
    ):
        col = ctk.CTkFrame(stats_row, fg_color="transparent")
        col.pack(side="left", padx=(0, 30))
        ctk.CTkLabel(col, text=label, font=theme.FONT_SMALL, text_color=theme.COLOR_TEXT_MUTED, anchor="w").pack(anchor="w")
        ctk.CTkLabel(col, text=value, font=theme.FONT_FIELD_LABEL, text_color=color, anchor="w").pack(anchor="w")

    bar = ctk.CTkProgressBar(inner, progress_color=theme.COLOR_INCOME, height=10, corner_radius=5)
    bar.set(min(goal["percent"] / 100, 1.0))
    bar.pack(fill="x", pady=(2, 4))

    ctk.CTkLabel(
        inner, text=f"{goal['percent']}% saved", font=theme.FONT_SMALL,
        text_color=theme.COLOR_TEXT_MUTED, anchor="w",
    ).pack(fill="x")

    return card
# ---------------------------------------------------------------------------
# Reports (Day 5)
# ---------------------------------------------------------------------------

def make_category_bar_row(parent, category, amount, max_amount, color):
    """One horizontal bar row for the category breakdown chart on the
    Reports screen — a label + proportional colored bar + amount."""
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", pady=6)

    top = ctk.CTkFrame(row, fg_color="transparent")
    top.pack(fill="x")
    ctk.CTkLabel(
        top, text=category, font=theme.FONT_FIELD_LABEL, text_color=theme.COLOR_TEXT_DARK, anchor="w"
    ).pack(side="left")
    ctk.CTkLabel(
        top, text=f"Rs. {amount:,.2f}", font=theme.FONT_FIELD_LABEL, text_color=color, anchor="e"
    ).pack(side="right")

    bar = ctk.CTkProgressBar(row, progress_color=color, height=10, corner_radius=5)
    bar.set(amount / max_amount if max_amount else 0)
    bar.pack(fill="x", pady=(4, 0))
    return row