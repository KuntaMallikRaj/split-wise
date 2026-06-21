from flask import Blueprint, request, jsonify

from extensions import db
from models import Settlement, Group, GroupMember

settlements_bp = Blueprint("settlements", __name__)


@settlements_bp.route("/api/settlements", methods=["POST"])
def create_settlement():
    """Record that payer paid payee to settle up. Body:
    {"group_id": 1, "payer_id": 2, "payee_id": 3, "amount": 20.0}"""
    data = request.get_json(silent=True) or {}

    group_id = data.get("group_id")
    payer_id = data.get("payer_id")
    payee_id = data.get("payee_id")

    try:
        amount = round(float(data.get("amount")), 2)
    except (TypeError, ValueError):
        return jsonify({"error": "amount must be a number"}), 400

    if not Group.query.get(group_id):
        return jsonify({"error": "group not found"}), 404
    if payer_id == payee_id:
        return jsonify({"error": "payer and payee must be different"}), 400
    if amount <= 0:
        return jsonify({"error": "amount must be positive"}), 400

    member_ids = {m.user_id for m in GroupMember.query.filter_by(group_id=group_id).all()}
    if payer_id not in member_ids or payee_id not in member_ids:
        return jsonify({"error": "payer and payee must be members of the group"}), 400

    settlement = Settlement(
        group_id=group_id, payer_id=payer_id, payee_id=payee_id, amount=amount
    )
    db.session.add(settlement)
    db.session.commit()
    return jsonify(settlement.to_dict()), 201
