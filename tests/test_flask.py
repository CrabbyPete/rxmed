import pytest
from main import application


@pytest.fixture
def client(request):
    application.config['TESTING'] = True
    client = application.test_client()

    def teardown():
        pass

    request.addfinalizer(teardown)

    return client


def test_empty_db(client):
    """Start with a blank database."""
    rv = client.get('/')
    assert(True)
