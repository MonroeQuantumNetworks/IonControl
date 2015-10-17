.. include:: inlineImages.include

Main GUI
========

.. figure:: images/ExperimentUi.png
   :scale: 100 %

   The main Experiment GUI

When you first start the program, the main GUI consists of a central area with plot windows surrounded by various control docks, with an action toolbar on top.

Toolbar
-------

The effects of the different toolbar actions are:

|start| -- start a scan
   This will run the scan set in the scan control dock, with the evaulation set in the evaulation control dock. When the scan concludes, it will run the analysis set in the analysis control dock.

|pause| -- pause a scan
   This will pause the scan wherever it currently is.

|stop| -- stop a scan
   This will stop the scan, but will still perform the analysis and register the scan in the measurement log.

|abort| -- abort a scan
   This will stop the scan, but will NOT perform the analysis or register the scan in the measurement log.

|save| -- save GUI configuration data
   This will save the GUI configuration to a new database file with the name "configuration_X.db" (where X is 001 the first time you hit save, then increments) which will be placed in the day's data directory. This can be used if you want to take a snapshot of your GUI configuration which you can later return to. Each time you click save, a new file is created. To reload the GUI configuration, copy the saved file to 'yourProjectDir/.gui-config', and rename it 'ExperimentUi.config'.

   Note that this is not for ordinary saving of the GUI configuration -- this happens automatically once a minute, and whenever the program is closed.

|XMLSave| -- save experiment configuration data to an XML file
  This will save all the global variables, scan settings, evaluation settings, analysis settings, and pulse program settings to XML files. These files can be imported via File > Import XML. This is mainly useful if you want to move a large list of experiment settings between projects.

|DedicatedCounters| -- open the :ref:`DedicatedCounters` window.
   \

|pulses| -- open the :ref:`PulseProgram` window.
   \

|voltages| -- open the :ref:`VoltageControl` window.
   \

|LogicAnalyzer| -- open the :ref:`LogicAnalyzer` window.
   \

|MeasurementLog| -- open the :ref:`MeasurementLog` window.
   \

|Scripting| -- open the :ref:`Scripting` window.
   \

|CheckBox| or |Exception| -- display if an exception occurred
   The |CheckBox| will turn into a |Exception| when an error occurs. If you click on it, you will see a list of all exceptions since the list was last cleared. You can clear the list, or clear individual exceptions.

|CheckBox| or |Warning| -- display if a warning occurred
   The |CheckBox| will turn into a |Warning| when a warning occurs. Interface is the same as for exceptions.

|histogram| -- copy histogram to traces
   This will copy the last histogram from the most recent scan to the trace list together with the other traces. From there it can be saved or viewed later.

|saveHistogram| -- save all histogram from last scan
   This will save every histogram from the most recent scan to a file. It does not create an entry in the trace list. The filename used is specified in the scan control (see :ref:`Scans`).

|addPlot| -- add a plot
   This will add a plot window, which will available for any evaluation.

|removePlot| -- remove a plot
   This will remove an existing plot window. Note: "Scan Data" and "Histogram" (and "Timestamps" if enabled) cannot be removed.

|renamePlot| -- rename a plot
   This will rename an existing plot window. The same plots which cannot be removed also cannot be renamed.

Menu Bar
--------

The menu bar has many of the same options as in the toolbar, with the addition of:

View
   Show or hide any dock widget

Print
   Print (or save to PDF or SVG) any of the plot windows, as configured by the Print Preferences dock.

File > Project:
   Show the current project and its configuration settings (see :ref:`Projects` ). Also allows setting the Project Selection GUI and Experiment Configuration GUI on next program start.

File > Import from XML:
   Import an XML file containing settings for the Scan Control, Evaluation, Analysis, Global Variables, or Pulse Program.

Docks
-----

All of the control and information windows in the main GUI are divided into the following docks:

FPGA Control Docks
~~~~~~~~~~~~~~~~~~

- Shutters

Scan Control Docks
~~~~~~~~~~~~~~~~~~

- Scan Control
- Evaluation Control
- Analysis Control
- Traces
- Fit
- Progress
- Average

see :ref:`Scans` for information on all of these docks.

External Parameters Docks
~~~~~~~~~~~~~~~~~~~~~~~~~

- Params Selection
- Params Control
- Params Reading

see :ref:`ExternalParameters` for information on all of these docks.