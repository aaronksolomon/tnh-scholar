import streamlit as st


def get_current_page():
    return st.session_state.pages[st.session_state.current_page_index]


def get_all_pages():
    return st.session_state.pages


def update_current_page(field, value):
    st.session_state.pages[st.session_state.current_page_index][field] = value


def reset_text_input_state():
    st.session_state.new_text_input = False


def key_exists(key):
    return key in st.session_state


def get_key_value(key):
    if key_exists(key):
        return st.session_state[key]
    else:
        None


def lookup_page_entry():
    return get_key_value("page_text_area")


def new_text_input():
    st.session_state.new_text_input = True
    save_text()


def reset_counter():
    st.session_state.counter = 0


def text_area_has_changed():
    return st.session_state.new_text_input


def save_new_page_text(text):
    update_current_page("text", text)
    update_current_page("modified", True)


def revert_page_text():
    current_page = get_current_page()
    update_current_page("text", current_page("original"))
    update_current_page("modified", False)


def is_current_page_modified():
    page = get_current_page()
    return page["modified"]


# Callback functions


def save_text():
    """
    Save the current text to the corresponding page in session state.
    """
    current_page = get_current_page()
    text = lookup_page_entry()
    if text and text_area_has_changed():
        if not is_current_page_modified():  # very first modification
            update_current_page("original", current_page["text"])
            save_new_page_text(text)
        elif (
            current_page["original"] == text
        ):  # the user has edited back to original state.
            revert_page_text()
        else:
            save_new_page_text(text)

        reset_text_input_state()


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


# Initialize session state variables
if "pages" not in st.session_state:
    st.session_state.pages = [
        {"number": 1, "text": "This is page 1.", "original": "", "modified": False},
        {"number": 2, "text": "This is page 2.", "original": "", "modified": False},
        {"number": 3, "text": "This is page 3.", "original": "", "modified": False},
    ]


if "current_page_index" not in st.session_state:
    st.session_state.current_page_index = 0

# debug option
if "counter" not in st.session_state:
    st.session_state.counter = 0

if "new_text_input" not in st.session_state:
    st.session_state.new_text_input = False

st.session_state.counter += 1

# debug option
st.write(f"app execution number {st.session_state.counter}")
st.button("reset counter", key="reset_button", on_click=reset_counter)

# Main Layout
st.title("Text Area Navigation")

# Get current page details
pages = get_all_pages()
current_page = get_current_page()

# Display current page details
st.write("")
if current_page["modified"]:
    st.write(f"Page {current_page['number']} has been modified.")

modified = current_page["modified"]
info_string = (
    f"Page {current_page['number']} of {len(pages)}. {'MODIFIED' if modified else ''}"
)
# Text area for editing page content
st.text_area(
    info_string,
    value=current_page["text"],
    height=300,
    on_change=new_text_input,
    key="page_text_area",
)

# Navigation buttons with callbacks
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    st.button("⬅️ Previous Page", on_click=navigate, args=("previous",))
with col3:
    st.button("Next Page ➡️", on_click=navigate, args=("next",))

# debug option
st.write(st.session_state)
