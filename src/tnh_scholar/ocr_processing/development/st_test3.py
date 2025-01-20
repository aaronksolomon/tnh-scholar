import streamlit as st

# Initialize session state variables
if "pages" not in st.session_state:
    st.session_state.pages = [
        {"number": 1, "text": "This is page 1.", "modified": False},
        {"number": 2, "text": "This is page 2.", "modified": False},
        {"number": 3, "text": "This is page 3.", "modified": False},
    ]
if "current_page_index" not in st.session_state:
    st.session_state.current_page_index = 0

if "counter" not in st.session_state:
    st.session_state.counter = 0

if "text_tracker" not in st.session_state:
    st.session_state.text_tracker = ""

st.session_state.counter += 1

st.write(f"app execution number {st.session_state.counter}")


# Callback functions
def save_text():
    """
    Save the current text to the corresponding page in session state.
    """
    current_page_index = st.session_state.current_page_index
    key = f"edited_text_{current_page_index}"
    if key in st.session_state:
        new_text = st.session_state[key]
        if st.session_state.pages[current_page_index]["text"] != new_text:
            st.session_state.pages[current_page_index]["text"] = new_text
            st.session_state.pages[current_page_index]["modified"] = True


def navigate(direction):
    """
    Save the current page's text and navigate to the specified direction.
    """
    save_text()
    if (
        direction == "next"
        and st.session_state.current_page_index < len(st.session_state.pages) - 1
    ):
        st.session_state.current_page_index += 1
    elif direction == "previous" and st.session_state.current_page_index > 0:
        st.session_state.current_page_index -= 1


# Main Layout
st.title("Dynamic Text Area Navigation with Callbacks")

# Get current page details
current_page_index = st.session_state.current_page_index
pages = st.session_state.pages
current_page = pages[current_page_index]

# Display current page details
st.write(f"Page {current_page['number']} of {len(pages)}")
if current_page["modified"]:
    st.write(f"Page {current_page['number']} has been modified.")

f"before text: {st.session_state.current_page_index}"
# Text area for editing page content
text_out = st.text_area(
    "Page Content",
    value=current_page["text"],
    height=300,
    key=f"edited_text_{current_page_index}",
)
if text_out != st.session_state.text_tracker:
    st.session_state.text_tracker = text_out
    "text_tracker updated."
f"current value of text_tracker: {st.session_state.text_tracker}"

# Navigation buttons with callbacks
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    st.button("⬅️ Previous Page", on_click=navigate, args=("previous",))
with col3:
    st.button("Next Page ➡️", on_click=navigate, args=("next",))

f"before nav: {st.session_state.current_page_index}"
