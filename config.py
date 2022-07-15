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

import random


login_url = "https://mojlicznik.energa-operator.pl/dp/UserLogin.do"
logout_url = "https://mojlicznik.energa-operator.pl/dp/MainLogout.go"
data_url = "https://mojlicznik.energa-operator.pl/dp/UserData.do"

verbose = False
log = "energa2mqtt.log"
log_to_screen = False

log_date_format = "%Y-%m-%d %H:%M:%S"

account = [
    {
        "name": "my home account",
        "active": False,
        "username": "email@server.com",
        "password": "changeme",
    },
    {
        "name": "parents account",
        "active": False,
        "username": "father@family.org",
        "password": "ILoveMyKids"
    }
]

mqtt_config = {
    "mqtt_broker": "mqtt.broker.address.local",
    "mqtt_broker_port": 1883,
    "mqtt_username": None,
    "mqtt_password": None,
    "mqtt_topic_name": "home/mojlicznik/{}/{}",
    "mqtt_topic": [
        ("name", "{}"),
        ("description", "{}"),
        ("last_update", "{}"),
        ("last_refresh", "{}"),
        ("value", "{}"),
        ("unit", "{}")
    ],
    "mqtt_clientid": f'mqtt-francaaa-{random.randint(0, 100)}',
    "mqtt_retain_flag": True
}

payload = {
    "j_username": "",
    "j_password": "",
    "selectedForm": "1",
    "save": "save",
    "clientOS": "web",
    "loginNow": "zaloguj+się",
    "_antixsrf": "invalid",
}


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0"
}
