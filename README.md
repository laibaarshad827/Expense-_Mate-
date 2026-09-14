# ExpenseMate — Frontend (Part 1: Auth Module)

This is the CustomTkinter frontend for ExpenseMate, covering Day 1 of your
roadmap: **Register, OTP verification, Login, Forgot Password, Reset
Password, Update Password, Update Email.**

## How to run it

```bash
pip install -r requirements.txt
python app.py
```

A window opens on the Login screen. Since your friend's real backend
isn't built yet, this currently runs against a **mock backend**
(`backend_interface.py`) that stores everything in memory (nothing is
saved to disk — closing the app resets all "accounts").

Try it end-to-end:
1. Click "Don't have an account? Register" → fill the form → Register.
2. Check the terminal/console — the mock OTP is printed there, e.g.
   `[MOCK OTP] OTP for you@example.com is: 483920`
3. Type that code into the OTP screen → you land back on Login.
4. Log in with the same email/password → you reach the (placeholder)
   dashboard, where you can also test Update Password / Update Email /
   Logout.

## What's new in this version

- **Logo & branding**: an original wallet/coin icon (`assets/logo.png`) appears
  on every screen — full-size on Login/Register's green side panel, a small
  version in the header of every other screen.
- **Labeled fields**: every input now has a bold label above it (e.g. "Email
  Address") plus descriptive placeholder text inside the box (e.g. "Enter
  your email"), instead of relying on placeholder text alone.
- **Full window**: the app now opens maximized and is resizable, instead of a
  small fixed-size box.

## File structure

```
frontend/
├── app.py                      # entry point + screen navigation controller
├── backend_interface.py        # THE CONTRACT with the backend (see below)
├── theme.py                    # colors/fonts/sizes, change once, applies everywhere
├── widgets.py                  # reusable styled widget builders (fields, buttons, logo, headers)
├── requirements.txt
├── assets/
│   └── logo.png                # original app icon (wallet + coin), used across all screens
└── screens/
    ├── login_screen.py
    ├── register_screen.py
    ├── otp_screen.py            # shared by register / forgot-password / update-email
    ├── forgot_password_screen.py
    ├── reset_password_screen.py
    ├── update_password_screen.py
    ├── update_email_screen.py
    └── dashboard_placeholder_screen.py   # temporary, replaced in Part 2
```

## How this connects to your friend's backend

Every screen file only ever calls functions from `backend_interface.py`
— never the database directly. That file documents the exact function
names, parameters, and return format (`success, message, data`) that
your friend's real backend needs to match.

**On integration day (Day 6 of your roadmap):**
- Your friend writes her real functions (e.g. in `auth_service.py`,
  using actual SQLite + password hashing + a real email/OTP service)
  with the *same function names and same return format*.
- You swap the mock file for her real module — none of the screen files
  need to change.

This is exactly the kind of clean frontend/backend split the roadmap
and your SRS (NFR-9: modular design) call for.

## What's next (Part 2)

Once you're happy with this, the next parts follow your roadmap:
- **Part 2:** Transactions + Categories (Day 2)
- **Part 3:** Budgets (Day 3)
- **Part 4:** Savings + real Dashboard with charts (Day 4)
- **Part 5:** CSV import/export + Reports (Day 5)

Each part will plug into `backend_interface.py` the same way.
