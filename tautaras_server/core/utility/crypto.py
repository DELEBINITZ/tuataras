import hashlib

def get_hash(input: str) -> str:
    sha256_hash_gen = hashlib.sha256()
    sha256_hash_gen.update(input.encode("utf-8"))
    return sha256_hash_gen.hexdigest()
