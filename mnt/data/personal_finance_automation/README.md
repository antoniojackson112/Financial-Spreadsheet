# Personal Financial Model V2 — Bank Automation

## Architecture
Bank → Plaid Link/API → Python → SQLite → Categorization → V2 Excel workbook.

## Current behavior
- Plaid Link creates a connection and exchanges a public token for an access token.
- Access tokens are stored in the OS credential store via `keyring`, not in Excel.
- Transactions use Plaid `/transactions/sync` with a stored cursor for incremental updates.
- Account balances are refreshed.
- Merchant rules are stored in SQLite and exported to the V2 workbook.
- Transactions are written to the workbook's `Raw Import` and `Transactions` tabs.
- Uncategorized transactions are marked for review.

## Setup
1. Copy `.env.example` to `.env`.
2. Put your Plaid client ID and secret in `.env`.
3. Install packages: `python -m pip install -r requirements.txt`.
4. Put `Personal_Financial_Model_V2.xlsx` in this folder (or change `EXCEL_PATH`).
5. Run `python -c "from database import init_db; init_db()"`.
6. Run `python -c "exec(open('load_rules.py').read())"` after creating your rules (optional; edit Category Rules in Excel or add SQLite rules).
7. Start the local app: `python app.py`.
8. Open `http://127.0.0.1:8000`.
9. Click Connect Bank and complete Plaid Link.
10. Click Sync Now whenever you want a new sync.

## CSV fallback
Use `import_csv.py` with a CSV containing:
`transaction_id,account_id,date,amount,merchant,description,currency,pending,source`

Example:
`python import_csv.py bank_export.csv`

## Security
- Never commit `.env`.
- Never put bank passwords, MFA codes, Plaid access tokens, SSNs, or full account numbers in Excel.
- For production hosting, move secrets from `.env`/local keychain into a proper secret manager.
- Keep the local Flask server bound to 127.0.0.1 unless you intentionally deploy it behind HTTPS/authentication.
