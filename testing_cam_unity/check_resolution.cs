using UnityEngine;

public class CheckWebcamResolution : MonoBehaviour
{
    void Start()
    {
        WebCamDevice[] devices = WebCamTexture.devices;
        for (int i = 0; i < devices.Length; i++)
        {
            Debug.Log($"Webcam {i}: {devices[i].name}");
        }

        // Check Insta360 X4 (Assuming it's the second webcam, adjust index if needed)
        WebCamTexture webcamTexture = new WebCamTexture(devices[1].name, 2880, 1440);
        Debug.Log($"Selected Camera: {devices[1].name}, Resolution: {webcamTexture.width}x{webcamTexture.height}");
    }
}
