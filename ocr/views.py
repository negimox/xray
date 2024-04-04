import base64
# IDK
import re

import cv2
import numpy as np
import pytesseract
from PIL import Image
from django.contrib import messages
from django.shortcuts import render

# import pathlib
# import textwrap
#
# import google.generativeai as genai


pytesseract.pytesseract.tesseract_cmd = (
    r"/usr/bin/tesseract"
)


def homepage(request):
    if request.method == "POST":
        try:
            image = request.FILES["imagefile"]
            # encode image to base64 string
            image_base64 = base64.b64encode(image.read()).decode("utf-8")
        except:
            messages.add_message(
                request, messages.ERROR, "No image selected or uploaded"
            )
            return render(request, "home.html")
        # lang = request.POST["language"]
        img = np.array(Image.open(image))

        # Convert the image to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Perform OCR on the image
        text = pytesseract.image_to_string(gray, lang="eng")
        parts = text.split("\n")
        #
        info = {"Name": "", "Gender": True, "DOB": ""}
        print(parts)

        # Extracting name
        clean_text = text.strip("[]'\"").replace("\\", "")
        match = extract_name(clean_text)
        if match:
            info["Name"] = match

        #
        for index, line in enumerate(parts):
            item = line.strip()
            split_item = item.split()
            has_digit = any(i.isdigit() for i in item)
            # search_dob(line.split(), item)
            if item.startswith("Name:") and info["Name"] == "":
                info["Name"] = item[len("Name:"):].strip().split("\n")[0]
            elif "Male" in item:
                info["Gender"] = True
            elif "Female" in item:
                info["Gender"] = False
            elif has_digit and info["DOB"] == "":
                dob = search_dob(split_item)
                if dob is not None:
                    info["DOB"] = dob

        # print(parts)
        print(info)

        # return text to html
        return render(request, "home.html",
                      {"image": image_base64, "info": info, "gender": info["Gender"], "dob": info["DOB"],
                       "name": info["Name"].capitalize()})

    return render(request, "home.html")


def search_dob(split_item):
    for i in split_item:
        name_patterns = [
            r'^\d{2}/\d{2}/\d{4}$',
            r'^\d{2}-\d{2}-\d{4}$',
            r'^\d{4}/\d{2}/\d{2}$',
            r'^\d{4}-\d{2}-\d{2}$'
        ]

        for index_pattern, pattern in enumerate(name_patterns):
            date_regex = re.compile(pattern)
            is_date = bool(date_regex.match(i))
            if is_date:
                temp = i.split("/") if index_pattern % 2 == 0 else i.split("-")
                # print(temp)
                if index_pattern == 0 or index_pattern == 1:
                    day = temp[0]
                    month = temp[1]
                    year = temp[2]
                else:
                    year = temp[0]
                    month = temp[1]
                    day = temp[2]
                dob = year + "-" + month + "-" + day
                # print(dob)
                return dob


def extract_name(text):
    """
  Extracts the name from OCR text using regular expressions and heuristics.

  Args:
      text: The OCR output as a string.

  Returns:
      The extracted name or None if not found.
  """
    # Split the text by lines
    lines = text.strip("[]").split("\n")

    # Heuristic 1: Look for lines starting with uppercase followed by spaces
    for line in lines:
        if line.isupper() and any(c.isspace() for c in line):
            return line.strip()

    # Heuristic 2: Look for lines containing "DOB :" followed by potential name
    for i, line in enumerate(lines):
        if "DOB :" in line:
            potential_name = lines[i - 1].strip()
            if re.match(r"[A-Z][a-z]+ [A-Z][a-z]+", potential_name):  # Check for two names
                return potential_name

    # Regular expression for common name formats (modify as needed)
    name_patterns = [
        r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b',  # Matches "First Last" format
        r'\b[A-Z]+\s[A-Z]+\b'  # Matches "ALL CAPS" format
    ]

    for pattern in name_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)

    # Name not found in any of the cases
    return None
