import os
import plaid
from plaid.api import plaid_api


def client():
    env = os.getenv("PLAID_ENV", "sandbox").lower()
    host = plaid.Environment.Production if env == "production" else plaid.Environment.Sandbox
    configuration = plaid.Configuration(
        host=host,
        api_key={
            "clientId": os.environ["PLAID_CLIENT_ID"],
            "secret": os.environ["PLAID_SECRET"],
        },
    )
    return plaid_api.PlaidApi(plaid.ApiClient(configuration))
