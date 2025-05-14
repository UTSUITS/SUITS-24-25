using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class SliderManager : MonoBehaviour
{
    public MaxMinVals valueSource;

    [System.Serializable]
    public class SliderBinding
    {
        public string valueKey;
        public SliderUpdater updater;
        public GameObject actionButton;  
    }

    public List<SliderBinding> sliders;
    void Start()
    {
        foreach (var binding in sliders)
        {
            binding.updater.Init(valueSource, binding.valueKey);

            if (binding.actionButton != null)
            {
                // Find "ButtonContent/Label" inside the action button
                var sublabelTransform = binding.actionButton.transform.Find("Frontplate/AnimatedContent/Subtext");

                if (sublabelTransform != null)
                {
                    var textComponent = sublabelTransform.GetComponent<TMPro.TMP_Text>();
                    if (textComponent != null)
                    {
                        textComponent.text = binding.valueKey;
                        textComponent.fontSize = 6.0f;

                        Color color = textComponent.color;
                        color.a = 0.88f;
                        textComponent.color = color;
                    }
                    else
                    {
                        Debug.LogWarning("TMP_Text component missing on Label object in: " + binding.actionButton.name);
                    }
                }
                else
                {
                    Debug.LogWarning("ButtonContent/Label path not found in: " + binding.actionButton.name);
                }
            }
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
