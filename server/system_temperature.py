import sys
import thread
import time
import traceback


class SystemTemperature:
    temp = 0
    interval = 5

    def read_temp(self):
        file = open('/sys/class/thermal/thermal_zone0/temp', 'r')
        self.temp = file.readline()
        file.close()

    def my_thread(self):
        while 1:
            self.read_temp()
            time.sleep(self.interval)

    def get_temp_raw(self):
        return self.temp

    def get_temp(self):
        return int(self.temp) / 1000

    def __init__(self):
        try:
            thread.start_new_thread(self.my_thread, ())
        except:
            print "Error: unable to start thread"
            print '-'*60
            traceback.print_exc(file=sys.stdout)
            print '-'*60
