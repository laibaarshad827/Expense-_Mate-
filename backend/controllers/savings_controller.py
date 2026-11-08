# backend/controllers/savings_controller.py
"""Savings controller (thin for now): routes the screens to savings_service."""
from backend.services import savings_service as _savings

create_savings_goal = _savings.create_savings_goal
get_savings_goals = _savings.get_savings_goals
get_savings_goal_by_id = _savings.get_savings_goal_by_id
update_savings_goal = _savings.update_savings_goal
delete_savings_goal = _savings.delete_savings_goal
add_savings_contribution = _savings.add_savings_contribution
get_savings_summary = _savings.get_savings_summary