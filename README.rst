Introduction
============

.. image:: https://readthedocs.org/projects/adafruit-circuitpython-miniesptool/badge/?version=latest
    :target: https://circuitpython.readthedocs.io/projects/miniesptool/en/latest/
    :alt: Documentation Status

.. image:: https://img.shields.io/discord/327254708534116352.svg
    :target: https://discord.gg/nBQh6qu
    :alt: Discord

.. image:: https://travis-ci.com/adafruit/Adafruit_CircuitPython_miniesptool.svg?branch=master
    :target: https://travis-ci.com/adafruit/Adafruit_CircuitPython_miniesptool
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

Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/adafruit/Adafruit_CircuitPython_miniesptool/blob/master/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.

Building locally
================

Zip release files
-----------------

To build this library locally you'll need to install the
`circuitpython-build-tools <https://github.com/adafruit/circuitpython-build-tools>`_ package.

.. code-block:: shell

    python3 -m venv .env
    source .env/bin/activate
    pip install circuitpython-build-tools

Once installed, make sure you are in the virtual environment:

.. code-block:: shell

    source .env/bin/activate

Then run the build:

.. code-block:: shell

    circuitpython-build-bundles --filename_prefix adafruit-circuitpython-miniesptool --library_location .

Sphinx documentation
-----------------------

Sphinx is used to build the documentation based on rST files and comments in the code. First,
install dependencies (feel free to reuse the virtual environment from above):

.. code-block:: shell

    python3 -m venv .env
    source .env/bin/activate
    pip install Sphinx sphinx-rtd-theme

Now, once you have the virtual environment activated:

.. code-block:: shell

    cd docs
    sphinx-build -E -W -b html . _build/html

This will output the documentation to ``docs/_build/html``. Open the index.html in your browser to
view them. It will also (due to -W) error out on any warning like Travis will. This is a good way to
locally verify it will pass.
