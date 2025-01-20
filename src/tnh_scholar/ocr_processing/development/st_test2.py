import streamlit as st

# Preloaded text data (simulates pages)
pages = ["a", "Page 2 content", "Page 3 content"]

# Initialize session state variables
if "current_page_index" not in st.session_state:
    st.session_state.current_page_index = 0

# Navigation buttons
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    if st.button("⬅️ Previous Page"):
        if st.session_state.current_page_index > 0:
            st.session_state.current_page_index -= 1

with col3:
    if st.button("Next Page ➡️"):
        if st.session_state.current_page_index < len(pages) - 1:
            st.session_state.current_page_index += 1

# Display the current page number and content
st.write(f"Page {st.session_state.current_page_index + 1} of {len(pages)}")
st.text_area(
    "Page Content",
    value=pages[st.session_state.current_page_index],
    key=f"text_area_{st.session_state.current_page_index}",
    height=200,
)

# Debugging: Display session state
st.write("Session State:", st.session_state)
