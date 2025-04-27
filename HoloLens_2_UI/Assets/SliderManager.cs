using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class SliderManager : MonoBehaviour
{
    public MaxMinVals valueSource;

    [System.Serializable]
    public class SliderBinding
    {
        public string valueKey;
        public SliderUpdater updater;
    }

    public List<SliderBinding> sliders;
    void Start()
    {
        foreach (var binding in sliders)
        {
            binding.updater.Init(valueSource, binding.valueKey);
        }
    }

    public void UpdateSliderValue(string key, float value)
    {
        var binding = sliders.Find(s => s.valueKey == key);
        if (binding != null && binding.updater != null)
        {
            binding.updater.SetSliderValue(value);
        }
    }

}
