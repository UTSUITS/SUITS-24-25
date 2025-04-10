using System.Collections;
using System.Collections.Generic;
using UnityEngine;

[System.Serializable]
public class ValueRange
{
    public float max;
    public float min;
    public float nominal;
    public string label;

    public ValueRange(string label, float min, float nominal, float max)
    {
        this.label = label;
        this.nominal = nominal;
        this.max = max;
        this.min = min;
    }
}


public class MaxMinVals : MonoBehaviour
{
    public Dictionary<string, ValueRange> valueRanges = new Dictionary<string, ValueRange>();

    void Awake()
    {
        //Suit Resources
        valueRanges.Add("batt_time_left", new ValueRange("Battery time left in seconds", 3600f, float.NaN, 10800f));
        valueRanges.Add("oxy_pri_storage", new ValueRange("Oxygen storage in primary tank in % full", 20f, float.NaN, 100f));
        valueRanges.Add("oxy_sec_storage", new ValueRange("Oxygen storage in secondary tank in % full", 20f, float.NaN, 100f));
        valueRanges.Add("oxy_pri_pressure", new ValueRange("Oxygen pressure in primary tank in psi", 600f, float.NaN, 3000f));
        valueRanges.Add("oxy_sec_pressure", new ValueRange("Oxygen pressure in secondary tank in psi", 600f, float.NaN, 3000f));
        valueRanges.Add("oxy_time_left", new ValueRange("Time left with oxygen supply in seconds", 3600f, float.NaN, 21600f));
        valueRanges.Add("coolant_storage", new ValueRange("Coolant in storage in % full", 80f, 100f, 100f));
        
        //Suit Atmosphere
        valueRanges.Add("heart_rate", new ValueRange("Heart rate in bpm", 50f, 90f, 160f));
        valueRanges.Add("oxy_consumption", new ValueRange("Oxygen consumption in psi/min", 0.05f, 0.1f, 0.15f));
        valueRanges.Add("co2_production", new ValueRange("CO2 production in psi/min", 0.05f, 0.1f, 0.15f));
        valueRanges.Add("suit_pressure_oxy", new ValueRange("Oxygen pressure in spacesuit in psi", 3.5f, 4.0f, 4.1f));
        valueRanges.Add("suit_pressure_co2", new ValueRange("CO2 pressure in spacesuit in psi", 0.0f, 0.0f, 0.1f));
        valueRanges.Add("suit_pressure_other", new ValueRange("Pressure of other gasses in spacesuit in psi", 0.0f, 0.0f, 0.5f));
        valueRanges.Add("suit_pressure_total", new ValueRange("Total pressure of spacesuit in psi", 3.5f, 4.0f, 4.5f));
        valueRanges.Add("helmet_pressure_co2", new ValueRange("Pressure of CO2 in helmet in psi", 0.0f, 0.1f, 0.15f));
        
        //Suit Helmet Fan
        valueRanges.Add("fan_pri_rpm", new ValueRange("Primary fan speed in rpm", 20000f, 30000f, 30000f));
        valueRanges.Add("fan_sec_rpm", new ValueRange("Secondary fan speed in rpm", 20000f, 30000f, 30000f));
        
        //Suit CO2 Scrubbers
        valueRanges.Add("scrubber_a_co2_storage", new ValueRange("CO2 in scrubber a storage in % full", 0.0f, float.NaN, 60f));
        valueRanges.Add("scrubber_b_co2_storage", new ValueRange("CO2 in scrubber b storage in % full", 0.0f, float.NaN, 60f));
        
        // Suit Temperature 
        valueRanges.Add("temperature", new ValueRange("Spacesuit temperature in degrees F", 50f, 70f, 90f));
        valueRanges.Add("coolant_liquid_pressure", new ValueRange("Spacesuit liquid coolant pressure in psi", 100f, 500f, 700f));
        valueRanges.Add("coolant_gas_pressure", new ValueRange("Spacesuit gas coolant pressure in psi", 0.0f, 0.0f, 700f));

        //foreach (KeyValuePair<string, ValueRange> entry in valueRanges)
        //{
        //    string key = entry.Key;
        //    ValueRange vr = entry.Value;

        //    string nominalDisplay = float.IsNaN(vr.nominal) ? "NaN" : vr.nominal.ToString("F2");

        //    Debug.Log($"Key: {key}\n  Label: {vr.label}\n  Min: {vr.min}\n  Nominal: {nominalDisplay}\n  Max: {vr.max}\n");
        //}
    }
}
