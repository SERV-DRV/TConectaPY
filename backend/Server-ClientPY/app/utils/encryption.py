try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError

    _ph = PasswordHasher()

    def hash_password(password: str) -> str:
        return _ph.hash(password)

    def verify_password(hash: str, password: str) -> bool:
        try:
            return _ph.verify(hash, password)
        except VerifyMismatchError:
            return False

except ImportError:
    def hash_password(password: str) -> str:
        raise NotImplementedError("argon2-cffi no está instalado")

    def verify_password(hash: str, password: str) -> bool:
        raise NotImplementedError("argon2-cffi no está instalado")
