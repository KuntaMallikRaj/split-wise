from datetime import datetime

from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email}


class Group(db.Model):
    __tablename__ = "groups"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    members = db.relationship("GroupMember", backref="group", cascade="all, delete-orphan")
    expenses = db.relationship("Expense", backref="group", cascade="all, delete-orphan")
    settlements = db.relationship("Settlement", backref="group", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "members": [m.user.to_dict() for m in self.members],
        }


class GroupMember(db.Model):
    __tablename__ = "group_members"
    __table_args__ = (db.UniqueConstraint("group_id", "user_id", name="uq_group_user"),)

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    user = db.relationship("User")


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    paid_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    split_type = db.Column(db.String(20), default="equal", nullable=False)  # equal | exact
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    splits = db.relationship("ExpenseSplit", backref="expense", cascade="all, delete-orphan")
    payer = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "group_id": self.group_id,
            "description": self.description,
            "amount": round(self.amount, 2),
            "paid_by": self.paid_by,
            "payer_name": self.payer.name if self.payer else None,
            "split_type": self.split_type,
            "created_at": self.created_at.isoformat(),
            "splits": [s.to_dict() for s in self.splits],
        }


class ExpenseSplit(db.Model):
    __tablename__ = "expense_splits"

    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey("expenses.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    share = db.Column(db.Float, nullable=False)

    user = db.relationship("User")

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else None,
            "share": round(self.share, 2),
        }


class Settlement(db.Model):
    __tablename__ = "settlements"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=False)
    payer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    payee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    payer = db.relationship("User", foreign_keys=[payer_id])
    payee = db.relationship("User", foreign_keys=[payee_id])

    def to_dict(self):
        return {
            "id": self.id,
            "group_id": self.group_id,
            "payer_id": self.payer_id,
            "payer_name": self.payer.name if self.payer else None,
            "payee_id": self.payee_id,
            "payee_name": self.payee.name if self.payee else None,
            "amount": round(self.amount, 2),
            "created_at": self.created_at.isoformat(),
        }
