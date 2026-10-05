from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def hash(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hash: str) -> bool:
    return password_hash.verify(password, hash)
