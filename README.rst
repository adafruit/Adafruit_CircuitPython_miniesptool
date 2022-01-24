Introduction
============

.. image:: https://readthedocs.org/projects/adafruit-circuitpython-miniesptool/badge/?version=latest
    :target: https://docs.circuitpython.org/projects/miniesptool/en/latest/
    :alt: Documentation Status

.. image:: https://img.shields.io/discord/327254708534116352.svg
    :target: https://adafru.it/discord
    :alt: Discord

.. image:: https://github.com/adafruit/Adafruit_CircuitPython_miniesptool/workflows/Build%20CI/badge.svg
    :target: https://github.com/adafruit/Adafruit_CircuitPython_miniesptool/actions/
    :alt: Build Status

ROM loader for ESP chips, works with ESP8266 or ESP32.
This is a 'no-stub' loader, so you can't read MD5 or firmware back on ESP8266.

See this document for protocol we're implementing:
https://github.com/espressif/esptool/wiki/Serial-Protocol

See this for the 'original' code we're miniaturizing:
https://github.com/espressif/esptool/blob/master/esptool.py

There's a very basic Arduino ROM loader here for ESP32:
https://github.com/arduino-libraries/WiFiNINA/tree/master/examples/Tools/FirmwareUpdater

Dependencies
=============
This driver depends on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_

Please ensure all dependencies are available on the CircuitPython filesystem.
This is easily achieved by downloading
`the Adafruit library and driver bundle <https://github.com/adafruit/Adafruit_CircuitPython_Bundle>`_.

Installing from PyPI
--------------------

On supported GNU/Linux systems like the Raspberry Pi, you can install the driver locally `from
PyPI <https://pypi.org/project/adafruit-circuitpython-miniesptool/>`_. To install for current user:

.. code-block:: shell

    pip3 install adafruit-circuitpython-miniesptool

To install system-wide (this may be required in some cases):

.. code-block:: shell

    sudo pip3 install adafruit-circuitpython-miniesptool

To install in a virtual environment in your current project:

.. code-block:: shell

    mkdir project-name && cd project-name
    python3 -m venv .env
    source .env/bin/activate
    pip3 install adafruit-circuitpython-miniesptool

Usage Example
=============

Check the examples folder for demo sketches to upload firmware to ESP8266 and ESP32

Documentation
=============

API documentation for this library can be found on `Read the Docs <https://docs.circuitpython.org/projects/miniesptool/en/latest/>`_.

Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/adafruit/Adafruit_CircuitPython_miniesptool/blob/main/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.

Documentation
=============

For information on building library documentation, please check out `this guide <https://learn.adafruit.com/creating-and-sharing-a-circuitpython-library/sharing-our-docs-on-readthedocs#sphinx-5-1>`_.
