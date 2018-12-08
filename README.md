# miniesptool

ROM loader for ESP chips. currently only tested with ESP8266.
No blob-stub support yet, so you can't read MD5 back on ESP8266.

See this document for protocol we're implementing: 
https://github.com/espressif/esptool/wiki/Serial-Protocol

See this for the 'original' code we're miniaturizing: 
https://github.com/espressif/esptool/blob/master/esptool.py

There's a very basic Arduino ROM loader here for ESP32:
https://github.com/arduino-libraries/WiFiNINA/tree/master/examples/Tools/FirmwareUpdater