from pathlib import Path
from datetime import datetime
import requests
import json
import logging


# class Weather():
#     def __init__(self, logger=None):
# 
# 
#     def is_safe(self, age_limit=300):
#         return safe
# 
# 
#     def has_been_safe(self, entered_state_at):
#         return ok


class DavisWeatherLinkLive():
    def __init__(self, logger=None, IP=None):
        self.logger = logger
        self.IP = IP
        self.name = 'WeatherLinkLive'
        self.url = f'http://{self.IP}/v1/current_conditions'


    def log(self, msg, level=logging.DEBUG):
        if self.logger: self.logger.log(level, f"{self.name:>15s}: {msg}")


    def get_data(self):
        r = requests.get(self.url)
        result = json.loads(r.text)
        data = result.get('data', None)
        error = result.get('error', None)
        if error is not None:
            raise Exception(result)
        data['timestamp'] = datetime.fromtimestamp(data['ts'])
        return data



from socket import *
import struct
import time
import requests
import json


def main():
        URL = 'http://192.168.4.76:80/v1/real_time?duration=20'
        UDP_PORT = 22222
        comsocket = socket(AF_INET, SOCK_DGRAM)
        comsocket.bind(('',22222))
        comsocket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        resp = requests.get(URL)
        while 1:
            print("HTTP Response Code:", resp)
            data, wherefrom = comsocket.recvfrom(2048)
            json_data = json.loads(data.decode("utf-8"))        
            if json_data["conditions"] == None:
                print (json_data["error"])
            else:
#                 print (json_data)
                print(json_data['ts'], json_data['conditions'][0].get('rx_state', None))
        
        comsocket.close()

if __name__ == "__main__":
    main()       
