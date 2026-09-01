from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError


_PASSWORD_HASH = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """
    使用 Argon2id 对明文密码进行哈希。

    :param password: 用户提交的明文密码。
    :return: 可安全持久化的 Argon2id 密码哈希。
    """
    return _PASSWORD_HASH.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """
    验证明文密码是否匹配已保存的密码哈希。

    :param password: 用户提交的明文密码。
    :param password_hash: 数据库中保存的密码哈希。
    :return: 密码匹配时返回 True，否则返回 False。
    """
    try:
        return _PASSWORD_HASH.verify(password, password_hash)
    except UnknownHashError:
        return False
