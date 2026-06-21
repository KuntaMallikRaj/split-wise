from flask import Blueprint, request, jsonify

from extensions import db
from models import Group, GroupMember, User, Expense, Settlement
from services.balances import group_balance_summary

groups_bp = Blueprint("groups", __name__)


@groups_bp.route("/api/groups", methods=["GET"])
def list_groups():
    return jsonify([g.to_dict() for g in Group.query.order_by(Group.created_at.desc()).all()])


@groups_bp.route("/api/groups", methods=["POST"])
def create_group():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    group = Group(name=name)
    db.session.add(group)
    db.session.flush()  # assign group.id before adding members

    for user_id in data.get("member_ids", []):
        if User.query.get(user_id):
            db.session.add(GroupMember(group_id=group.id, user_id=user_id))

    db.session.commit()
    return jsonify(group.to_dict()), 201


@groups_bp.route("/api/groups/<int:group_id>", methods=["GET"])
def get_group(group_id):
    group = Group.query.get(group_id)
    if not group:
        return jsonify({"error": "group not found"}), 404

    data = group.to_dict()
    data["expenses"] = [
        e.to_dict()
        for e in Expense.query.filter_by(group_id=group_id).order_by(Expense.created_at.desc()).all()
    ]
    data["settlements"] = [
        s.to_dict()
        for s in Settlement.query.filter_by(group_id=group_id).order_by(Settlement.created_at.desc()).all()
    ]
    data.update(group_balance_summary(group_id))
    return jsonify(data)


@groups_bp.route("/api/groups/<int:group_id>/members", methods=["POST"])
def add_member(group_id):
    if not Group.query.get(group_id):
        return jsonify({"error": "group not found"}), 404

    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    if not User.query.get(user_id):
        return jsonify({"error": "user not found"}), 404

    exists = GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
    if exists:
        return jsonify({"error": "user already in group"}), 409

    db.session.add(GroupMember(group_id=group_id, user_id=user_id))
    db.session.commit()
    return jsonify(Group.query.get(group_id).to_dict()), 201
