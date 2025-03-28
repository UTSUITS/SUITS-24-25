using UnityEngine;
using UnityEngine.UI;

public class Webcam360Panoramic : MonoBehaviour
{
    public Renderer sphereRenderer;  // Assign the Sphere's Renderer in Inspector
    private WebCamTexture webcamTexture;

    void Start()
    {
        WebCamDevice[] devices = WebCamTexture.devices;

        int selectedCameraIndex = -1;
        for (int i = 0; i < devices.Length; i++)
        {
            Debug.Log($"Webcam {i}: {devices[i].name}");
            if (devices[i].name.Contains("Insta360"))
            {
                selectedCameraIndex = i;
                break;
            }
        }

        if (selectedCameraIndex == -1)
        {
            Debug.LogError("Insta360 X4 not found! Defaulting to first webcam.");
            selectedCameraIndex = 0; // Use default webcam
        }

        // Set Insta360 X4 to 2:1 panoramic output resolution
        webcamTexture = new WebCamTexture(devices[selectedCameraIndex].name, 2880, 1440);
        sphereRenderer.material.mainTexture = webcamTexture;
        webcamTexture.Play();
    }

    void OnDestroy()
    {
        if (webcamTexture != null)
        {
            webcamTexture.Stop();
        }
    }
}
