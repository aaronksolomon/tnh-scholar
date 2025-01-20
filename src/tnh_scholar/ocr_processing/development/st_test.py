
import streamlit as st
from lxml import etree


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
def extract_pages(tree):
    """
    Extract page data from the XML tree.

    Args:
        tree (etree.ElementTree): Parsed XML tree.

    Returns:
        list: A list of dictionaries containing 'number' and 'text' for each page.
    """
    xml_pages = []
    for page in tree.xpath("//page"):
        page_number = page.get("page")
        ocr_text = page.text.strip() if page.text else ""
        xml_pages.append({"number": page_number, "text": ocr_text, "modified": False})
    return xml_pages


def reset_text_file_state():
    """
    Reset session state variables related to the uploaded text file.
    """
    st.session_state.tree = None
    st.session_state.pages = []
    st.session_state.current_page_index = 0
    st.session_state.uploaded_xml_file_name = None


def handle_uploaded_text_file(uploaded_file):
    """
    Handle the uploaded text file, resetting or updating session state variables.

    Args:
        uploaded_file: The uploaded file object from Streamlit's file_uploader.
    """
    if uploaded_file.name.endswith(".xml"):
        if st.session_state.uploaded_xml_file_name != uploaded_file.name:
            # Reload file if a new file is uploaded
            print(f"Loading {uploaded_file.name}")
            st.session_state.tree = load_xml(uploaded_file)
            if st.session_state.tree:
                st.session_state.pages = extract_pages(st.session_state.tree)
                st.session_state.current_page_index = 0  # Reset to the first page
                st.session_state.uploaded_xml_file_name = uploaded_file.name
                print(
                    f"Uploaded XML file name: {st.session_state.uploaded_xml_file_name}"
                )
    else:
        print("Error: Unsupported file type.")


def save_text_change_locally():
    new_text = st.session_state.new_text
    current_page_index = st.session_state.current_page_index
    st.session_state.pages[current_page_index]["text"] = new_text
    st.session_state.pages[current_page_index]["modified"] = True
    print(f"saved new text for page {current_page_index}.")


def handle_text_change(edited_text):
    st.session_state.text_change = True
    st.session_state.new_text = edited_text


def reset_text_change_state():
    st.session_state.text_change = False
    st.session_state.new_text = ""


def handle_prev_button():
    if st.session_state.text_change:
        save_text_change_locally()
    if st.session_state.current_page_index > 0:
        st.session_state.current_page_index -= 1
    reset_text_change_state()  # reset the text change state since moving to a new page


def handle_next_button():
    pages = st.session_state.pages
    if not pages:
        raise ValueError("pages not set.")
    if st.session_state.text_change:
        save_text_change_locally()
    if st.session_state.current_page_index < len(pages) - 1:
        st.session_state.current_page_index += 1
    reset_text_change_state()  # reset the text change state since moving to a new page


# Initialize session state variables
if "current_page_index" not in st.session_state:
    st.session_state.current_page_index = 0

if "tree" not in st.session_state:
    st.session_state.tree = None

if "pages" not in st.session_state:
    st.session_state.pages = []

if "uploaded_xml_file_name" not in st.session_state:
    st.session_state.uploaded_xml_file_name = None

if "text_change" not in st.session_state:
    st.session_state.text_change = False

if "new_text" not in st.session_state:
    st.session_state.new_text = ""

if "current_image" not in st.session_state:
    st.session_state.current_image = None

# settings
st.set_page_config(layout="wide")

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
    handle_uploaded_text_file(uploaded_text_file)
else:  # No active XML file, reset state
    reset_text_file_state()

# variables for this update round
current_page_index = st.session_state.current_page_index
pages = st.session_state.pages
if pages:
    current_text = pages[current_page_index]["text"]
else:
    current_text = ""
current_image = st.session_state.current_image

# Navigation buttons
col1, col2, col3 = st.columns([1, 2, 1])

# Display columns for the editor
col1, col2 = st.columns([1, 1])

# Image viewer in the left column
with col1:
    if current_image:
        st.image(current_image, caption="Uploaded Image", use_container_width=True)
    else:
        st.write("No image data loaded.")

with col2:
    if pages:
        col_save, col_prev, col_next = st.columns([2, 1, 1])

        with col_prev:
            if st.button("⬅️ Previous Page"):
                handle_prev_button()
        with col_next:
            if st.button("Next Page ➡️"):
                handle_next_button()

        # Get current page index
        current_page_index = st.session_state.current_page_index

        # Generate unique key for the current page's edited text
        key = f"edited_text_{current_page_index}"

        # Initialize edited text for this page in session state if not already set
        if key not in st.session_state:
            st.session_state[key] = st.session_state.pages[current_page_index]["text"]

        # Display text area, using the current page's edited text as the value
        edited_text = st.text_area(
            "Page Content",
            value=st.session_state[key],
            key=f"text_area_{current_page_index}",
            height=800,
        )

        unsaved_text_edit = False
        if (
            edited_text != pages[st.session_state.current_page_index]["text"]
        ):  # check for change in the text.
            print("TEXT CHANGE:")  # debug
            print(
                f"---CURRENT---\n>{current_text}<\n---[end]\n\n---EDITED---\n>{edited_text}<\n---[end]\n\n"
            )
            handle_text_change(edited_text)
            unsaved_text_edit = True
        modified = (
            unsaved_text_edit or pages[st.session_state.current_page_index]["modified"]
        )
        st.write(
            f"Page {st.session_state.current_page_index + 1} of {len(pages)} {'MODIFIED' if modified else ''}"
        )

    else:
        st.write("No page data loaded.")

# Debugging: Display session state
st.write("Session State:", st.session_state)

# else:
#     pages = [
#         {"number": 0, "text": "Page 0 content"},
#         {"number": 1, "text": "Page 1 content"},
#         {"number": 2, "text": "Page 2 content"}
#             ]
