import os
import pytest
import testing.postgresql

from tests.fixtures import load_fixtures
from models         import *

CURRENT_PATH = os.path.join( os.path.dirname(__file__), 'fixtures' )

@pytest.fixture()
def db_setup():
    """ Setup any state tied to the execution of the given function.
        Invoked for every test function in the module.
    """
    PG = testing.postgresql.Postgresql()
    yield PG
    PG.stop()


def test_models(db_setup):
    with Database(db_setup.url()) as DB:
        load_fixtures(CURRENT_PATH, ['caresource.json'])
        records = Caresource.get_all()
        assert not records is None
        one = Caresource.get(1)
        assert one
        by_name = Caresource.find_by_name('allopurinol')
        assert by_name
        by_rxcui = Caresource.find_by_rxcui(519)
        assert by_rxcui

