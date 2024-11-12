import re


def validate_token_id(token_id: str):
    if len(token_id) != 64 or not re.match(r"^[a-fA-F0-9]{64}$", token_id):
        raise ValueError("Invalid token_id format")


def validate_str_params(product_name: str):
    if len(product_name) > 100:
        raise ValueError("Product name too long")
    if not re.match(r"^[\w\s\-\_\d]+$", product_name):
        raise ValueError("Invalid product_name format")
