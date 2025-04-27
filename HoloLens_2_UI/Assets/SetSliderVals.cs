using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class SliderUpdater : MonoBehaviour
{
    public Slider targetSlider;
    public Image fill;
    public Gradient gradient;
    private float targetValue;
    public float lerpSpeed = 5f;

    [HideInInspector] public MaxMinVals valueData;
    [HideInInspector] public string valueKey;

    private ValueRange vr;
    
    
    public void Init(MaxMinVals data, string key)
    {
        valueData = data;
        valueKey = key;

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
        if (vr == null || float.IsNaN(vr.nominal))
            return;

        float percentDiff = Mathf.Abs(currentValue - vr.nominal) / (vr.max - vr.min);
        percentDiff = Mathf.Clamp01(percentDiff);

        if (fill != null && gradient != null)
        {
            fill.color = gradient.Evaluate(percentDiff);
        }

    }
    public void SetSliderValue(float newValue)
    {
        targetValue = Mathf.Clamp(newValue, targetSlider.minValue, targetSlider.maxValue);
        UpdateFillColor(targetSlider.value);
    }

    void Update()
    {
        if (targetSlider != null)
        {
            targetSlider.value = Mathf.Lerp(targetSlider.value, targetValue, Time.deltaTime * lerpSpeed);
            UpdateFillColor(targetSlider.value);
        }
    }

}
