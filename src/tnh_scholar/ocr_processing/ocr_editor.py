import os

import streamlit as st
from lxml import etree
from PIL import Image

# Initialize session state variables
if "current_page_index" not in st.session_state:
    st.session_state.current_page_index = 0

if "tree" not in st.session_state:
    st.session_state.tree = None

if "pages" not in st.session_state:
    st.session_state.pages = []

if "uploaded_xml_file_name" not in st.session_state:
    st.session_state.uploaded_xml_file_name = None

if "current_text" not in st.session_state:
    st.session_state.current_text = None

if "current_image" not in st.session_state:
    st.session_state.current_image = None


# Load XML file
def load_xml(file_obj):
    """
    Load an XML file from a file-like object.
    """
    try:
        tree = etree.parse(file_obj)  # Directly parse the file-like object
        return tree
    except etree.XMLSyntaxError as e:
        st.error(f"Error parsing XML file: {e}")
        return None


# Save XML file
def save_xml(tree, file_path):
    """
    Save the modified XML tree to a file.
    """
    with open(file_path, "wb") as file:
        tree.write(file, pretty_print=True, encoding="utf-8", xml_declaration=True)


# Extract page data from XML
def extract_pages(tree) -> list:
    """
    Extract page data from the XML tree.

    Args:
        tree (etree.ElementTree): Parsed XML tree.

    Returns:
        list: A list of dictionaries containing 'number' and 'text' for each page.
    """
    pages = []
    for page in tree.xpath("//page"):
        page_number = page.get("page")
        ocr_text = page.text.strip() if page.text else ""
        pages.append({"number": page_number, "text": ocr_text})
    return pages


# settings
st.set_page_config(layout="wide")

# look at state for debugging:
st.write(st.session_state)

# Sidebar file upload
st.sidebar.title("OCR Editor")
uploaded_image_file = st.sidebar.file_uploader(
    "Upload an Image", type=["jpg", "jpeg", "png", "pdf"]
)
uploaded_text_file = st.sidebar.file_uploader("Upload OCR Text File", type=["xml"])

# Directory paths (optional for advanced workflows)
st.sidebar.subheader("Optional Directories")
image_directory = st.sidebar.text_input("Image Directory", value="./images")
ocr_text_directory = st.sidebar.text_input("OCR Text Directory", value="./ocr_text")

# Main app
st.title("OCR Editor Tool")

# handle upload of text and image
if uploaded_text_file:
    if uploaded_text_file.name.endswith(".xml"):
        if st.session_state.uploaded_xml_file_name != uploaded_text_file.name:
            # Reload file if a new file is uploaded
            print(f"loading {uploaded_text_file.name}")
            st.session_state.tree = load_xml(uploaded_text_file)
            if st.session_state.tree:
                st.session_state.pages = extract_pages(st.session_state.tree)
                st.session_state.current_page_index = 0  # Reset to the first page
                st.session_state.uploaded_xml_file_name = uploaded_text_file.name
                print(f"Session tree: {st.session_state.tree}")
                print(
                    f"Uploaded XML file name: {st.session_state.uploaded_xml_file_name}"
                )
    else:
        print("Error we should not reach: unsupported file type.")
else:  # there is no active xml file so reset related state:
    st.session_state.tree = None
    st.session_state.pages = []
    st.session_state.current_page_index = 0
    st.session_state.uploaded_xml_file_name = None

if uploaded_image_file:
    # Handle uploaded image files
    st.session_state.current_image = Image.open(uploaded_image_file)

# Variables
current_page_index = st.session_state.current_page_index
pages = st.session_state.pages
current_text = pages[current_page_index]
tree = st.session_state.tree
current_image = st.session_state.current_image

# Display columns for the editor
col1, col2 = st.columns([1, 1])

# Image viewer in the left column
with col1:
    if current_image:
        st.image(current_image, caption="Uploaded Image", use_column_width=True)
    else:
        st.write("No image available.")

# Text editor and buttons in the right column
with col2:

    if pages:
        # Ensure the current page's text is in session state
        current_text = pages[current_page_index]["text"]
        if st.session_state.current_text != current_text:
            print("switched pages?")
            st.session_state.current_text = current_text

        # Dynamically update the text area based on session state
        edited_text = st.text_area(
            "Edit OCR Text",
            value=st.session_state.current_text,
            key=f"text_area_{st.session_state.current_page_index}",
            height=400,
        )

        # Button row for navigation
        col_save, col_prev, col_next = st.columns([2, 1, 1])
        with col_save:
            if st.button("Save Changes"):
                if tree:
                    # Update the XML tree with the latest content from pages
                    for idx, page in enumerate(tree.xpath("//page")):
                        page.text = st.session_state.pages[idx]["text"]

                    # Save the updated XML file
                    save_path = os.path.join(ocr_text_directory, "updated_ocr.xml")
                    save_xml(tree, save_path)
                    st.success(f"All changes saved to {save_path}")

                else:
                    # Save edited text to a .txt file
                    save_path = "updated_ocr.txt"
                    with open(save_path, "w", encoding="utf-8") as f:
                        f.write(edited_text)
                        f.write(edited_text)
                    st.success(f"Text file saved to {save_path}")

        # Left Arrow Button
        with col_prev:
            if st.button("⬅️ Previous Page"):
                # Save current page's edits to pages before navigating
                if edited_text != st.session_state.current_text:
                    st.session_state.pages[st.session_state.current_page_index][
                        "text"
                    ] = edited_text
                    st.session_state.current_text = edited_text

                # Navigate to the previous page
                if current_page_index > 0:
                    st.session_state.current_page_index -= 1
                    print(f"current page: {st.session_state.current_page_index}")
                    # st.session_state.current_text = st.session_state.pages[st.session_state.current_page_index]["text"]

        # Right Arrow Button
        with col_next:
            # Save current page's edits to pages before navigating
            if st.button("Next Page ➡️"):
                if edited_text != st.session_state.current_text:
                    st.session_state.pages[st.session_state.current_page_index][
                        "text"
                    ] = edited_text
                    st.session_state.current_text = edited_text

                if current_page_index < len(pages) - 1:
                    st.session_state.current_page_index += 1
                    print(f"current page: {st.session_state.current_page_index}")
                    # st.session_state.current_text = st.session_state.pages[st.session_state.current_page_index]["text"]

        # Display the current page number
        st.write(f"Page {current_page_index + 1} of {len(pages)}")
    else:
        st.write("Upload a text file to edit OCR text.")

st.write(st.session_state)
