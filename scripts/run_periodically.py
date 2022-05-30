import schedule, time
from upload_tournament import run

schedule.every().hour.do(run)

schedule.run_all()

while True:
    schedule.run_pending()
    time.sleep(1)