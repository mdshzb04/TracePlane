from app.core.oauth_state import create_oauth_state, verify_oauth_state


def test_oauth_state_round_trip():
    state = create_oauth_state()
    assert verify_oauth_state(state)


def test_oauth_state_rejects_tampering():
    state = create_oauth_state()
    tampered = state[:-4] + "xxxx"
    assert not verify_oauth_state(tampered)


def test_oauth_state_rejects_empty():
    assert not verify_oauth_state("")
