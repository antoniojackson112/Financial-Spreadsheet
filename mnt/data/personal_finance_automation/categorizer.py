from database import get_rules


def categorize(merchant: str | None, description: str | None, amount: float):
    text = f"{merchant or ''} {description or ''}".upper()

    for rule in get_rules():
        if rule["pattern"].upper() in text:
            tx_type = rule["transaction_type"] or ("Income" if amount > 0 else "Expense")
            return {
                "transaction_type": tx_type,
                "category": rule["category"],
                "subcategory": rule["subcategory"],
                "recurring": int(rule["recurring"]),
                "review": False,
            }

    if amount > 0:
        return {"transaction_type": "Income", "category": "Uncategorized", "subcategory": "Uncategorized", "recurring": 0, "review": True}
    return {"transaction_type": "Expense", "category": "Uncategorized", "subcategory": "Uncategorized", "recurring": 0, "review": True}
