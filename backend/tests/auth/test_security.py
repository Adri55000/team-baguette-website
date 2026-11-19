from app.modules.auth.security import (
    generate_session_token,
    hash_session_token,
)


def test_session_tokens_are_unique():
    token1 = generate_session_token()
    token2 = generate_session_token()

    assert token1 != token2


def test_session_token_hash_has_expected_length():
    token = generate_session_token()
    token_hash = hash_session_token(token)

    assert len(token_hash) == 64


def test_session_token_hash_is_deterministic():
    token = generate_session_token()

    assert hash_session_token(token) == hash_session_token(token)


def test_different_tokens_have_different_hashes():
    token1 = generate_session_token()
    token2 = generate_session_token()

    assert hash_session_token(token1) != hash_session_token(token2)
