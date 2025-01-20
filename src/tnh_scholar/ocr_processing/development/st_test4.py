import streamlit as st


def update_text(value):  # <--- define callback function
    st.session_state.text = value


# Initialize session state
if "text" not in st.session_state:
    st.session_state.text = "original"

if st.button("show"):
    # Allow the user to modify the text
    st.text_input("Edit Text", key="text")

# Display the modified text
st.markdown(st.session_state.text)

if st.button(
    "show again", on_click=update_text, args=[st.session_state.text]
):  # <--- invoke the callback
    # Display the modified text
    st.markdown(st.session_state.text)
