"""Balance computation and debt simplification for a group.

Net balance per user = (what they paid) - (their share of expenses),
adjusted by settlements. A positive net means the group owes that user;
a negative net means that user owes the group.
"""
from collections import defaultdict

from models import Expense, Settlement, User

# Amounts below this (in currency units) are treated as fully settled, to avoid
# float dust producing spurious 0.00 debts.
EPSILON = 0.01


def compute_net_balances(group_id):
    """Return {user_id: net_amount} for everyone involved in the group."""
    nets = defaultdict(float)

    for expense in Expense.query.filter_by(group_id=group_id).all():
        nets[expense.paid_by] += expense.amount
        for split in expense.splits:
            nets[split.user_id] -= split.share

    for s in Settlement.query.filter_by(group_id=group_id).all():
        # Payer hands money to payee, reducing the payer's debt.
        nets[s.payer_id] += s.amount
        nets[s.payee_id] -= s.amount

    return {uid: round(amt, 2) for uid, amt in nets.items()}


def simplify_debts(nets):
    """Greedily reduce net balances to a minimal set of 'who pays whom'.

    Returns a list of {"from": uid, "to": uid, "amount": x} transactions.
    """
    creditors = sorted(
        ([uid, amt] for uid, amt in nets.items() if amt > EPSILON),
        key=lambda x: -x[1],
    )
    debtors = sorted(
        ([uid, -amt] for uid, amt in nets.items() if amt < -EPSILON),
        key=lambda x: -x[1],
    )

    transactions = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        debtor, creditor = debtors[i], creditors[j]
        pay = round(min(debtor[1], creditor[1]), 2)
        if pay > 0:
            transactions.append({"from": debtor[0], "to": creditor[0], "amount": pay})
        debtor[1] = round(debtor[1] - pay, 2)
        creditor[1] = round(creditor[1] - pay, 2)
        if debtor[1] <= EPSILON:
            i += 1
        if creditor[1] <= EPSILON:
            j += 1

    return transactions


def group_balance_summary(group_id):
    """Net balances and simplified settle-up suggestions, with user names."""
    nets = compute_net_balances(group_id)
    names = {u.id: u.name for u in User.query.all()}

    balances = [
        {"user_id": uid, "user_name": names.get(uid), "net": amt}
        for uid, amt in sorted(nets.items())
    ]
    settle_up = [
        {
            "from": t["from"],
            "from_name": names.get(t["from"]),
            "to": t["to"],
            "to_name": names.get(t["to"]),
            "amount": t["amount"],
        }
        for t in simplify_debts(nets)
    ]
    return {"balances": balances, "settle_up": settle_up}


def split_amount_equally(amount, user_ids):
    """Split amount equally, pushing rounding remainder onto the first user so
    the shares always sum exactly to amount."""
    n = len(user_ids)
    base = round(amount / n, 2)
    shares = {uid: base for uid in user_ids}
    remainder = round(amount - base * n, 2)
    shares[user_ids[0]] = round(shares[user_ids[0]] + remainder, 2)
    return shares
