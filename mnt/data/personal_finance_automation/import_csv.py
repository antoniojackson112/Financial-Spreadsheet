import csv
import sys
from datetime import datetime, timezone

from database import connect
from categorizer import categorize


def import_csv(path):
    added = 0
    with open(path, newline='', encoding='utf-8-sig') as f, connect() as con:
        reader = csv.DictReader(f)
        required = {'transaction_id','account_id','date','amount'}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError(f"CSV must include: {sorted(required)}")
        now = datetime.now(timezone.utc).isoformat()
        for row in reader:
            txid = row['transaction_id'].strip()
            amount = float(row['amount'])
            merchant = row.get('merchant','').strip() or None
            description = row.get('description','').strip() or merchant or ''
            cat = categorize(merchant, description, amount)
            con.execute('''
                INSERT INTO transactions(transaction_id,account_id,date,merchant,description,amount,currency,transaction_type,category,subcategory,recurring,pending,source,fingerprint,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(transaction_id) DO UPDATE SET
                    merchant=excluded.merchant,description=excluded.description,amount=excluded.amount,
                    category=excluded.category,subcategory=excluded.subcategory,
                    transaction_type=excluded.transaction_type,recurring=excluded.recurring,
                    pending=excluded.pending,updated_at=excluded.updated_at
            ''', (txid,row['account_id'],row['date'],merchant,description,amount,row.get('currency','USD'),cat['transaction_type'],cat['category'],cat['subcategory'],cat['recurring'],int(row.get('pending','false').lower()=='true'),row.get('source','CSV'),txid,now,now))
            added += 1
    return added

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python import_csv.py path/to/file.csv')
    print(f'Imported {import_csv(sys.argv[1])} rows')
