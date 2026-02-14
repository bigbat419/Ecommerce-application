import os
import tempfile
import pytest
from app import app as flask_app
from config import Config

@pytest.fixture
def client(monkeypatch):
    # configure app for testing: small sqlite in-memory or temp file
    monkeypatch.setenv('MYSQL_HOST','')
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        yield c

def test_home(client):
    rv = client.get('/')
    assert rv.status_code in (200,302)  # depending on setup, should return something
