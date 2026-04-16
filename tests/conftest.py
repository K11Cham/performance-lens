import pytest


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv('PERFORMANCELENS_DB_PATH', str(tmp_path / 'test-performance.db'))
    monkeypatch.setenv('PERFORMANCELENS_SECRET_KEY', 'pytest-secret-key-not-for-production')
    from app import create_app

    return create_app()


@pytest.fixture
def client(app):
    return app.test_client()
