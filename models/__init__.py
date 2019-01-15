from .base import Database
from sqlalchemy import Text, Integer

try:
    ndb = Database('postgresql+psycopg2://douma:thefatd0g@rxmed.cfbsndnshc5a.us-east-1.rds.amazonaws.com:5432/rdmed')
    db.open()
except Exception as e:
    print( "Database ailed to open:{}".format(str(e)))
pass
