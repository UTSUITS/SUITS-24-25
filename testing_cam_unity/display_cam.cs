using UnityEngine;

public class WebcamDeviceSelector : MonoBehaviour
{
    void Start()
    {
        WebCamDevice[] devices = WebCamTexture.devices;

        for (int i = 0; i < devices.Length; i++)
        {
            Debug.Log($"Webcam {i}: {devices[i].name}");
        }
    }
}
