import hashlib
import os
from datetime import datetime, timezone

from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest

from categorizer import categorize
from database import connect
from plaid_client import client
from security import get_access_token


def fingerprint(account_id, date, merchant, description, amount):
    raw = f"{account_id}|{date}|{merchant or ''}|{description or ''}|{amount:.2f}"
    return hashlib.sha256(raw.encode()).hexdigest()


def sync_item(item_id: str):
    access_token = get_access_token(item_id)
    if not access_token:
        raise RuntimeError(f"No access token available for item {item_id}")

    started = datetime.now(timezone.utc).isoformat()
    with connect() as con:
        row = con.execute("SELECT cursor FROM plaid_items WHERE item_id=?", (item_id,)).fetchone()
        cursor = row[0] if row else None

    added, modified, removed = [], [], []
    has_more = True
    first_pass = cursor or ""

    while has_more:
        req_kwargs = {"access_token": access_token}
        if cursor:
            req_kwargs["cursor"] = cursor
        response = client().transactions_sync(TransactionsSyncRequest(**req_kwargs)).to_dict()
        added.extend(response.get("added", []))
        modified.extend(response.get("modified", []))
        removed.extend(response.get("removed", []))
        cursor = response.get("next_cursor", "")
        has_more = bool(response.get("has_more"))
        if not cursor and not added and not modified and not removed:
            break

    now = datetime.now(timezone.utc).isoformat()
    added_count = modified_count = removed_count = 0

    with connect() as con:
        # Pull standardized account balances and map them to internal account IDs.
        acct_resp = client().accounts_balance_get(AccountsBalanceGetRequest(access_token=access_token)).to_dict()
        institution = None
        for a in acct_resp.get("accounts", []):
            external_id = a["account_id"]
            existing = con.execute("SELECT account_id FROM accounts WHERE external_account_id=?", (external_id,)).fetchone()
            account_id = existing[0] if existing else f"PLAID_{external_id[:8]}"
            balance = a.get("balances", {})
            con.execute("""
                INSERT INTO accounts(account_id,item_id,institution,account_name,account_type,currency,current_balance,external_account_id,last_sync)
                VALUES(?,?,?,?,?,?,?,?,?)
                ON CONFLICT(external_account_id) DO UPDATE SET
                    account_name=excluded.account_name,
                    account_type=excluded.account_type,
                    currency=excluded.currency,
                    current_balance=excluded.current_balance,
                    last_sync=excluded.last_sync
            """, (
                account_id, item_id, institution, a.get("name"), a.get("type"),
                balance.get("iso_currency_code") or "USD", balance.get("current"), external_id, now
            ))

        for t in added:
            account_id = con.execute("SELECT account_id FROM accounts WHERE external_account_id=(SELECT account_id FROM accounts WHERE account_id IS NOT NULL AND external_account_id IS NOT NULL LIMIT 1)").fetchone()
            ext_account = t.get("account_id")
            row = con.execute("SELECT account_id FROM accounts WHERE external_account_id=?", (ext_account,)).fetchone()
            if not row:
                continue
            account_id = row[0]
            amount = float(t.get("amount", 0.0))
            merchant = t.get("merchant_name")
            description = t.get("name") or merchant or ""
            date_value = t.get("date")
            date_str = str(date_value)
            cat = categorize(merchant, description, -amount)
            fp = fingerprint(account_id, date_str, merchant, description, -amount)

            con.execute("""
                INSERT INTO transactions(transaction_id,account_id,date,merchant,description,amount,currency,transaction_type,category,subcategory,recurring,pending,source,fingerprint,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(transaction_id) DO UPDATE SET
                    account_id=excluded.account_id,
                    date=excluded.date,
                    merchant=excluded.merchant,
                    description=excluded.description,
                    amount=excluded.amount,
                    category=excluded.category,
                    subcategory=excluded.subcategory,
                    transaction_type=excluded.transaction_type,
                    recurring=excluded.recurring,
                    pending=excluded.pending,
                    updated_at=excluded.updated_at
            """, (
                t["transaction_id"], account_id, date_str, merchant, description, -amount,
                (t.get("iso_currency_code") or "USD"), cat["transaction_type"], cat["category"],
                cat["subcategory"], cat["recurring"], int(t.get("pending", False)), "Plaid", fp, now, now
            ))
            added_count += 1

        for t in modified:
            con.execute("DELETE FROM transactions WHERE transaction_id=?", (t["transaction_id"],))
            ext_account = t.get("account_id")
            row = con.execute("SELECT account_id FROM accounts WHERE external_account_id=?", (ext_account,)).fetchone()
            if not row:
                continue
            account_id = row[0]
            amount = float(t.get("amount", 0.0))
            merchant = t.get("merchant_name")
            description = t.get("name") or merchant or ""
            date_str = str(t.get("date"))
            cat = categorize(merchant, description, -amount)
            fp = fingerprint(account_id, date_str, merchant, description, -amount)
            con.execute("""
                INSERT INTO transactions(transaction_id,account_id,date,merchant,description,amount,currency,transaction_type,category,subcategory,recurring,pending,source,fingerprint,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                t["transaction_id"], account_id, date_str, merchant, description, -amount,
                (t.get("iso_currency_code") or "USD"), cat["transaction_type"], cat["category"],
                cat["subcategory"], cat["recurring"], int(t.get("pending", False)), "Plaid", fp, now, now
            ))
            modified_count += 1

        for t in removed:
            con.execute("DELETE FROM transactions WHERE transaction_id=?", (t["transaction_id"],))
            removed_count += 1

        con.execute("UPDATE plaid_items SET cursor=?, updated_at=? WHERE item_id=?", (cursor, now, item_id))
        con.execute("""
            INSERT INTO sync_log(started_at,completed_at,transactions_added,transactions_modified,transactions_removed,status,error)
            VALUES(?,?,?,?,?,?,?)
        """, (started, now, added_count, modified_count, removed_count, "OK", None))

    return {"added": added_count, "modified": modified_count, "removed": removed_count, "cursor": cursor}


def sync_all():
    with connect() as con:
        items = [r[0] for r in con.execute("SELECT item_id FROM plaid_items").fetchall()]
    results = {}
    for item_id in items:
        results[item_id] = sync_item(item_id)
    return results
