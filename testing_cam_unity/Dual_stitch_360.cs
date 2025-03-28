using UnityEngine;

public class DualStitching360_TopBottom : MonoBehaviour
{
    public Renderer frontHemisphereRenderer;  // Assign Front Hemisphere Renderer
    public Renderer rearHemisphereRenderer; // Assign Rear Hemisphere Renderer
    private WebCamTexture webcamTexture;
    private Texture2D frontTexture;
    private Texture2D rearTexture;

    void Start()
    {
        WebCamDevice[] devices = WebCamTexture.devices;
        int selectedCameraIndex = -1;

        // Find the Insta360 X4
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
            selectedCameraIndex = 0;
        }

        // Start capturing with a high resolution (adjust if needed)
        webcamTexture = new WebCamTexture(devices[selectedCameraIndex].name, 2880, 2880);
        webcamTexture.Play();

        // Create textures for the front (top half) and rear (bottom half)
        frontTexture = new Texture2D(2880, 1440);
        rearTexture = new Texture2D(2880, 1440);

        // Assign textures to the hemispheres
        frontHemisphereRenderer.material.mainTexture = frontTexture;
        rearHemisphereRenderer.material.mainTexture = rearTexture;

        // Start processing frames
        InvokeRepeating("UpdateFisheyeTextures", 0, 0.03f);
    }

    void UpdateFisheyeTextures()
    {
        if (webcamTexture.didUpdateThisFrame)
        {
            // Copy the top half (front view)
            frontTexture.SetPixels(webcamTexture.GetPixels(0, 1440, 2880, 1440));
            frontTexture.Apply();

            // Copy the bottom half (rear view)
            rearTexture.SetPixels(webcamTexture.GetPixels(0, 0, 2880, 1440));
            rearTexture.Apply();
        }
    }

    void OnDestroy()
    {
        if (webcamTexture != null)
        {
            webcamTexture.Stop();
        }
    }
}
