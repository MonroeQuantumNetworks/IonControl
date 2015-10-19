.. include:: inlineImages.include

.. _FPGAControl:

FPGA Control
============

When a scan is not running, the FPGA outputs can be controlled via the following docks:

- Shutters
   Allows control of each TTL output -- red is TTL low, green is TTL high. When the program is first run, default TTL names (set by the pulser config file) are shown in gray. Double click a name to change it. These shutter names also appear as labels in the pulse program shutters window.

   Shutter values set here are completely overwritten by the pulse program when a scan is running. When a scan stops, shutter values return to the values set here.

- Triggers
   Allows control of each trigger line. Select the lines you want to trigger, then click *Apply*. As with shutters, these names appear in the pulse program triggers window.

- DDS
   Set the frequency, amplitude and phase of each DDS. The *On* checkbox for a given DDS is completely equivalent to the corresponding DDS enable shutter channel (the two are linked; clicking one will click the other). The *Square* checkbox enables the digital output of the DDS.

   All fields here can be set to globals, or more generally to a mathematical expression, which can involve globals. If a field is set to a global (or an expression), it will be highlighted in green.

   If "Apply directly" is checked, the DDS will change to the value typed upon hitting enter. Otherwise, "Write All" will write the information to the DDSs (but not change their output), and "Apply" will trigger the DDSs to change their output to the values written. This is only necessary if you want to change the DDSs synchronously.

   DDS values set in the pulse program overwrite values set here during a scan. If the pulse program does NOT write a given value, then that value is left unchanged during a scan. At the conclusion of a scan, values revert to those set here.

- DAC
   Similar to DDS. For *IonControl-firmware-LX150-UMD.bit*, channels 0-7 control the DACs directly. Channels 8-15 are virtual DAC channels that control the DAC in concert with the PI loops. see :ref:`PILoops` .

   As with the DDSs, globals and expressions can be used, and values written in the pulse program overwrite values set here.

- Pulser Parameters

   Control various parameters associated with the FPGA.

   - PI Loop Parameters
      see :ref:`PILoops` .

   - DAC Scan Parameters
      Each of the 8 DACs on the breakout board can be configured to put out a triangle waveform by turning on the respective DAC Scan (shutters 41-48 on *IonControl-firmware-LX150-UMD.bit*). This can be useful if the DAC is being used for a lock. The parameters set here control the behavior of that scan:

      - Max
          The maximum of the triangle waveform

      -Min
         The minimum of the triangle waveform

      -Increment
         The amount it changes each clock cycle (which indirectly determines the frequency)

   - PI Loop Regulator Inputs
      see :ref:`PILoops` .

   - Output Delays
      Any TTL output shutter can be set to have a hardwired delay *t* of up to 1.25 us. This means that if an **update** command in the pulse program changes that shutter, the shutter actually changes a time *t* later. This is useful for compensating for timing offsets caused by things like the delay between triggering an AOM and the beam actually turning on.

.. _PILoops:

PI Loops
--------

Each of the 8 ADCs on the breakout board can be used as the error signal for a PI control loop. PI Loop <n> corresponds to ADC <n>. The output of the PI loop is reconfigurable -- any DAC or any DDS amplitude can "listen" to any PI loop. The PI loops are turned on and off via the shutters (shutters 32-39 on *IonControl-firmware-LX150-UMD.bit*). The PI loops can be used as either always-on or sample-and-hold. If *PI loop <n>* is turned off during the pulse program, and turned back on later, the integrator will pick up where it left off.

The routing of the PI loops is controlled in the Pulser Parameters dock by the PI Loop Regulator Inputs section. If *DAC<n> regulator input* is set to *<m>* where *m* is between 0 and 7, then *DAC<n>* will be controlled by *PI loop <m>* (and the corresponding error signal on *ADC<m>*) when *PI loop <m>* is enabled. If *DAC<n> regulator input* is set to any number over 7, then it will not be controlled by a PI loop. The same applies to all DDS amplitudes, which can also be controlled by a PI loop by setting *DDS<n> regulator input*.

The settings of the PI loop are set in the *PI Loop Parameters* section of the Pulser Parameters dock.

- P Coefficient
   Proportional gain (units: unitless)

- I Coefficient
   Integrator gain (units: unitless)

- delay Coefficient (units: time)
   This is similar to "Output Delays" in the Pulser parameters dock. It tells the PI loop to not engage after being switched on until the delay has elapsed. For example, suppose the PI loop is stabilizing a laser intensity in a sample-and-hold configuration in the pulse program. After the laser is switched on, there is a 5 us ramp up before it is fully on and the photodiode signal is stable. The PI loop should not try and stabilize for those first 5 us. By setting the delay to 5 us in the pulser parameters, the PI loop and the laser can be turned on in the same shutter in the pulse program without causing problems.

- offset Coefficient (units: volts)
   This is the lock point of the PI loop. The PI loop will try and stabilize the ADC signal to this value.