import streamlit as st


class Page:
    """
    Represents a single page in a document editor.

    Attributes:
        number (int): The page number.
        text (str): The current content of the page.
        original (str): The original, unmodified content of the page.
        modified (bool): Indicates if the page has been modified.
    """

    def __init__(self, number: int, text: str):
        self.number = number
        self.text = text
        self.original = text
        self.modified = False

    def save_text(self, new_text: str):
        """
        Saves new text to the page, updating the modification status.

        Args:
            new_text (str): The new text to save.
        """
        if new_text != self.text:
            if not self.modified:
                self.original = self.text
            self.text = new_text
            self.modified = new_text != self.original

    def revert_to_original(self):
        """
        Reverts the page text to its original state.
        """
        self.text = self.original
        self.modified = False

    def is_modified(self) -> bool:
        """
        Checks if the page has been modified.

        Returns:
            bool: True if the page is modified, False otherwise.
        """
        return self.modified


class DocumentEditor:
    """
    A modular document editor for managing multiple pages.

    Attributes:
        pages (list[Page]): The list of Page objects in the document.
        current_page_index (int): The index of the currently displayed page.
        debug (bool): Enables debug output when set to True.
    """

    def __init__(
        self,
        document_key,
        page_data: list,
        debug: bool = False,
    ):
        """
        Initializes the DocumentEditor with pages.

        Args:
            page_data (list): A list of Page objects or strings.
            debug (bool): Enables debug mode if True.
        """
        if all(isinstance(p, Page) for p in page_data):
            self.pages = page_data
        elif all(isinstance(p, str) for p in page_data):
            self.pages = [Page(number=i + 1, text=p) for i, p in enumerate(page_data)]
        else:
            raise ValueError("page_data must be a list of Page objects or strings.")

        self.current_page_index = 0
        self.key = document_key
        self.debug = debug

    def get_current_page(self) -> Page:
        """
        Retrieves the currently displayed page.

        Returns:
            Page: The current Page object.
        """
        return self.pages[self.current_page_index]

    def navigate(self, direction: str):
        """
        Navigates to the next or previous page.

        Args:
            direction (str): Either 'next' or 'previous'.
        """
        self.save_text()
        if direction == "next" and self.current_page_index < len(self.pages) - 1:
            self.current_page_index += 1
        elif direction == "previous" and self.current_page_index > 0:
            self.current_page_index -= 1

    def display(self):
        """
        Renders the Streamlit interface for the DocumentEditor.
        """

        # Display debug info
        if self.debug:
            st.write(f"Current Page Index: {self.current_page_index}")
            st.write("Pages State:", self.pages)

        current_page = self.get_current_page()

        # Display current page details
        st.write(
            f"Page {current_page.number} of {len(self.pages)}. {'MODIFIED' if current_page.is_modified() else ''}"
        )

        # Text area for editing page content
        new_text = st.text_area(
            label=f"Page {current_page.number} Content",
            value=current_page.text,
            height=300,
            on_change=self.save_text,
            key=f"{self.key}_document_page_area",
        )

        # Navigation buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.button("⬅️ Previous Page", on_click=self.navigate, args=("previous",))
        with col3:
            st.button("Next Page ➡️", on_click=self.navigate, args=("next",))

    # def save_text(self):
    #     """
    #     Saves the text from the current page's text area.
    #     """
    #     import streamlit as st

    #     current_page = self.get_current_page()
    #     text_key = "unknown"  # not yet implemented!!
    #     if text_key in st.session_state:
    #         new_text = st.session_state[text_key]
    #         current_page.save_text(new_text)

    def save_text(self):
        """
        Save the current text to the corresponding page in the document.
        Handles the case where the user edits the text back to the original.

        Raises:
            RuntimeError: If called without an active page loaded.
        """

        # Ensure a valid current page
        if (
            not self.pages
            or self.current_page_index < 0
            or self.current_page_index >= len(self.pages)
        ):
            raise RuntimeError("Invalid page state. No page to save.")

        # Retrieve current page and text from the text area
        current_page = self.get_current_page()
        text_key = f"{self.key}_document_page_area"
        if text_key not in st.session_state:
            return  # No text area input to process

        new_text = st.session_state[text_key]

        # Handle text saving logic
        if new_text != current_page.text:  # Text has changed
            if not current_page.modified:  # First modification
                current_page.original = current_page.text
                current_page.text = new_text
                current_page.modified = True
            elif new_text == current_page.original:  # Edited back to the original state
                current_page.text = current_page.original
                current_page.modified = False
            else:  # Further modifications
                current_page.text = new_text
                current_page.modified = True
