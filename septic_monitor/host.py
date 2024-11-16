import shutil
import time

from septic_monitor import storage

while True:
    total, used, free = shutil.disk_usage(".")
    storage.set_disk_usage(used/total*100)
    time.sleep(60)
