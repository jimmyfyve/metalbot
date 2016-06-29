#!/usr/bin/python3

import requests
import sys
import logging
import re
import random
import youtubegetter
import config
import datetime
import parsedatetime
import time
import uuid
import subprocess
import os

from apscheduler.schedulers.background import BackgroundScheduler

class command(object):
    def __init__(self, regex, action):
        self.r = re.compile(regex)
        self.action = action

    def check(self, text):
        m = re.search(self.r, text)
        if m:
            return m.groups()

class MetalBot(object):
    def __init__(self):
        self.baseurl = "https://api.telegram.org/bot%s/" % config.telegram_token
        self.update_id = 0

        self.commands = [command("/dice ([0-9]*)", self.cmd_dice),
                command("/metal", self.cmd_metal),
                command("/8ball (.*)", self.cmd_8ball),
                command("/insult (.*)", self.cmd_insult),
                command("/randomimage", self.cmd_randomimage),
                command("/wake (.*?) (.*)", self.cmd_wake),
                command("/read (.*)", self.cmd_read),
                command("/what (.*)", self.cmd_what)

                ]

        self.youtube = youtubegetter.YoutubeGetter(config.youtube_key)
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

        self.alarms = []

    def api_request(self, method, data=None, files=None):
        """
        Makes a request to the Telegram API using the method 'method' and sending data 'data', which must be a key-value dictionary.
        """
        logging.debug("starting api request %s" % method)
        tries = 0
        while tries < config.max_tries:
            try:
                logging.debug("trying...")
                response = requests.post(self.baseurl + method, data, files=files, timeout=config.timeout).json()
                if response['ok'] == True:
                    logging.debug("API request ok")
                    return response['result']
                else:
                    logging.error("API request failed, dunno why?")
            except (requests.ConnectionError, requests.ReadTimeout) as e:
                #logging.exception("Something is wrong with your connection, trying again in %d s" % config.retry_interval)
                logging.error("Something is wrong with your connection, trying again in %d s" % config.retry_interval)
                time.sleep(config.retry_interval)
            #except Exception as e:
            #    logging.exception("API request failed")
            tries += 1

    def check_connection(self):
        """
        Checks the connection to the server and the bot token. Retrieves additional bot details.
        """

        me = self.api_request("getMe")
        if me:
            self.username, self.id, self.first_name = me['username'], me['id'], me['first_name']
        else:
            logging.error("something failed, I'm dying\n")
            exit()
        logging.info("connection ok!")
        logging.info("username: %s" % self.username)
        logging.info("id: %s" % self.id)
        logging.info("first name: %s" % self.first_name)

    def get_updates(self):
        """
        Fetches unconfirmed updates from the server. When this method is called, all updates fetched previously (up to self.update_id) will be confirmed.
        """

        logging.debug("getting updates")
        self.updates = self.api_request('getUpdates', {'offset' : self.update_id})
        if self.updates:
            self.update_id = self.updates[-1]['update_id'] + 1
            logging.info("received %i updates" % len(self.updates))
            return self.updates

    def send_voice(self, voicefile, chat_id):
        resp = self.api_request("sendVoice", {'chat_id': chat_id}, files={'voice' : open(voicefile, 'rb')})
        if resp:
            return True
        else:
            return False

    def send_text(self, text, chat_id):
        resp = self.api_request("sendMessage", {'chat_id' : chat_id, 'text' : text})
        if resp:
            return True
        else:
            return False

    def respond(self, text):
        if self.message:
            return self.send_text(text, self.message['chat']['id'])

    def handle_message(self, message):
        self.message = message
        if message['chat']['type'] == 'private':
            self.handle_message_private()
        elif message['chat']['type'] == 'group':
            self.handle_message_group()

    def handle_message_private(self):
        self.handle_message_generic()

    def handle_message_group(self):
        self.handle_message_generic()

    def handle_message_generic(self):
        try:
            text = self.message['text']
            self.parse_command(text)
        except:
            pass

    def parse_command(self, text):
        logging.debug("parsing for commands")
        for cmd in self.commands:
            params = cmd.check(text)
            if not params == None:
                try:
                    cmd.action(params)
                except:
                    logging.exception("something went wrong")
                break


    # actual commands

    def cmd_dice(self, params):
        logging.info("dice rolling...")
        try:
            limit = int(params[0])
            rannum = random.randint(1,limit)
            self.respond("%s rolled: %i" % (self.message['from']['first_name'], rannum))
        except Exception as e:
            logging.exception("something failed :(")
            self.respond("Don't screw me over, %s! \U0001f620" % (self.message['from']['first_name']))

    def cmd_metal(self, params):
        logging.info("metal!")
        link = self.youtube.randomVideo()
        self.respond(link)

    def cmd_8ball(self, params):
        logging.info("8ball")
        ballz = ["yes", "no", "reply hazy,try again", "outlook not so good", "as i see it,yes", "repeat the question", "not in a million years", "it is certain", "it is decidedly so", "my sources say no", "better not tell you now", "signs point to yes", "count on it", "meh"]
        if(len(params[0]) < 10):
            self.respond("whaddya say?")
        else:
            self.respond(random.choice(ballz))

    def cmd_insult(self, params):
        logging.info("insult")
        insults = ["%s, you ugly, venomous toad!", "%s, you infectious pestilence!", "%s, you lunatic, lean-witted fool!", "%s, you impudent, tattered prodigal!", "%s, you old, withered crab tree!", "I bet your brain feels as good as new, %s, seeing that you never use it.", "I wasn't born with enough middle fingers to let you know how I feel about %s", "%s must have been born on a highway because that's where most accidents happen", "%s has two brain cells, one is lost and the other is out looking for it.", "%s, you are so fat the only letters of the alphabet you know are KFC", "% is as bright as a black hole, and twice as dense.", "I fart to make %s smell better", "Learn from %s's parents' mistakes - use birth control!", "Some drink from the fountain of knowledge; %s only gargled.", "%s, you are so stupid, you'd trip over a cordless phone.", "Ordinarily people live and learn. %s just lives.", "%s is as useless as ejection seats on a helicopter.", "%s is as useless as a one-legged man at an arse kicking contest"]
        name = params[0]
        a = False
        if name.lower() == self.first_name.lower() or name.lower == "me" or name.lower == "myself":
            name = self.message['from']['first_name']
            a = True
        self.respond(random.choice(insults) % name)

    def cmd_randomimage(self, params):
        logging.info("randomimage")
        self.respond("randomimage")

    def cmd_wake(self, params):
        logging.info("wake")
        if params[0] == "me":
            userid = self.message['from']['id']
        else:
            self.respond("Who is %s?" % params[0])
            return

        time_struct, parse_status = parsedatetime.Calendar().parse(params[1])
        if parse_status > 0:
            datet = datetime.datetime(*time_struct[:6])
            logging.info("%s parsed as %s", params[1], datet)
            self.alarms.append(self.scheduler.add_job(self.jb_wake, 'date', (self.message['from'], self.message['chat']), run_date=datet))
            self.respond(random.choice(["Alright, dickface.", "Sleep well my dear.", "Will do.", "You can count on me!"]))
        else:
            logging.info("could not parse %s", params[1])
            self.respond(random.choice(["You're talking rubbish.", "I don't get it", "Can't hear you", "Whatever", "I don't understand"]))

    def cmd_read(self, params):
        try:
            filename = "metalbot%s" % str(uuid.uuid4())
            p = subprocess.Popen(['text2wave', '-o', '/tmp/%s.wav' % filename], stdin=subprocess.PIPE)
            p.communicate(input=bytes(params[0], 'utf-8'))
            subprocess.run(['opusenc', '/tmp/%s.wav' % filename, '/tmp/%s.opus' % filename])
            self.send_voice('/tmp/%s.opus' % filename, self.message['chat']['id'])
            os.remove('/tmp/%s.opus' % filename)
            os.remove('/tmp/%s.wav' % filename)
        except:
            logging.exception("could not create voice message")
            self.respond("I got a hangover")

    def cmd_what(self, params):
        if "are you" in params[0]:
            self.respond(random.choice(["My name is Bot. MetalBot.", "I'm your worst nightmare", "They call me the destroyer.", "Who wants to know?", "The bot that rules them all."]))
        elif "the fuck" in params[0]:
            self.respond("Watch your language!")


    def jb_wake(self, sender, chat):
        self.send_text("Wake up %s, you lazy piece of shit!" % sender['first_name'], chat['id'])











if __name__ == '__main__':
    logging.basicConfig(filename="metalbot.log", format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.ERROR)
    requests_log.propagate = True
    logging.info("----==== \m/ Hello Metalworld! \m/ ====----")
    random.seed()

    if not config.telegram_token:
        logging.error("Telegram token missing!")
        exit()

    if not config.youtube_key:
        logging.error("YouTube key missing!")
        exit()

    m = MetalBot()

    m.check_connection()

    while True:
        m.get_updates()
        if m.updates:
            for u in m.updates:
                m.handle_message(u['message'])
