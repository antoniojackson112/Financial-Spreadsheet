import os
from datetime import datetime, timezone

from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest

from database import connect
from security import save_access_token
from plaid_client import client


def create_link_token():
    products = [Products(p.strip()) for p in os.getenv("PLAID_PRODUCTS", "transactions").split(",") if p.strip()]
    countries = [CountryCode(c.strip()) for c in os.getenv("PLAID_COUNTRY_CODES", "US").split(",") if c.strip()]
    request = LinkTokenCreateRequest(
        client_name="Personal Financial Model",
        language="en",
        country_codes=countries,
        products=products,
        user=LinkTokenCreateRequestUser(
            client_user_id=os.getenv("PLAID_CLIENT_USER_ID", "personal-finance-local-user")
        ),
    )
    response = client().link_token_create(request)
    return response["link_token"]


def exchange_public_token(public_token: str):
    response = client().item_public_token_exchange(
        ItemPublicTokenExchangeRequest(public_token=public_token)
    )
    item_id = response["item_id"]
    access_token = response["access_token"]
    save_access_token(item_id, access_token)
    now = datetime.now(timezone.utc).isoformat()
    with connect() as con:
        con.execute("""
            INSERT INTO plaid_items(item_id, institution_name, cursor, created_at, updated_at)
            VALUES (?, ?, NULL, ?, ?)
            ON CONFLICT(item_id) DO UPDATE SET updated_at=excluded.updated_at
        """, (item_id, None, now, now))
    return item_id
