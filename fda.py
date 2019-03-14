import time
import schedule

from api    import FDA
from models import OpenNDC, FTA

def job():
    fda = FDA()
    fda.open_fda()

"""
schedule.every().day.at("20:00").do(job)


while True:
    schedule.run_pending()
    time.sleep(1)
"""

