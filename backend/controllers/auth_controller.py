# backend/controllers/auth_controller.py
"""Auth controller (thin for now). Rewritten in Part C, where the basic input
validation moves up into this layer."""
from backend.services import auth_service as _auth

register_user = _auth.register_user
send_otp = _auth.send_otp
verify_otp = _auth.verify_otp
login_user = _auth.login_user
logout_user = _auth.logout_user
request_password_reset = _auth.request_password_reset
reset_password = _auth.reset_password
update_password = _auth.update_password
update_email = _auth.update_email
is_valid_email = _auth.is_valid_email
is_valid_password = _auth.is_valid_password