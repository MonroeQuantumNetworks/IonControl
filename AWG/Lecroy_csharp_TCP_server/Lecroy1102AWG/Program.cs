using System;
using System.Net;  //import IPAddress
using System.Net.Sockets;  //import Socket
using System.Text;  // import Encoding
using System.Collections.Generic;  // import List

//import the following shortcuts from the DLL:
//Device, DeviceSet, Functionality, ARBChannel, ATError, ClockSource, FrequencyInterpolation,
//OutputImpedance, TriggerMode, TriggerSource, SensitivityEdge, TriggerAction, 
//WaveformStruct, GenerationSequenceStruct, TransferMode
using ActiveTechnologies.Instruments.AWG4000.Control;

class Lecroy1102AWG
{
    ARBChannel[] channels;
    Device device;
    ARBChannel channel0;
    ARBChannel channel1;
    Socket listener = null;
    Socket handler = null;

    public Lecroy1102AWG(int port)
    {
        bool isInitialized = Initialize();
        if (isInitialized)
        {
            //Configure(new byte[0]);  // configure with default info
            ServerLoop(port);
        }
        else
        {
            Console.WriteLine("Unable to find any AWG device.");
        }

        // Shutdown and exit
        if (!(device == null))
        {
            // stop the AWG
            Stop();
        }
    }

    void InitializeTCP(int port)
    {
        // wait for TCP connection

        // Establish the local endpoint for the socket.
        // Dns.GetHostName returns the name of the host running the application.
        //IPHostEntry ipHostInfo = //Dns.GetHostName()); //or "localhost"? //Dns.Resolve("locahost");
        IPAddress ipAddress = IPAddress.Any; // use ipHostInfo.AddressList[0]; instead to limit connections to this computer
        IPEndPoint localEndPoint = new IPEndPoint(ipAddress, port);

        // Create a TCP/IP socket.
        listener = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
        listener.Blocking = true;

        // Bind the socket to the local endpoint and 
        listener.Bind(localEndPoint);

        // listen for incoming connections.
        listener.Listen(1);

        // Start listening for connections.
        Console.WriteLine("Waiting for a connection...");

        // Program is suspended while waiting for an incoming connection.
        handler = listener.Accept();

        Console.WriteLine("TCP connected.");

        // set timeout to 10 seconds
        handler.Blocking = true;
        //handler.ReceiveTimeout = 10000;
        Console.WriteLine("handler.ReceiveBufferSize = " + handler.ReceiveBufferSize.ToString());
    }

    bool ReceiveTCP()
    {
        /*
            This function takes in a TCP message, checks to see if it correctly formatted, and returns it as an array of strings for use in command processing
        */

        // variables to store incoming data from the client
        string data = null;
        byte[] bytes = null;
        byte[] bytes_in = null;
        int bytesRec = 0;
        int bytes_read = 0;

        try
        {
            // wait for a new TCP message, read first 4 bytes
            bytes = new byte[4];
            bytesRec = handler.Receive(bytes);

            // check to see if the message is correctly formatted: the first 4 bytes should read "MESG"
            if (bytesRec != 4)
            {
                // The message header was bad.  Close socket and start over, requiring new connection
                Console.WriteLine("Bad message header.  Should start with 4 bytes spelling MESG.  Shutting down socket.");
                return false;
            }
            data = Encoding.ASCII.GetString(bytes);

            if (data != "MESG")
            {
                // The message header was bad.  Close socket and start over, requiring new connection
                Console.WriteLine("Bad message header.  Should start with MESG.  Shutting down socket.");
                return false;
            }

            // read the next 4 bytes to get the message size
            bytes = new byte[4];
            bytesRec = handler.Receive(bytes);
            if (bytesRec != 4)
            {
                // The message header was bad.  Close socket and start over, requiring new connection  !!!
                Console.WriteLine("Bad message header length, should be 4 byte uint.  Shutting down socket.");
                return false;
            }
            Array.Reverse(bytes); // Correct for endian-ness
            UInt32 length = BitConverter.ToUInt32(bytes, 0);
            System.Console.WriteLine(((int)length).ToString());
            Console.WriteLine("TCP message: expecting length " + length.ToString());

            // now read the number of bytes of the rest of the message
            bytes = new byte[length];
            bytes_in = new byte[length];
            //bytesRec = handler.Receive(bytes, (int)length, 0);
            // read until we get the right number of bytes
            bytesRec = 0;
            do
            {
                bytes_read = handler.Receive(bytes_in);
                Array.Copy(bytes_in, 0, bytes, bytesRec, bytes_read);
                bytesRec += bytes_read;
                System.Console.WriteLine("receiving: " + bytesRec.ToString() + " " + bytes_read.ToString());
            } while (bytesRec < length);
            if (bytesRec != length)
            {
                // The message length was bad.  Close socket and start over, requiring new connection
                Console.WriteLine("\nBad message length.  Expecting " + length.ToString() + " but received " + bytesRec.ToString() + ". Shutting down socket.");
                return false;
            }

            Console.WriteLine("Received length " + length.ToString());
            //Console.WriteLine(Encoding.ASCII.GetString(bytes));

            // we need at least 4 bytes to have a command string
            if (bytesRec >= 4)
            {
                //read the first 4 bytes
                byte[] command_bytes = new byte[4];
                Array.Copy(bytes, 0, command_bytes, 0, 4);
                string command = Encoding.ASCII.GetString(command_bytes);

                byte[] command_data;
                if (bytes.Length > 4)
                {
                    // save read everything after the first 4 bytes
                    command_data = new byte[bytes.Length - 4];
                    Array.Copy(bytes, 4, command_data, 0, bytes.Length - 4);
                }
                else
                {
                    command_data = new byte[0];
                }

                switch (command)
                {
                    case "CONF":
                        Configure(command_data);
                        break;
                    case "UPDA":
                        Update(command_data);
                        break;
                    case "TRIG":
                        ForceTrigger();
                        break;
                }
            }
            // loop and look for next command
            return true;
        }
        catch (Exception e)
        {
            Console.WriteLine("Caught exception in ReceiveTCP().");
            Console.WriteLine(e.ToString());
            return false;
        }
    }

    void ServerLoop(int port)
    {
        while(true) // loop forever looking for connections
        {
            try
            {
                InitializeTCP(port);

                Console.WriteLine("TCP port initialized.");

                // Loop looking for incoming messages
                while (ReceiveTCP())
                {
                    //handle message
                }
                //close socket and retry
                if (!(handler == null))
                {
                    handler.Shutdown(SocketShutdown.Both);
                    handler.Close();
                    handler = null;
                }
                if (!(listener == null))
                {
                    listener.Shutdown(SocketShutdown.Both);
                    listener.Close();
                    listener = null;
                }
            }
            catch (SocketException e)
            {
                //close socket and retry
                if (!(handler == null))
                {
                    handler.Shutdown(SocketShutdown.Both);
                    handler.Close();
                    handler = null;
                }
                //System.Console.WriteLine("Caught Socket Exception in ServerLoop().");
                //System.Console.WriteLine("Socket Exception: " + e.ToString());
            }
            // Wait a little bit to prevent trying to connect to the socket right away.
            System.Threading.Thread.Sleep(1);  // 500 ms
        }
    }

    bool Initialize()
    {
        // *** Initialize AWG ***

        DeviceSet deviceSet = new DeviceSet();

        if (deviceSet.DeviceList.Count <= 0)
        {
            Console.WriteLine("No devices found");
            return false;
        }

        device = deviceSet.DeviceList[0];
        Console.WriteLine("Connected to AWG device: " + device.AWGModelType + " " + device.SerialId);

        Functionality[] funct = { Functionality.ARB, Functionality.ARB };
        device.Initialize(funct);

        channel0 = (ARBChannel) device.GetChannel(0);
        channel1 = (ARBChannel) device.GetChannel(1);
        channels = new ARBChannel[] { channel0, channel1 };
        // check errors
        ATError error;
        error = device.ErrorResult;
        if (error.ErrorCode != 0)
        {
            Console.WriteLine("AWG device error: ", error.ErrorCode);
            Console.WriteLine(error.ErrorDescription);
            Console.WriteLine(error.ErrorSource);
            return false;
        }
        error = channel0.ErrorResult;
        if (error.ErrorCode != 0)
        {
            Console.WriteLine("AWG device error: ", error.ErrorCode);
            Console.WriteLine(error.ErrorDescription);
            Console.WriteLine(error.ErrorSource);
            return false;
        }
        error = channel1.ErrorResult;
        if (error.ErrorCode != 0)
        {
            Console.WriteLine("AWG device error: ", error.ErrorCode);
            Console.WriteLine(error.ErrorDescription);
            Console.WriteLine(error.ErrorSource);
            return false;
        }
        return true;
    }

    void Configure(byte[] command_data)
    {
        // *** Configure AWG ***
        
        // Set a default value for sample_frequency.  This will be overwritten if it was passed as a command string.
        decimal sample_frequency = 244258800;
        ClockSource clock_type = ClockSource.External; //or .Internal

        // Set a default value for external_clock_frequency.  This will be overwritten if it was passed as a command string.
        decimal external_clock_frequency = 81419600;
        
        // The rest of these settings could also be passed in from python, but for now they are hard coded here.

        FrequencyInterpolation interpolation = FrequencyInterpolation.Frequency2X;  // 1X, 2X or 4X

        double amplitude_correction_factor0 = 1.0;
        ulong samplig_rate_prescaler0 = 1;
        OutputImpedance outimpedance0 = OutputImpedance.Ohm50;
        float voltage0 = 0.0F;
        TriggerMode trigger_mode0 = TriggerMode.Stepped;
        uint delay_samples0 = 0;
        TriggerSource source0 = TriggerSource.FPTriggerIN;
        SensitivityEdge edge0 = SensitivityEdge.RisingEdge;
        TriggerAction action0 = TriggerAction.TriggerStart;

        double amplitude_correction_factor1 = 1.0;
        ulong samplig_rate_prescaler1 = 1;
        OutputImpedance outimpedance1 = OutputImpedance.Ohm50;
        float voltage1 = 0.0F;
        TriggerMode trigger_mode1 = TriggerMode.Stepped;
        uint delay_samples1 = 0;
        TriggerSource source1 = TriggerSource.FPTriggerIN;
        SensitivityEdge edge1 = SensitivityEdge.RisingEdge;
        TriggerAction action1 = TriggerAction.TriggerStart;

        // Parse command string.  Loop through the list until we have read all the commands.
        int index = 0;
        // Commands start with at least a 4 byte command word.  Check to see if we have at least that much command_data left.

        Console.WriteLine("Configure: command_data = " + Encoding.ASCII.GetString(command_data));
        Console.WriteLine("Configure: command_data.Length = " + command_data.Length);
        while (index+4 <= command_data.Length)
        {
            // read first 4 bytes
            byte[] command_bytes = new byte[4];
            Array.Copy(command_data, index, command_bytes, 0, 4);
            index += 4;  // move the counter along through command_data

            System.Console.WriteLine("Configure: command_bytes = " + Encoding.ASCII.GetString(command_bytes));

            string command = Encoding.ASCII.GetString(command_bytes);

            System.Console.WriteLine("Configure: command = " + command);

            switch (command)
            {
                case "rate":

                    System.Console.WriteLine("Configure: setting sample rate.");

                    // get an 8 byte double
                    if (index+8 <= command_data.Length)
                    {
                        // make a temporary copy of the 8 bytes
                        byte[] sample_frequency_bytes = new byte[8];
                        Array.Copy(command_data, index, sample_frequency_bytes, 0, 8);
                        Array.Reverse(sample_frequency_bytes); // Correct for endian-ness
                        double sample_frequency_double = BitConverter.ToDouble(sample_frequency_bytes, 0);
                        
                        //double sample_frequency_double = BitConverter.ToDouble(command_data, index);
                        System.Console.WriteLine("Configure: sample_frequency_double = " + sample_frequency_double.ToString());
                        
                        // convert double to decimal.  Encase in try block, because it can overflow.
                        try
                        {
                            sample_frequency = System.Convert.ToDecimal(sample_frequency_double);
                            System.Console.WriteLine("Configure: sample_frequency = " + sample_frequency.ToString());
                        }
                        catch (System.OverflowException)
                        {
                            System.Console.WriteLine("Overflow in double-to-double conversion.");
                        }
                    }
                    index += 8;
                    break;
                case "eclk":

                    System.Console.WriteLine("Configure: setting external clock rate.");

                    // get an 8 byte double
                    if (index + 8 <= command_data.Length)
                    {
                        // make a temporary copy of the 8 bytes
                        byte[] external_clock_frequency_bytes = new byte[8];
                        Array.Copy(command_data, index, external_clock_frequency_bytes, 0, 8);
                        Array.Reverse(external_clock_frequency_bytes); // Correct for endian-ness
                        double external_clock_frequency_double = BitConverter.ToDouble(external_clock_frequency_bytes, 0);

                        System.Console.WriteLine("Configure: external_clock_frequency_double = " + external_clock_frequency_double.ToString());

                        // convert double to decimal.  Encase in try block, because it can overflow.
                        try
                        {
                            external_clock_frequency = System.Convert.ToDecimal(external_clock_frequency_double);
                            System.Console.WriteLine("Configure: external_clock_frequency = " + external_clock_frequency.ToString());
                        }
                        catch (System.OverflowException)
                        {
                            System.Console.WriteLine("Overflow in double-to-double conversion.");
                        }
                    }
                    index += 8;
                    break;
            }
        }

        // stop AWG
        Stop();

        // device config
        System.Console.WriteLine("sample_frequency before SetSamplingFrequency: " + sample_frequency.ToString());

        decimal right_frequency = 0; //test

        AWG_err("SetSamplingFrequency", device.SetSamplingFrequency(ref sample_frequency, ref right_frequency, clock_type, external_clock_frequency));
        System.Console.WriteLine("sample_frequency after SetSamplingFrequency: " + sample_frequency.ToString());
        System.Console.WriteLine("right_frequency after SetSamplingFrequency: " + right_frequency.ToString());
        AWG_err("SetFrequencyInterpolation", device.PairLeft.SetFrequencyInterpolation(interpolation));

        // channel 0 config
        channel0.AmplitudeCorrectionFactor = amplitude_correction_factor0;
        channel0.SampligRatePrescaler = samplig_rate_prescaler0;
        AWG_err("channel0.SetOutputImpedance", channel0.SetOutputImpedance(outimpedance0));
        AWG_err("channel0.SetOutputVoltage", channel0.SetOutputVoltage(voltage0));
        AWG_err("channel0.SetTriggerMode", channel0.SetTriggerMode(trigger_mode0));
        AWG_err("channel0.SetTriggerDelay", channel0.SetTriggerDelay(delay_samples0));
        AWG_err("channel0.SetExternalTrigger", channel0.SetExternalTrigger(source0, edge0, action0));

        // channel 1 config
        channel1.AmplitudeCorrectionFactor = amplitude_correction_factor1;
        channel1.SampligRatePrescaler = samplig_rate_prescaler1;
        AWG_err("channel1.SetOutputImpedance", channel1.SetOutputImpedance(outimpedance1));
        AWG_err("channel1.SetOutputVoltage", channel1.SetOutputVoltage(voltage1));
        AWG_err("channel1.SetTriggerMode", channel1.SetTriggerMode(trigger_mode1));
        AWG_err("channel1.SetTriggerDelay", channel1.SetTriggerDelay(delay_samples1));
        AWG_err("channel1.SetExternalTrigger", channel1.SetExternalTrigger(source1, edge1, action1));

        // start AWG
        Start();

        System.Console.WriteLine("AWG configured.");
    }

    void Update(byte[] command_data)
    {
        // *** Update AWG waveforms ***
        
        // Parse command string.  Loop through the list until we have read all the commands.
        int index = 0;
        // read the length of the first waveform (number of 8 bytes doubles), encoded as a 4 byte long
        // read first 4 bytes
        byte[] waveform_0_length_encoded = new byte[4];
        Array.Copy(command_data, index, waveform_0_length_encoded, 0, 4);
        index += 4;
        Array.Reverse(waveform_0_length_encoded); // Correct for endian-ness
        UInt32 waveform_0_length = BitConverter.ToUInt32(waveform_0_length_encoded, 0);
        Console.WriteLine("Waveform 0 length: " + waveform_0_length.ToString());

        // read the rest of waveform 0
        double[] waveform_0 = new double[waveform_0_length];
        //byte[] waveform_0_encoded = new byte[waveform_0_length * 8];
        // Array.Copy(command_data, index, waveform_0_encoded, 0, waveform_0_length * 8);
        // Array.Reverse(waveform_0_encoded);
        Buffer.BlockCopy(command_data, index, waveform_0, 0, (int) waveform_0_length*8);
        /*
        for (int i=0; i<waveform_0_length; i++)
        {
            Console.Write(waveform_0[i]);
            Console.Write(" ");
        }
        */
        System.Console.WriteLine("");
        index += (int) waveform_0_length * 8;

        // waveform 1
        // read 4 bytes
        byte[] waveform_1_length_encoded = new byte[4];
        Array.Copy(command_data, index, waveform_1_length_encoded, 0, 4);
        index += 4;
        Array.Reverse(waveform_1_length_encoded); // Correct for endian-ness
        UInt32 waveform_1_length = BitConverter.ToUInt32(waveform_1_length_encoded, 0);
        Console.WriteLine("Waveform 1 length: " + waveform_1_length.ToString());

        // read the rest of waveform 1
        double[] waveform_1 = new double[waveform_1_length];
        Buffer.BlockCopy(command_data, index, waveform_1, 0, (int) waveform_1_length * 8);
        /*
        for (int i = 0; i < waveform_1_length; i++)
        {
            Console.Write(waveform_1[i]);
            Console.Write("");
        }
        */
        System.Console.WriteLine("");
        index += (int) waveform_1_length * 8;

        double[][] samples = new double[2][] { waveform_0, waveform_1 };
        uint num_channels = 2;
        
        // Stop AWG
        Stop();

        for (uint i = 0; i < num_channels; i++)
        {
            ARBChannel channel = channels[i];

            // The AWG can be programmed with multiple waveforms per channel, to be executed consecutively.
            //  However, because we can string together arbitrary sequences easily in Python, we use only the first waveform on each channel.
            int rows = 1;

            // clear channel
            AWG_err("ClearBuffer WaveformsSamples", channel.ClearBuffer(ARBBufferType.WaveformsSamples));
            AWG_err("ClearBuffer GenerationList", channel.ClearBuffer(ARBBufferType.GenerationList));

            // create an array of WaveformStruct, which will be populated with default WaveformStruct objects
            WaveformStruct[] waveforms = new WaveformStruct[rows];

            // The AWG triggers as soon as it's programmed.  To fix this, rotate the array of waveforms so that
            // once we start the experiment, the right waveform comes first.
            // We start by assigning the last sample (rows-1) to the 0 position.

            waveforms[0].Sample = samples[i];

            // load each row of the samples into waveforms
            // offset samples by one row (j+1) to account for rotation of the whole array
            // leave off last row (rows-1) as that has already been assigned
            /*
            for (int j = 0; j < rows - 1; j++)
            {
                waveforms[j + 1].Sample = samples[i][j];
            }
            */

            GenerationSequenceStruct[] sequence = new GenerationSequenceStruct[rows];
            for (uint j = 0; j < rows; j++)
            {
                sequence[j].Repetitions = 1;
                sequence[j].WaveformIndex = j;
            }

            // load sequence into channel i
            AWG_err("LoadWaveforms", channel.LoadWaveforms(waveforms));
            AWG_err("LoadGenerationSequence", channel.LoadGenerationSequence(sequence, TransferMode.NonReEntrant, true));

        }

        System.Console.WriteLine("AWG succesfully programmed.");

        Start();
    }

    void Start()
    {
        // start AWG
        byte[] channelId = { 1, 2 };
        AWG_err("Start", device.RUN(channelId));
    }

    void Stop()
    {
        // *** Stop AWG ***
        AWG_err("Stop", device.STOP());
        AWG_err("CloseCompletedTransfers", device.CloseCompletedTransfers());
    }
    
    void ForceTrigger()
    {
        byte[] channelId = { 1, 2 };
        AWG_err("ForceTrigger", device.ForceTrigger(channelId));
    }

    void AWG_err(string text, ATError err)
    {
        System.Console.Write(text + ": ");
        if (err.ErrorSource == 0)
        {
            System.Console.WriteLine("ok");
        }
        else
        {
            System.Console.WriteLine("error");
            System.Console.WriteLine("    code: " + err.ErrorCode.ToString());
            System.Console.WriteLine("    error source: " + err.ErrorSource.ToString());
            System.Console.WriteLine("    error description: " + err.ErrorDescription);
        }
    }

    public static int Main(string[] args)
    {
        int port = 11000;  // default port number
        if (args.Length <1)
        {
            Console.WriteLine("No TCP port specified.  Defaulting to 11000.  To pass in a port number as a command line parameter, try: Lecroy1102AWG.exe 11000");
        }
        else
        {
            // read port number as a command line parameter
            try
            {
                port = Int32.Parse(args[0]);
            }
            catch (Exception e)
            {
                System.Console.WriteLine("Error: "+e.ToString());
                Console.WriteLine("Could not convert command line parameter to integer for use as TCP port number.  Try: Lecroy1102AWG.exe 11000");
                return 1;
            }
        }
        new Lecroy1102AWG(port);
        return 0;
    }
}
