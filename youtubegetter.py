#!/usr/bin/python3
import random
import logging
import requests

class YoutubeGetter(object):
    def __init__(self, apikey):
        self.apikey = apikey
        self.labels = ["UCoxg3Kml41wE3IPq-PC-LQw", "UCKdA5J4-opjla1aWOjF74mg", "UCSldglor1t-5E-Gy2eBdMrA", "UCG7AaCh_CiG6pq_rRDNw72A"]

    def getSuggestions(self):
        l = random.randint(0, len(self.labels) - 1)
        label = self.labels[l]
        logging.info("decided for label: %i" % l)
        try:
            result = requests.get('https://www.googleapis.com/youtube/v3/search', {'key': self.apikey, 'part': 'snippet', 'channelId': label, 'maxResults': 50}).json()
            if result:
                vids = result['items']
                return vids
        except:
            logging.exception("Shit happens...")


    def selectVideo(self, vids):
        selection = random.choice(vids)
        videoid = selection['id']['videoId']
        return videoid

    def randomVideo(self):
        selection = self.selectVideo(self.getSuggestions())
        return "http://youtu.be/%s" % selection


