from .base import Database
from sqlalchemy import Text, Integer

try:
    db = Database('postgresql+psycopg2://douma:thefatd0g@rxmed.cfbsndnshc5a.us-east-1.rds.amazonaws.com:5432/rdmed')
    db.open()
except:
    print("Error opening database")

pass
