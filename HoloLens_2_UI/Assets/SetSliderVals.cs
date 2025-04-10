using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class SliderUpdater : MonoBehaviour
{
    public Slider targetSlider;
    public MaxMinVals valueData;
    public string valueKey;
    public Image fill;

    [Header("Color settings")]
    public Gradient gradient;
    

    private ValueRange vr;
    void Start()
    {
        if (valueData == null || !valueData.valueRanges.ContainsKey(valueKey))
        {
            Debug.LogWarning("Value or data missing.");
            return;
        }
        vr = valueData.valueRanges[valueKey];

        targetSlider.minValue = vr.min;
        targetSlider.maxValue = vr.max;

        float startValue = float.IsNaN(vr.nominal) ? vr.min : vr.nominal;
        targetSlider.value = startValue;

        UpdateFillColor(targetSlider.value);

        targetSlider.onValueChanged.AddListener(UpdateFillColor);
    }

    void UpdateFillColor(float currentValue)
    {
        if (float.IsNaN(vr.nominal))
            return;

        float percentDiff = Mathf.Abs(currentValue - vr.nominal) / (vr.max - vr.min);
        percentDiff = Mathf.Clamp01(percentDiff);

        if (fill != null && gradient != null)
        {
            fill.color = gradient.Evaluate(percentDiff);
        }

    }
    void Update()
    {
        //fill.color = gradient.Evaluate(targetSlider.normalizedValue);
    }
 
}
