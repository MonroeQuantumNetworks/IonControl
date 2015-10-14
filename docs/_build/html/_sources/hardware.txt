Hardware
========

The only FPGAs that can currently be used with this software are the Opal Kelly **XEM6010-LX45** and the **XEM6010-LX150**. The LX150 is a larger FPGA, but you cannot compile firmware for it without a license. It is therefore a more expensive option if you need to modify the FPGA firmware itself. However, the firmware as it stands is pushing the capacity limits of the LX45, and there is very little room for any future modifications.

A given bitfile assumes a specific internal hardware configuration, as the FPGA must know what pins are connected to what DDS/DAC/ADC. The hardware configuration described here is for the LX150 firmware *IonControl-firmware-LX150-UMD.bit*. This firmware is setup for use with the Duke breakout board *OpalKellyIonControlBoxFanout_v3b*, which contains 8x DACs, 8x ADCs, 3x 8 pin TTL input banks, 9x 8 pin TTL output banks, and 10x SMA TTL outputs (for connecting to RF switches).

The FPGA is configured to talk to the 4x of the 2 channel AD9912 DDS boards: *DDS-AD9912_r4*, for a total of 8x DDSs. The breakout board should be connected to the DDSs as follows:

* **Out3**: Channels 1 and 0 in the opposite order from what's labeled on the DDS board, that is if you look at the board with the rf output connectors facing you and the chip on the top side then the left channel is channel 0, the right channel 1)
* **Out4**: Channels 3 and 2 (same as above)
* **Out5**: Channels 5 and 4
* **Out6**: Channels 7 and 6

SMA switch channels:

* **DDS 0**: JP2-31
* **DDS 1**: JP2-34
* **DDS 2**: JP2-30
* **DDS 3**: JP2-33
* **DDS 4**: JP2-29
* **DDS 5**: JP2-32
* **DDS 6**: JP2-37
* **DDS 7**: JP2-38
