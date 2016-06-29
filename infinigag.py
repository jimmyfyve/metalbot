#!/usr/bin/python
import requests
import random
import logging

def randomgag():
    try:
        result = requests.get('http://infinigag.k3min.eu/hot').json()
        if result:
            gags = result['data']
            selection = random.choice(gags)
            link = selection['link']
            return link
    except:
        logging.exception("fetching gag failed")


