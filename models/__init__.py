from .base import Database
from sqlalchemy import Text, Integer


#db = Database('postgresql+psycopg2://petedouma:drd00m@127.0.0.1:5432/rxmed')
db = Database('postgresql+psycopg2://douma:thefatd0g@rxmed.cfbsndnshc5a.us-east-1.rds.amazonaws.com:5432/rdmed')
db.open()

pass
