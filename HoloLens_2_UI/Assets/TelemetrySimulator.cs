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
