.. _Installation:

Installation
============

Python 2.7
----------

.. _WinPython: https://winpython.github.io/

* Install WinPython_

    * get version 2.7.X+, 64 bit
    * install into C:\\

* Open WinPython Control Panel

    * Select Advanced -> Register distribution

Python Modules
--------------

.. _psycopg: http://www.stickpeople.com/projects/python/win-psycopg/
.. _`Opal Kelly FrontPanel`: https://pins.opalkelly.com/downloads
.. _pyqtgraph: https://github.com/pmaunz/pyqtgraph/archive/develop-pm.zip
.. _pyvisa: https://pyvisa.readthedocs.org/en/stable/

* Install psycopg_ -- used for interfacing with Postgres database

    * get Python 2.7 version, 64 bit

* Install `Opal Kelly FrontPanel`_ -- used for interfacing with FPGA

    * get 64 bit version
    * This will require registration with Opal Kelly Pins
    * This should install the **ok** module into C:\\$yourWinPythonDir$\\$yourPythonDir$\\Lib\\site-packages
    * **if there is no ok directory at this path:**

        * create directory "\\$yourWinPythonDir$\\$yourPythonDir$\\Lib\\site-packages\\ok"
        * copy into that directory contents of "C:\\Program Files\\Opal Kelly\\FrontPanelUSB\\API\\Python\\2.7\\x64"

* Change to custom branch of pyqtgraph_ -- used for all plotting

    * type "pip uninstall pyqtgraph" to uninstall existing copy of pyqtgraph
    * Extract the archive at your favorite location (inside download folder is just fine)
    * Open a command terminal
    * Change into the folder pyqtgraph-develop-pm
    * Execute

       .. code-block:: python

          >>> python setup.py install

* Install pyvisa_ -- used for communicating with many external instruments

    * get via pip:

      .. code-block:: python

         >>> pip install pyvisa

    * **Note:** versions 1.7 and 1.8 are definitely fine

* Equipment specific dependencies

    * The program contains code to communicate with a number of pieces of hardware that require specific files:

        * To use National Instruments hardware, Install **NISync**
        * To use Newport Conex controllers, install the Conex DLL from Newport
        * To use Chase AWGs, install the DLL from Chase

Database Server
---------------

.. _postgres: http://www.enterprisedb.com/products-services-training/pgdownload#windows

* Install postgres_ 9.4.1+ for windows, 64bit
* open pgAdmin III
* set postgres user password
* double click PostgreSQL
* right click Login roles, select New Login role

    * role name: **python**
    * set password on second tab of window
    * **Note:** This is the password that the program will use to access data stored in the database. **It is stored by the program in plain text!** Do not use a password you care deeply about.
    * click OK

* right click Databases

    * select **New Database**
    * Name: **ioncontrol**
    * Owner: **python**
    * click OK

* Close pgAdmin III

Git
---

.. _SourceTree: https://www.sourcetreeapp.com/

* Download and install SourceTree_, which is a convenient front-end for Git
* Click Clone/New
* Set the source path to be wherever you're getting the code from
* set the destination to be wherever you would like the code to go (this can be anywhere convenient)

Development Tools
-----------------

.. _pyCharm: https://www.jetbrains.com/pycharm/
.. _Eclipse: https://eclipse.org/downloads/

If you plan to make changes to the code, you will need a python IDE and version control software.

**IDE:**

We have used two different IDEs for development:

    1) pyCharm_
    2) the pyDev extension for Eclipse_

Each have some advantages and disadvantages. Take your pick. (JM prefers pyCharm)

If you want to use Eclipse_, do the following to install the PyDev extension:

    * Download Eclipse IDE for Java Developers (64 bit)
    * Extract the zip wherever you want to have it (no installation necessary) and make a shortcut to eclipse.exe (e.g. C:\Program Files\eclipse)
    * Open Eclipse
    * Help -> Install New Software
    * Add
      - Name PyDev
      - Location http://pydev.org/updates
    * Select PyDev and install
    * Eclipse restarts then Window -> Preferences -> PyDev -> Interpreters -> Python interpreter
    * Quick Autoconfig
    * To import the project into the workspace do File -> Import -> General -> Existing Projects into workspace
    * Select IonControl directory as root directory and finish