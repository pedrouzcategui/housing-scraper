import importlib


def test_signup_login_and_protected_users(tmp_path, monkeypatch):
    db_path = tmp_path / "test_auth.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")

    import db.session as db_session

    # Ensure the engine is rebuilt for this test database.
    db_session._engine = None
    db_session._engine_url = None

    import backend.main as backend_main

    importlib.reload(backend_main)

    from fastapi.testclient import TestClient

    with TestClient(backend_main.app) as client:
        signup = client.post(
            "/auth/signup",
            json={"name": "Pedro", "email": "pedro@example.com", "password": "pw123"},
        )
        assert signup.status_code == 201
        assert "password" not in signup.json()

        login = client.post(
            "/auth/login",
            json={"email": "pedro@example.com", "password": "pw123"},
        )
        assert login.status_code == 200
        token = login.json()["access_token"]

        unauthorized = client.get("/users")
        assert unauthorized.status_code == 401

        authorized = client.get(
            "/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert authorized.status_code == 200
        assert len(authorized.json()) == 1
