from .base import Database, log

try:
    db = Database('postgresql+psycopg2://douma:thefatd0g@rxmed.cfbsndnshc5a.us-east-1.rds.amazonaws.com:5432/rdmed')
    db.open()
except Exception as e:
    log.error("Database failed to open:{}".format(str(e)))

