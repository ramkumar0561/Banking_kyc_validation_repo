import os
import pandas as pd
from PIL import Image, ImageDraw

# --- 1. DATA SETUP (5 Aadhar + 5 PAN) ---
# This is your "Truth" data for testing.
profiles = [
    ["Aadhar", "Aarav Sharma", "12/04/1990", "Male", "9182 7364 5091"],
    ["Aadhar", "Ishani Verma", "25/11/1995", "Female", "1029 3847 5610"],
    ["Aadhar", "Rohan Deshmukh", "08/02/1982", "Male", "5566 7788 9900"],
    ["Aadhar", "Meera Iyer", "14/07/1988", "Female", "1122 3344 5566"],
    ["Aadhar", "Arjun Kapoor", "30/09/1975", "Male", "9988 7766 5544"],
    ["PAN", "Aarav Sharma", "12/04/1990", "Male", "BRVPS1234A"],
    ["PAN", "Ishani Verma", "25/11/1995", "Female", "CTVPI5678B"],
    ["PAN", "Rohan Deshmukh", "08/02/1982", "Male", "DLKPR9012C"],
    ["PAN", "Meera Iyer", "14/07/1988", "Female", "EMPWI3456D"],
    ["PAN", "Arjun Kapoor", "30/09/1975", "Male", "FNPWK7890E"]
]

# Create a folder for your project files
output_dir = "PROJECT_TEST_DATA"
os.makedirs(output_dir, exist_ok=True)


# --- 2. HELPER FUNCTIONS ---
def create_aadhar_template(width=1000, height=600):
    """Creates a background that looks like a real Aadhar card."""
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Header
    draw.rectangle([0, 0, width, 100], fill=(178, 34, 34))  # Dark red
    draw.text((400, 40), "भारत सरकार / GOVERNMENT OF INDIA", fill=(255, 255, 255))
    # Photo placeholder
    draw.rectangle([50, 150, 300, 450], outline=(0, 0, 0), width=2)
    draw.text((120, 280), "PHOTO", fill=(150, 150, 150))
    # Bottom emblem
    draw.ellipse([450, 500, 550, 580], outline=(0, 0, 0), width=2)
    return img


def create_pan_template(width=1000, height=600):
    """Creates a background that looks like a real PAN card."""
    img = Image.new('RGB', (width, height), color=(200, 230, 200))  # Light green
    draw = ImageDraw.Draw(img)
    # Header
    draw.rectangle([0, 0, width, 80], fill=(0, 100, 0))  # Dark green
    draw.text((300, 30), "INCOME TAX DEPARTMENT / आयकर विभाग", fill=(255, 255, 255))
    # Photo placeholder
    draw.rectangle([50, 120, 250, 320], outline=(0, 0, 0), width=2)
    draw.text((100, 200), "PHOTO", fill=(100, 100, 100))
    return img


def add_text_to_card(img, type, name, dob, gender_or_pan, id_num):
    """Overlays the profile data onto the correct positions."""
    draw = ImageDraw.Draw(img)

    if type == "Aadhar":
        # Aadhar Layout
        draw.text((350, 180), f"Name: {name}", fill=(0, 0, 0))
        draw.text((350, 240), f"DOB: {dob}", fill=(0, 0, 0))
        draw.text((350, 300), f"Gender: {gender_or_pan}", fill=(0, 0, 0))
        # Aadhar Number is large and at the bottom
        draw.text((350, 480), f"{id_num}", fill=(0, 0, 0))
    else:
        # PAN Layout
        draw.text((300, 150), "Name", fill=(50, 50, 50))
        draw.text((300, 180), name.upper(), fill=(0, 0, 0))  # PAN names are usually uppercase
        draw.text((300, 250), "Date of Birth", fill=(50, 50, 50))
        draw.text((300, 280), dob, fill=(0, 0, 0))
        # PAN Number is in a specific box
        draw.rectangle([300, 350, 700, 420], outline=(0, 0, 0), width=1)
        draw.text((320, 370), "Permanent Account Number", fill=(50, 50, 50))
        draw.text((350, 390), id_num, fill=(0, 0, 0))

    # Add a 'SPECIMEN' watermark for clarity
    draw.text((50, 50), "SPECIMEN FOR TESTING", fill=(200, 200, 200))


# --- 3. MAIN EXECUTION ---
print(f"Starting... files will be created in: {os.path.abspath(output_dir)}")

# Generate images
for i, (type, name, dob, gender, id_num) in enumerate(profiles):
    # 1. Create base template
    if type == "Aadhar":
        card_img = create_aadhar_template()
    else:
        card_img = create_pan_template()

    # 2. Add profile data
    add_text_to_card(card_img, type, name, dob, gender, id_num)

    # 3. Save image
    filename = f"{type.lower()}_{i + 1}.png"
    card_img.save(os.path.join(output_dir, filename))
    print(f"Generated: {filename}")

# Generate Excel file
df = pd.DataFrame(profiles, columns=["Type", "Name", "DOB", "Gender", "ID Number"])
try:
    df.to_excel(os.path.join(output_dir, "test_data_registry.xlsx"), index=False)
    print("\nSUCCESS! Excel file 'test_data_registry.xlsx' created successfully.")
except ModuleNotFoundError:
    # Fallback to CSV if openpyxl is still an issue
    df.to_csv(os.path.join(output_dir, "test_data_registry.csv"), index=False)
    print("\n'openpyxl' library not found. Saved as CSV instead. (Run 'pip install openpyxl' for Excel)")

print(f"\nAll 10 realistic specimen cards and the data file are ready in the '{output_dir}' folder.")