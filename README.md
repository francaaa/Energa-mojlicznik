# Energa "Mój licznik"

### Yet another "scrapping" integration for Energa meters.

This piece of software can be used to gather energy production and consumption published on https://mojlicznik.energa-operator.pl and send it to mqtt broker. From that point meter readings can be easy picked up by Home Assistant or similar software which is mqtt capable. As this is "local" application the rest od the documentation will be provided in polish. 


### Kolejna integracja typu "scrapping" dla strony "Mój licznik" dostawcy Energa. Oczywiście wszystko jest zależne od struktury strony, więc jeśli Energa zmieni coś na stronie koniecznie będą zmiany w kodzie.


Program odczytuje wartości energii ze strony https://mojlicznik.energa-operator.pl i publikuje je do brokera mqtt.

- Może zostać uruchomiona "z ręki", z crona (patrz niżej) albo jako usługa systemd (patrz niżej), pewnie także na Windowsie - tego akurat nie sprawdzałem.

- Napisana w Python 3.9.2 - niewykluczone, że będzie działać w starszych/nowszych wersjach.

- Do działania potrzebuje bibliotek/modułów (instalacja przez pip/apt), testowane na Debian GNU/Linux 11:
  - paho-mqtt 1.6.1
  - requests 2.28.1
  - bs4 (beautifulsoup4 4.11.1)
  - czasami tez program wymaga lxml 4.9.1

## Ficzery

- Przesyła odczytane wartości do brokera mqtt    
- Obsługuje wiele kont (np Twoje, rodziców, albo szwagra), produkcje energii (A-) oraz zużycie (A+)
- Być może obsługuje tylko A+
- Na pewno nie obsługuje wiecej niż jednej taryfy, lub wiecej niż jednego licznika (nie miałem jak tego sprawdzić --> potrzebne dodatkowe dane --> napisz)
- Prawdopodobnie zawiera błędy

## Znane błędy

- na razie wszystkie błędy są niezname, program działa u mnie już jakiś czas bez wiekszych problemow, no ale wiadomo, że u autora zawsze działa dobrze. :)

## Konfiguracja


- Wyedytuj config.py i wpisz swoje dane do konta ze strony moj licznik (account). Ustaw active na True jeśli chesz żeby to konto było sprawdzane.

    ```
    account = [
        {
            "name": "my home account",
            "active": True,
            "username": "user@email.com",
            "password": "changeme",
        }
    ```

- Wpisz namiary brokera mqtt
    ```
    mqtt_config = {
    "mqtt_broker": "mqtt.broker.local",
    "mqtt_broker_port": 1883,
    "mqtt_username": None,
    "mqtt_password": None,

    ```
- Uruchom energa2mqtt.py (np: python3 energa2mqtt.py)
- topic mqtt zostanie będzie ustawiony na /home/mojlicznik/nazwa twojego konta. Możesz to zmienić edytując:

```
"mqtt_topic_name": "home/mojlicznik/{}/{}",
```
- Do brokera mqtt wysyłane są następujące informacje:
  - name: a_plus dla energii zużytej, a_minus dla oddanej do sieci
  - description: Opis pola - "Eenrgia konsumpcja" albo "Energia produkcja"
  - last_update: data i czas kiedy Energa zaktualizowała dane (przeważnie codziennie o północy)
  - last_refresh: data i czas kiedy dane ostani raz zostały odświeżone (kiedy ostatni razy był uruchomiony program)
  - value: wartość odczytu
  - unit: jednostka - kWh

### Przykład (z home assistant developer tools):

```
unit_of_measurement: kWh
friendly_name: Licznik Energa produkcja
description: Energia produkcja
last_update: '2022-07-15 00:00:00'
last_refresh: '2022-07-15 21:57:38'
value: 1111.111
unit: kWh
```

 ### Przykładowa konfiguracja Home Assistant (do wpisania do /config/configuration.yaml)

```
# Licznik energa    
- platform: mqtt
    name: "Licznik Energa zużycie"
    json_attributes_topic: "home/mojlicznik/my home account/a_plus"
    state_topic: "home/mojlicznik/my home account/a_plus"
    unit_of_measurement: "kWh"
    value_template: "{{ value_json.value }}"
- platform: mqtt
    name: "Licznik Energa produkcja"
    json_attributes_topic: "home/mojlicznik/my home account/a_minus"
    state_topic: "home/mojlicznik/my home account/a_minus"
    unit_of_measurement: "kWh"
    value_template: "{{ value_json.value }}"
```

W Home assistancie powinniśmy zobaczyć:
```
    - sensor.licznik_energa_produkcja
    - sensor.licznik_energa_zuzycie
```

---

### Pliki systemd do konfiguracji periodycznego odczytu danych z poiomu użytkownika, można też skorzystać z cron-a (odsyłam do [podobnego projektu](https://github.com/PapuutekAPT/Energa-HomeAssistant-Integration#automatyczne-uruchanianie-skryptu))


Usługa systemd może być uruchamiana z poziomu zwykłego użytkownia. W tym przypadku uzyskujemy możliwość jej rekonfiguracji bez posiadania uprawnień superusera. Dodaj --user po poleceniu systemd np:

```
systemctl --user status energa2mqtt
systemctl --user stop energa2mqtt

```
Utworz pliki usługi w katalogu:

```
/home/<user>/.config/systemd/user
```

energa2mqtt.service
```
[Unit]
Description=Periodically run task to gather energy meter data from Energa webpage
Wants=network-online.target
After=network.target


[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/<user>/mojlicznik/energa2mqtt.py
WorkingDirectory=/home/<user>/mojlicznik
KillMode=mixed

[Install]
WantedBy=energa2mgtt.timer
```

energa2mqtt.timer
```
[Unit]
Description=Triggers energa2mqtt everyday

[Timer]
OnCalendar=*-*-* 01:00:00

[Install]
WantedBy=timers.target

```

Dalej postępuj w/g standardowych zasad:
```
systemctl --user enable energa2mqtt.service
systemctl --user enable energa2mqtt.timer

systemctl --user start energa2mqtt.timer

```
Sprawdz czy działa:

```
$ systemctl --user status energa2mqtt
● energa2mqtt.service - Periodically run task to gather energy meter data from webpage (Energa - mojlicznik.pl)
     Loaded: loaded (/home/<REDACTED>/.config/systemd/user/energa2mqtt.service; enabled; vendor preset: enabled)
     Active: inactive (dead) since Fri 2022-07-15 01:00:40 CEST; 22h ago
TriggeredBy: ● energa2mqtt.timer
    Process: 26506 ExecStart=/usr/bin/python3 /home/<REDACTED>/mojlicznik/energa2mqtt.py (code=exited, status=0/SUCCESS)
   Main PID: 26506 (code=exited, status=0/SUCCESS)
        CPU: 433ms

$ systemctl --user status energa2mqtt.timer
● energa2mqtt.timer - Triggers energa2mqtt everyday
     Loaded: loaded (/home/<REDACTED>/.config/systemd/user/energa2mqtt.timer; enabled; vendor preset: enabled)
     Active: active (waiting) since Tue 2022-07-12 14:19:45 CEST; 3 days ago
    Trigger: Sat 2022-07-16 01:00:00 CEST; 1h 55min left
   Triggers: ● energa2mqtt.service

```
Have fun!
