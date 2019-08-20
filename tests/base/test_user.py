import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.app.config['TESTING'] = True

    with app.app.test_client() as client:
        yield client


def test_empty(client):
    response = client.get('/')
    assert response.status_code == 200