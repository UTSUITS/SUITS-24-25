using System.Collections;
using System.Collections.Generic;
using Unity.XR.CoreUtils.Datums;
using UnityEngine;

public class TelemetrySimulator : MonoBehaviour
{
    public SliderManager sliderManager;
    public float updateInterval = 1.0f;

    private float timer = 0f;

    void Update()
    {
        timer += Time.deltaTime;

        if (timer >= updateInterval)
        {
            SimulateTelemetry();
            timer = 0f;
        }
    }

    void SimulateTelemetry()
    {
        foreach (var binding in sliderManager.sliders)
        {
            if (binding.updater == null) continue;

            var valueData = binding.updater.valueData;
            var valueKey = binding.updater.valueKey;

            if (valueData != null && valueData.valueRanges.ContainsKey(valueKey))
            {
                var range = valueData.valueRanges[valueKey];

                float simulatedValue;
                if (!float.IsNaN(range.nominal))
                {
                    simulatedValue = Random.Range(range.nominal * 0.8f, range.nominal * 1.2f);
                }
                else
                {
                    simulatedValue = Random.Range(range.min, range.max);
                }

                simulatedValue = Mathf.Clamp(simulatedValue, range.min, range.max);


                binding.updater.SetSliderValue(simulatedValue);
            }
        }
    }
}

//using System;
//using System.Collections;
//using System.Collections.Generic;
//using System.IO;
//using System.Net;
//using System.Net.Sockets;
//using System.Text;
//using UnityEngine;

//public class TelemetryUDPClient : MonoBehaviour
//{
//    public SliderManager sliderManager;
//    public float updateInterval = 1.0f;
//    private float timer = 0f;

//    private UdpClient udpClient;
//    private IPEndPoint serverEndPoint;
//    private string ipAddress;
//    private float? teamNumber = null;

//    private HashSet<int> floatOutputs = new HashSet<int>();

//    void Start()
//    {
//        LoadServerInfo();
//        InitializeUDP();
//        InitializeFloatOutputs();
//    }

//    void Update()
//    {
//        timer += Time.deltaTime;

//        if (timer >= updateInterval)
//        {
//            StartCoroutine(CollectData());
//            timer = 0f;
//        }
//    }

//    void LoadServerInfo()
//    {
//        try
//        {
//            string path = "/home/utsuits/ip_address.txt"; // Change if needed
//            if (File.Exists(path))
//            {
//                var lines = File.ReadAllLines(path);
//                if (lines.Length > 0) ipAddress = lines[0].Trim();
//                if (lines.Length > 1 && float.TryParse(lines[1].Trim(), out float teamNum))
//                {
//                    teamNumber = teamNum;
//                }
//            }
//            else
//            {
//                Debug.LogError("IP Address file not found.");
//            }
//        }
//        catch (Exception ex)
//        {
//            Debug.LogError($"Error reading IP Address file: {ex}");
//        }
//    }

//    void InitializeUDP()
//    {
//        try
//        {
//            udpClient = new UdpClient();
//            udpClient.Client.ReceiveTimeout = 200; // milliseconds
//            serverEndPoint = new IPEndPoint(IPAddress.Parse(ipAddress), 14141);
//        }
//        catch (Exception ex)
//        {
//            Debug.LogError($"UDP Initialization error: {ex}");
//        }
//    }

//    void InitializeFloatOutputs()
//    {
//        floatOutputs = new HashSet<int>();
//        for (int i = 17; i <= 30; i++) floatOutputs.Add(i);
//        for (int i = 32; i <= 41; i++) floatOutputs.Add(i);
//        for (int i = 43; i <= 52; i++) floatOutputs.Add(i);
//        for (int i = 63; i <= 107; i++) floatOutputs.Add(i);
//        floatOutputs.Add(111);
//        floatOutputs.Add(114);
//        floatOutputs.Add(117);
//        floatOutputs.Add(120);
//        floatOutputs.Add(123);
//    }

//    IEnumerator CollectData()
//    {
//        Dictionary<int, object> results = new Dictionary<int, object>();
//        DateTime startTime = DateTime.Now;
//        int requestTime = (int)(DateTimeOffset.Now.ToUnixTimeSeconds());

//        try
//        {
//            for (int command = 1; command <= 123; command++)
//            {
//                byte[] message = BuildUDPMessage(requestTime, command);
//                try
//                {
//                    udpClient.Send(message, message.Length, serverEndPoint);
//                }
//                catch (Exception e)
//                {
//                    Debug.LogWarning($"Failed to send command {command}: {e}");
//                }
//            }

//            HashSet<int> receivedCommands = new HashSet<int>();
//            int maxAttempts = 150;

//            while (receivedCommands.Count < 123 && maxAttempts > 0)
//            {
//                try
//                {
//                    if (udpClient.Available > 0)
//                    {
//                        byte[] data = udpClient.Receive(ref serverEndPoint);
//                        ParseUDPResponse(data, results, receivedCommands);
//                    }
//                }
//                catch (SocketException)
//                {
//                    // Timeout likely
//                }
//                catch (Exception e)
//                {
//                    Debug.LogWarning($"Error receiving/parsing response: {e}");
//                }
//                maxAttempts--;
//                yield return null; // Yield to avoid freezing frame
//            }

//            // Fill missing
//            for (int command = 1; command <= 123; command++)
//            {
//                if (!results.ContainsKey(command))
//                {
//                    results[command] = null;
//                }
//            }

//            UpdateSliders(results);
//        }
//        catch (Exception e)
//        {
//            Debug.LogError($"Lost connection to UDP server or other issue: {e}");
//        }

//        TimeSpan elapsed = DateTime.Now - startTime;
//        Debug.Log($"Collect cycle took {elapsed.TotalSeconds:F3}s");
//    }

//    byte[] BuildUDPMessage(int requestTime, int command)
//    {
//        List<byte> data = new List<byte>();

//        data.AddRange(BitConverter.GetBytes(IPAddress.HostToNetworkOrder(requestTime)));
//        data.AddRange(BitConverter.GetBytes(IPAddress.HostToNetworkOrder(command)));

//        if (command >= 63 && teamNumber.HasValue)
//        {
//            byte[] teamBytes = BitConverter.GetBytes(teamNumber.Value);
//            if (BitConverter.IsLittleEndian)
//                Array.Reverse(teamBytes);
//            data.AddRange(teamBytes);
//        }

//        return data.ToArray();
//    }

//    void ParseUDPResponse(byte[] data, Dictionary<int, object> results, HashSet<int> receivedCommands)
//    {
//        if (data.Length < 8) return;

//        int serverTime = IPAddress.NetworkToHostOrder(BitConverter.ToInt32(data, 0));
//        int command = IPAddress.NetworkToHostOrder(BitConverter.ToInt32(data, 4));
//        byte[] outputData = new byte[data.Length - 8];
//        Array.Copy(data, 8, outputData, 0, outputData.Length);

//        if (!receivedCommands.Contains(command))
//        {
//            if (floatOutputs.Contains(command))
//            {
//                if (outputData.Length >= 4)
//                {
//                    if (BitConverter.IsLittleEndian)
//                        Array.Reverse(outputData);
//                    float value = BitConverter.ToSingle(outputData, 0);
//                    results[command] = value;
//                }
//            }
//            else
//            {
//                if (outputData.Length >= 4)
//                {
//                    if (BitConverter.IsLittleEndian)
//                        Array.Reverse(outputData);
//                    int value = BitConverter.ToInt32(outputData, 0) & 0xFF;
//                    results[command] = value;
//                }
//            }
//            receivedCommands.Add(command);
//        }
//    }

//    void UpdateSliders(Dictionary<int, object> results)
//    {
//        if (sliderManager == null) return;

//        foreach (var binding in sliderManager.sliders)
//        {
//            if (binding.updater == null) continue;
//            var key = binding.updater.valueKey;

//            if (int.TryParse(key, out int commandId))
//            {
//                if (results.ContainsKey(commandId) && results[commandId] != null)
//                {
//                    float value = Convert.ToSingle(results[commandId]);
//                    binding.updater.SetSliderValue(value);
//                }
//            }
//        }
//    }
//}

/**//**//**/
