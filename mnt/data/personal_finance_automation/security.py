import keyring

SERVICE = "personal-finance-plaid"


def save_access_token(item_id: str, access_token: str):
    keyring.set_password(SERVICE, item_id, access_token)


def get_access_token(item_id: str) -> str | None:
    return keyring.get_password(SERVICE, item_id)


def delete_access_token(item_id: str):
    try:
        keyring.delete_password(SERVICE, item_id)
    except keyring.errors.PasswordDeleteError:
        pass
