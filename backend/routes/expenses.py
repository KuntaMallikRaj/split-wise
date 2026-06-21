from flask import Blueprint, request, jsonify

from extensions import db
from models import Expense, ExpenseSplit, Group, GroupMember
from services.balances import split_amount_equally, EPSILON

expenses_bp = Blueprint("expenses", __name__)


@expenses_bp.route("/api/expenses", methods=["POST"])
def create_expense():
    """
    Body:
      {
        "group_id": 1,
        "description": "Dinner",
        "amount": 90.0,
        "paid_by": 2,
        "split_type": "equal",                       # equal | exact
        "participants": [1, 2, 3],                   # for equal split
        "shares": [{"user_id": 1, "share": 30}, ...] # for exact split
      }
    """
    data = request.get_json(silent=True) or {}

    group_id = data.get("group_id")
    description = (data.get("description") or "").strip()
    paid_by = data.get("paid_by")
    split_type = data.get("split_type", "equal")

    try:
        amount = round(float(data.get("amount")), 2)
    except (TypeError, ValueError):
        return jsonify({"error": "amount must be a number"}), 400

    if not Group.query.get(group_id):
        return jsonify({"error": "group not found"}), 404
    if not description:
        return jsonify({"error": "description is required"}), 400
    if amount <= 0:
        return jsonify({"error": "amount must be positive"}), 400

    member_ids = {m.user_id for m in GroupMember.query.filter_by(group_id=group_id).all()}
    if paid_by not in member_ids:
        return jsonify({"error": "paid_by must be a member of the group"}), 400

    # Build the per-user shares depending on split type.
    if split_type == "exact":
        shares_in = data.get("shares") or []
        if not shares_in:
            return jsonify({"error": "shares are required for an exact split"}), 400
        shares = {}
        for item in shares_in:
            uid = item.get("user_id")
            if uid not in member_ids:
                return jsonify({"error": f"user {uid} is not a member of the group"}), 400
            try:
                shares[uid] = round(float(item.get("share")), 2)
            except (TypeError, ValueError):
                return jsonify({"error": "each share must be a number"}), 400
        if abs(sum(shares.values()) - amount) > EPSILON:
            return jsonify({"error": "shares must sum to the total amount"}), 400
    else:  # equal
        participants = data.get("participants") or list(member_ids)
        participants = [p for p in participants if p in member_ids]
        if not participants:
            return jsonify({"error": "at least one valid participant is required"}), 400
        shares = split_amount_equally(amount, participants)

    expense = Expense(
        group_id=group_id,
        description=description,
        amount=amount,
        paid_by=paid_by,
        split_type=split_type,
    )
    db.session.add(expense)
    db.session.flush()

    for uid, share in shares.items():
        db.session.add(ExpenseSplit(expense_id=expense.id, user_id=uid, share=share))

    db.session.commit()
    return jsonify(expense.to_dict()), 201


@expenses_bp.route("/api/expenses/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    expense = Expense.query.get(expense_id)
    if not expense:
        return jsonify({"error": "expense not found"}), 404
    db.session.delete(expense)
    db.session.commit()
    return jsonify({"status": "deleted", "id": expense_id})
