from app.core.passwords import hash_password, verify_password


def test_password_is_hashed_with_argon2id_and_can_be_verified() -> None:
    """
    验证密码以 Argon2id 哈希保存并可正确校验。

    :return: 无返回值。
    """
    password = "Correct-Horse-Battery-Staple-2026"
    password_hash = hash_password(password)

    assert password_hash != password
    assert password_hash.startswith("$argon2id$")
    assert verify_password(password, password_hash) is True
    assert verify_password("wrong-password", password_hash) is False


def test_unknown_password_hash_is_rejected() -> None:
    """
    验证历史占位哈希和无效哈希只会导致登录失败。

    :return: 无返回值。
    """
    assert verify_password("any-password", "!") is False
