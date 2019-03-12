import pytest
import testing.postgresql

from models.base import Database

DATABASE = testing.postgresql.Postgresql().url()

def test_models():
    with Database(DATABASE) as db:
        pass

'''
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
'''