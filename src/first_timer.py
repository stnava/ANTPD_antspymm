import os
import ants
import antspyt1w
import antspymm

template_path = os.path.expanduser("~/.antspymm/PPMI_template0.nii.gz")

if os.path.exists(template_path):
    template = ants.image_read(template_path)
else:
    # Run fallback code here
    print("Template file not found. Running fallback procedure...")
    antspyt1w.get_data(force_download=True)
    antspymm.get_data(force_download=True)

print("ready for test run")
