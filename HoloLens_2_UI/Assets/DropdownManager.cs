using UnityEngine;
using UnityEngine.UI;

public class DropdownController : MonoBehaviour
{
    public GameObject dropdown; // Drag your dropdown GameObject here
    private bool isVisible = false; // To track if the dropdown is visible
    public void ToggleDropdown()
    {
        isVisible = !isVisible;
        dropdown.SetActive(isVisible);
    }
}