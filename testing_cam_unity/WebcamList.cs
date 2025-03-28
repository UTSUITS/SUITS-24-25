using UnityEngine;

public class WebcamList : MonoBehaviour
{
    void Start()
    {
        foreach (var device in WebCamTexture.devices)
        {
            Debug.Log("Webcam detected: " + device.name);
        }
    }
}
