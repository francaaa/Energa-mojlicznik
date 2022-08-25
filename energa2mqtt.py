# -------------------------------------------------------------------------------
# Name:        Energa - Mój licznik - scrapping integration
# Purpose:     Integration with mqtt/home assistant
#
# Author:      arabiczko@gmail.com
#
# Created:     30/06/2022
# Copyright:   (c) arabiczko@gmail.com 2022
# Licence:     GPL
# -------------------------------------------------------------------------------

import json
import logging
import sys

import paho.mqtt.client as mqtt
import requests
from bs4 import BeautifulSoup, NavigableString
from datetime import datetime
from time import sleep

from config import *

def get_meter_readings_file():
    with open("index.html", "r") as f:
        html = str(f.readlines())


def get_meter_readings(html):
    soup = BeautifulSoup(html, "lxml")

    a_plus_minus = soup.find_all("td", class_="first")
    a_plus_minus_values = soup.find_all("td", class_="last")

    a_headers = []
    a_values = []
    out = {}

    for a in a_plus_minus:
        cols = [element.text.strip() for element in a]
        a_headers.append([element for element in cols if element])

    # we should have at least one reading from A+ zone (import), two (A+ and A- for export) and maybe more if we heave two tariff --> examples needed.
    if len(a_headers) > 0:
        now = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        for x in range(0, len(a_headers)):
            #fix last_update entry - lack of seconds on the page
            last_update = str(datetime.strptime(a_headers[x][1], "%Y-%m-%d %H:%M"))
            if x == 0:
                out["a_plus"] = {
                    "name": a_headers[x][0],
                    "description": "Energia konsumpcja",
                    #"last_update": a_headers[x][1],
                    "last_update": last_update,
                    "last_refresh": "",
                    "value": -1,
                    "unit": "kWh",
                }
                out["a_plus"]["last_refresh"] = now
            if x == 1:
                out["a_minus"] = {
                    "name": a_headers[x][0],
                    "description": "Energia produkcja",
                    "last_update": last_update,
                    "last_refresh": "",
                    "value": -1,
                    "unit": "kWh",
                }
                out["a_minus"]["last_refresh"] = now
            if x >= 2:
                logging.info(
                    "More than two zones (A+, A-) or two tariffs. This state is not implemented yet. Contact author to obtain updated version."
                )
                break

    for a in a_plus_minus_values:
        cols = [element.text.strip() for element in a]
        a_values.append([element for element in cols if element])

    allowed = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ",", "."]
    valueout = []

    if len(a_values) > 0:
        for x in range(0, len(a_values)):
            for element in a_values[x]:
                if element in allowed:
                    valueout.append(element)

            value = ("".join(valueout)).replace(",", ".")
            value_float = float(value)
            if x == 0:
                out["a_plus"]["value"] = value_float
                logging.info("parsed a_plus value: {}".format(value_float))
            if x == 1:
                out["a_minus"]["value"] = value_float
                logging.info("parsed a_minus value: {}".format(value_float))
            if x > 2:
                logging.info(
                    "More than two zones (A+, A-) or two tariffs. This state is not implemented yet. Contact author to obtain updated version."
                )
                break
            valueout.clear()
    return out


def get_meter_page(account):
    s = requests.Session()
    r = s.get(login_url, headers=headers)

    soup = BeautifulSoup(r.text, "lxml")
    form = soup.find("form", id="loginForm")
    antixsrf = form.find("input", {"name": "_antixsrf"})["value"]
    payload["_antixsrf"] = antixsrf
    payload["j_username"] = account['username']
    payload["j_password"] = account['password']
    
    logging.info("Gathering data for '{}' account".format(account['name']))

    r = s.post(login_url, data=payload, headers=headers)
    if (r.status_code) == 200:
        logging.info("login (code: {})".format(r.status_code))
        r = s.get(data_url)
        if r.status_code == 200:
            logging.info("downloaded meter data (code: {})".format(r.status_code))
            page_out = r.text
            # logout
            r = s.get(logout_url, headers=headers)
            logging.info("logout (code: {})".format(r.status_code))
            return page_out
    else:
        logging.error("Unable to login, http error: {}".format(r.status_code))

def mqtt_setup():
    
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logging.info("Connected to mqtt broker at {}".format(mqtt_config["mqtt_broker"]))
        else:
            logging.info("Failed to connecto to mqtt broker (error: {})".format(rc))
    
    mqtt_client = mqtt.Client(mqtt_config["mqtt_clientid"])
    if mqtt_config["mqtt_username"] != None:
        mqtt_client.username_pw_set(mqtt_config["mqtt_username"], mqtt_config["mqtt_password"])

    try:
        if mqtt_config["mqtt_broker"] != None:
            mqtt_client.on_connect = on_connect
            mqtt_client.on_publish = mqtt_on_publish
            mqtt_client.on_disconnect = mqtt_on_disconnect
            mqtt_client.connect(mqtt_config["mqtt_broker"], port=mqtt_config["mqtt_broker_port"])
            return mqtt_client

    except:
        logging.error("Fatal error ", exc_info=True)

def mqtt_on_publish(client, userdata, result):
    logging.info('Data published to mqtt.')
    

def mqtt_on_disconnect(client, userdata, rc):
    logging.info("mqtt client disconnected ok")
    client.disconnect()

def mqtt_on_message(client, userdata, message):
    logging.info("message received {}s".format(message.payload.decode("utf-8")))
    logging.info("message topic={} qos={} retain flag={}".format(message.topic, message.qos,message.retain))

def mqtt_send_to_broker(client, account, readings):
  
    if mqtt_config["mqtt_retain_flag"]:
        for i, (key, value) in enumerate(readings.items()):
            readings[key]["retain"] = mqtt_config["mqtt_retain_flag"]
    
    for i, (key, value) in enumerate(readings.items()):
        client.publish(mqtt_config["mqtt_topic_name"].format(account["name"], key), json.dumps(readings[key]))
        sleep(1)

def main():
    try:
        logger = logging.getLogger("")
        logger.setLevel(logging.INFO)
        if verbose:
            formatter = logging.Formatter(
                "[%(asctime)s] %(levelname)s [%(filename)s.%(funcName)s:%(lineno)d] %(message)s",
                datefmt=log_date_format,
            )
        else:
            formatter = logging.Formatter(
                "[%(asctime)s] %(levelname)s %(message)s",
                datefmt=log_date_format,
            )
        if log:
            fh = logging.FileHandler(log)
            logger.addHandler(fh)
            fh.setFormatter(formatter)

        if log_to_screen:
            sh = logging.StreamHandler(sys.stdout)
            sh.setFormatter(formatter)
            logger.addHandler(sh)

        try:
            for x in range(0, len(account)):
                if account[x]['active']:
                    out = get_meter_page(account[x])
                    if out:
                        readings = get_meter_readings(out)
                        if readings:
                            mqtt_client = mqtt_setup()
                            if mqtt_client:
                                mqtt_send_to_broker(mqtt_client, account[x], readings)    
                        else:
                            logging.info("No meter readings recevied from Energa server.")
                else:
                    logging.info("Account '{}' is not active, skipping.".format(account[x]["name"]))
        except:
            logging.error("Error connecting to MQTT. Check username/password for mqtt server.", exc_info=True)
        
    except Exception:
        logging.error("Fatal error ", exc_info=True)

if __name__ == "__main__":
    main()
