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
}
