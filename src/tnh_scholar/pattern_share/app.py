# app.py
import os
import tempfile
from pathlib import Path
from typing import Dict, List

import git
import streamlit as st
from dotenv import load_dotenv
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings
from supabase import Client, create_client

from tnh_scholar.ai_text_processing import Prompt
from tnh_scholar.exceptions import ConfigurationError


class CredentialsManager:
    def __init__(self):
        """Initialize credentials manager with error handling."""
        try:
            self.db_credentials = self._get_db_credentials()
            self._initialize_openai_key()
        except ConfigurationError as e:
            st.error(str(e))
            st.stop()
        except Exception as e:
            st.error(f"Unexpected error during initialization: {str(e)}")
            st.stop()

    def _get_db_credentials(self):
        """
        Get Supabase credentials from secrets.
        Raises ConfigurationError if credentials are invalid.
        """
        try:
            if not hasattr(st, "secrets"):
                raise ConfigurationError(
                    "Database configuration not found. Please ensure .streamlit/secrets.toml is configured."
                )

            credentials = {
                "SUPABASE_URL": st.secrets.get("SUPABASE_URL"),
                "SUPABASE_KEY": st.secrets.get("SUPABASE_KEY"),
            }

            if not all(credentials.values()):
                raise ConfigurationError(
                    "Missing required database credentials (SUPABASE_URL, SUPABASE_KEY)"
                )

            return credentials

        except Exception as e:
            # Convert any unexpected exceptions to ConfigurationError
            raise ConfigurationError(
                f"Error loading database credentials: {str(e)}"
            ) from e

    def _initialize_openai_key(self):
        """Initialize OpenAI key with graceful fallbacks."""
        try:
            if "openai_key" in st.session_state:
                return

            # Try .env file first
            load_dotenv()
            if user_key := os.getenv("OPENAI_KEY"):
                st.session_state.openai_key = user_key
                st.success("OpenAI API key loaded from environment")
                return

            # Fallback to secrets
            if hasattr(st, "secrets"):
                if fallback_key := st.secrets.get("OPENAI_KEY"):
                    st.session_state.openai_key = fallback_key
                    st.info("Using default OpenAI API key")
                    return

            # No key found - set empty and let UI handle it
            st.session_state.openai_key = ""
            st.warning("No OpenAI API key found. Please enter your key in the sidebar.")

        except Exception as e:
            st.warning(
                f"Error initializing OpenAI key: {str(e)}. Please enter your key manually."
            )
            st.session_state.openai_key = ""

    def render_key_input(self):
        """Render OpenAI key input in the Streamlit interface."""
        st.sidebar.text_input(
            "OpenAI API Key",
            value=st.session_state.openai_key,
            key="openai_key_input",
            type="password",
            help="Enter your OpenAI API key. This will be used for all AI operations.",
            on_change=self._update_openai_key,
        )

    def _update_openai_key(self):
        """Update OpenAI key in session state."""
        st.session_state.openai_key = st.session_state.openai_key_input

    def get_credentials(self):
        """
        Get all current credentials.

        Returns:
            dict: Complete credentials including database and current OpenAI key
        """
        return {**self.db_credentials, "OPENAI_KEY": st.session_state.openai_key}

    def is_openai_key_valid(self):
        """Check if OpenAI key is present and valid."""
        return bool(
            st.session_state.openai_key
            and st.session_state.openai_key.startswith("sk-")
        )


class PatternRepository:
    """Manages pattern storage and retrieval using Supabase."""

    def __init__(self, supabase_url: str, supabase_key: str, openai_key: str):
        """Initialize with Supabase and OpenAI credentials."""
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
        self.vector_store = SupabaseVectorStore(
            self.supabase,
            self.embeddings,
            table_name="patterns",
            query_name="match_patterns",
        )

    def add_pattern(self, pattern: "Prompt") -> str:
        """Add pattern to database with embeddings."""
        # Extract frontmatter for metadata
        metadata = pattern.extract_frontmatter() or {}

        # Create embeddings from instructions
        pattern_data = {
            "content": pattern.instructions,
            "metadata": {"name": pattern.name, **metadata},
        }

        # Store in Supabase with embeddings
        ids = self.vector_store.add_texts(
            texts=[pattern.instructions], metadatas=[pattern_data["metadata"]]
        )
        return ids[0]

    def search_patterns(self, query: str, limit: int = 10) -> List[Dict]:
        """Search patterns using semantic similarity."""
        results = self.vector_store.similarity_search_with_score(query, k=limit)
        return [
            {"pattern": doc.page_content, "metadata": doc.metadata, "score": score}
            for doc, score in results
        ]


def get_credentials():
    """
    Retrieve credentials from either Streamlit secrets (production) or .env file (development).

    Returns:
        dict: Dictionary containing credentials (SUPABASE_URL, SUPABASE_KEY, OPENAI_KEY)
    """
    # Try to get credentials from Streamlit first (production)
    try:
        return {
            "SUPABASE_URL": st.secrets["SUPABASE_URL"],
            "SUPABASE_KEY": st.secrets["SUPABASE_KEY"],
            "OPENAI_KEY": st.secrets["OPENAI_KEY"],
        }
    # If not running in Streamlit cloud, load from .env
    except Exception:
        load_dotenv()
        return {
            "SUPABASE_URL": os.getenv("SUPABASE_URL"),
            "SUPABASE_KEY": os.getenv("SUPABASE_KEY"),
            "OPENAI_KEY": os.getenv("OPENAI_KEY"),
        }


def main():
    st.set_page_config(page_title="Pattern Library", layout="wide")
    st.title("AI Pattern Library")

    # Initialize repository with credentials
    credentials = get_credentials()
    repo = PatternRepository(
        credentials["SUPABASE_URL"],
        credentials["SUPABASE_KEY"],
        credentials["OPENAI_KEY"],
    )

    # Sidebar for upload
    with st.sidebar:
        st.header("Share Patterns")

        upload_type = st.radio("Upload Type", ["Single Pattern", "Git Repository"])

        if upload_type == "Single Pattern":
            if uploaded_file := st.file_uploader("Upload Pattern (.md)", type=["md"]):
                content = uploaded_file.read().decode()
                pattern = Prompt(
                    name=Path(uploaded_file.name).stem, instructions=content
                )
                if st.button("Share Pattern"):
                    pattern_id = repo.add_pattern(pattern)
                    st.success(f"Pattern shared! ID: {pattern_id}")

        else:
            repo_url = st.text_input("Git Repository URL")
            if repo_url and st.button("Import Repository"):
                with tempfile.TemporaryDirectory() as tmpdir:
                    try:
                        git.Repo.clone_from(repo_url, tmpdir)
                        pattern_files = Path(tmpdir).glob("**/*.md")

                        for file in pattern_files:
                            pattern = Prompt(
                                name=file.stem, instructions=file.read_text()
                            )
                            repo.add_pattern(pattern)

                        st.success("Repository imported successfully!")
                    except Exception as e:
                        st.error(f"Failed to import: {str(e)}")

    # Main content area
    tab1, tab2 = st.tabs(["Search Patterns", "Browse"])

    with tab1:
        if query := st.text_input("Search patterns..."):
            results = repo.search_patterns(query)
            for result in results:
                with st.expander(
                    f"{result['metadata']['name']} ({result['score']:.2f})"
                ):
                    st.markdown(result["pattern"])

    with tab2:
        # Simple pagination for browsing
        page = st.number_input("Page", min_value=1, value=1)
        patterns_per_page = 10

        patterns = (
            repo.supabase.table("patterns")
            .select("*")
            .range((page - 1) * patterns_per_page, page * patterns_per_page)
            .execute()
        )

        for pattern in patterns.data:
            with st.expander(pattern["metadata"]["name"]):
                st.markdown(pattern["content"])


if __name__ == "__main__":
    main()
