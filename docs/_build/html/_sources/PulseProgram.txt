.. include:: inlineImages.include

.. _PulseProgram:

Pulse Program
-------------

Once the configuration files have been setup, the main program opens. The first time the program runs, the pulse program window will also open. On subsequent runs, it will return to whatever state it was in when it was closed last. To open the pulse program window, click |pulses| .

The pulse program window consists of four sections. The primary section is the text file itself, which is under the heading *Pulse Program*. The two sections *Shutters, Triggers, Counters* and *Parameters* are interfaces to set the variables which are declared in the pulse program. The *Shutters, Triggers, Counters* window is for settings binary variables, while the *Parameters* window is for setting all other types of parameters. Finally, the *RAM Control* window is for directly writing to the RAM on the FPGA board.

When a pulse program is saved (CTRL-S in the editor, or click |save|), the program attempts to compile it. If it fails, it indicates where and why it failed. If it is successful, it updates the parameters, shutters, triggers, and counters displays to match the pulse program.

.. figure:: images/PulseProgram.png
   :scale: 100 %

   The pulse program interface

The pulse program written here is run on the FPGA. It is compiled to a machine code that contains microcontroller instructions that are understood by the FPGA.

Pulse Program Syntax
~~~~~~~~~~~~~~~~~~~~

variable types
``````````````

- const
   A constant value, which we typically use for things like DDS Channels, e.g.:

   .. code-block:: C

      const DDSDetect = 0
      const DDSCooling = 1

- parameter
   A numerical value that is set by the user or by a scan. This is the main variable type which allows configuring the experiment. When the pulse program is saved, the list of parameters in the parameter window is updated.

   The simplest parameter declaration would look like:

   .. code-block:: Python

      parameter CoolingTime

   This initializes a parameter named "CoolingTime," which will show up in the parameter table and as a scan target. You can also type:

   .. code-block:: Python

      parameter CoolingTime = 500 us

   The effect of this will be to set CoolingTime to 500 us when you save the program and CoolingTime is added to the parameter list. However, that is the only time the 500 us value is read! Every subsequent time the program is run, the value of CoolingTime will be set via whatever is typed into the Parameters table, or via a scan. Therefore, this is to be avoided, as it can lead to confusion, and instead parameters should be declared without any value called out in the pulse program code.

   A parameter can also have a device specific *encoding*. An encoding is a way of translating something like "200 MHz" into a frequency tuning word used to program a DDS. An encoding is written like this:

   .. code-block:: Python

      parameter <AD9912_FRQ> CoolingFreq

   This means that :python:`CoolingFreq`, which is in MHz, will be converted appropriately to program an AD9912 DDS. Encodings are only necessary on a frequency that is actually written to a DDS. For example, the following is fine:

   .. code-block:: Python

      const DDSRaman1 = 2
      parameter RamanCarrierFreq
      parameter RamanDetuning
      parameter <AD9912_FRQ> DDSRaman1Freq
      set_dds(channel=DDSRaman1, freq=DDSRaman1Freq)

   where in the parameters table, :python:`DDSRaman1Freq` is set to :python:`RamanCarrierFreq + RamanDetuning`. Only :python:`DDSRaman1Freq` need have the encoding, as it is the only one which is directly written to the DDS, while the others are used indirectly.

   The following encodings are available:

   - AD9912_FRQ
      frequency to set an AD9912 DDS
   - AD9910_FRQ
      frequency to set an AD9910 DDS
   - AD9912_PHASE
      phase to set an AD9912 DDS
   - AD9910_PHASE
      phase to set an AD9910 DDS
   - DAC8568_VOLTAGE
      voltage to set a DAC8568 DAC
   - ADC7606_VOLTAGE
      voltage returned by the ADC7606 ADC
   - ADC_VOLTAGE
   - ADCTI122S101_VOLTAGE

- var
   An internal variable. This is something that might change throughout the course of an experiment (unlike **const**), but which is set within the experiment rather than by the user. An example would be:

   .. code-block:: C#

      var experimentsleft = 100

   where experimentleft is an internal variable, initialized to 100. (In the pulse program this is from, it is used to keep track of how many experiments are remaining). The difference between **var** and **parameter** is only in how they are treated by the GUI; **var** variables are not shown in the GUI as something to be scanned or set by the user. Also, normally there are programmatic changes made to **vars**, while **parameters** are not changed by the program unless they are being scanned. This is for clarity, though, not a requirement. As with parameters, vars can have an encoding.

   Unlike parameters, vars often need to be initialized in the code, as they are not overridden from outside the code.

- shutter
   A shutter is a binary variable, which specifies the state of every TTL output of the FPGA, whether every PI loop is on or off, and whether the DAC scans are on or off see (:ref:`PILoops` for an explanation of the last two). When a shutter is added to the pulse program, a new line appears in the shutters window

- counter
  A counter variable. When a counter is added, a new line appears in the counters GUI.

- masked_shutter
- trigger
- address
- exitcode

commands
````````

.. _PILoops:

PI Loops
~~~~~~~~

