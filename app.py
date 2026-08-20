import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

load_dotenv()

from database import init_db, connect
from plaid_flow import create_link_token, exchange_public_token
from sync import sync_all
from excel_sync import sync_workbook

BASE = Path(__file__).resolve().parent
app = Flask(__name__, static_folder=str(BASE / 'static'))
init_db()


@app.get('/')
def index():
    return send_from_directory(BASE, 'index.html')


@app.post('/api/create_link_token')
def api_create_link_token():
    return jsonify({'link_token': create_link_token()})


@app.post('/api/exchange_public_token')
def api_exchange_public_token():
    public_token = request.json.get('public_token')
    if not public_token:
        return jsonify({'error':'public_token required'}),400
    item_id = exchange_public_token(public_token)
    return jsonify({'item_id': item_id})


@app.post('/api/sync')
def api_sync():
    result = sync_all()
    excel = sync_workbook()
    return jsonify({'result': result, 'excel': excel})


@app.get('/api/status')
def api_status():
    with connect() as con:
        items = con.execute('SELECT item_id,institution_name,cursor,updated_at FROM plaid_items').fetchall()
        tx_count = con.execute('SELECT COUNT(*) FROM transactions').fetchone()[0]
        review_count = con.execute("SELECT COUNT(*) FROM transactions WHERE category='Uncategorized'").fetchone()[0]
    return jsonify({'items':[dict(x) for x in items], 'transaction_count':tx_count, 'review_count':review_count})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.getenv('PORT','8000')), debug=False)
