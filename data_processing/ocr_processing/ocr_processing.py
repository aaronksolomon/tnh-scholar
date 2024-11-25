import os
import io
from typing import List, Tuple
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF for PDF processing
from google.cloud import vision
from google.cloud.vision_v1.types import EntityAnnotation, BoundingPoly
from google.auth.credentials import Credentials
import json
from pathlib import Path
import base64
import warnings

DEFAULT_ANNOTATION_FONT_PATH = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
DEFAULT_ANNOTATION_FONT_SIZE = 12 # default annotation font size
DEFAULT_ANNOTATION_OFFSET = 2  # pixels to offset annotation labels in labeled images
DEFAULT_ANNOTATION_LANGUAGE_HINTS = ['vi'] 
DEFAULT_ANNOTATION_METHOD = "DOCUMENT_TEXT_DETECTION"

class PDFParseWarning(Warning):
    """
    Custom warning class for PDF parsing issues.
    """
    pass

def start_image_annotator_client(
    credentials_file: str = None,
    api_endpoint: str = "vision.googleapis.com",
    timeout: Tuple[int, int] = (10, 30),
    enable_logging: bool = False
) -> vision.ImageAnnotatorClient:
    """
    Starts and returns a Google Vision API ImageAnnotatorClient with optional configuration.

    Parameters:
        credentials_file (str): Path to the credentials JSON file. If None, uses the default environment variable.
        api_endpoint (str): Custom API endpoint for the Vision API. Default is the global endpoint.
        timeout (Tuple[int, int]): Connection and read timeouts in seconds. Default is (10, 30).
        enable_logging (bool): Enable detailed logging for debugging. Default is False.

    Returns:
        vision.ImageAnnotatorClient: Configured Vision API client.

    Raises:
        FileNotFoundError: If the specified credentials file is not found.
        Exception: For unexpected errors during client setup.

    Example:
        >>> client = start_image_annotator_client(
        >>>     credentials_file="/path/to/credentials.json",
        >>>     api_endpoint="vision.googleapis.com",
        >>>     timeout=(10, 30),
        >>>     enable_logging=True
        >>> )
        >>> print("Google Vision API client initialized.")
    """
    try:
        # Set up credentials
        if credentials_file:
            if not os.path.exists(credentials_file):
                raise FileNotFoundError(f"Credentials file '{credentials_file}' not found.")
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_file

        # Configure client options
        client_options = {"api_endpoint": api_endpoint}
        client = vision.ImageAnnotatorClient(client_options=client_options)

        # Optionally enable logging
        if enable_logging:
            print(f"Vision API Client started with endpoint: {api_endpoint}")
            print(f"Timeout settings: Connect={timeout[0]}s, Read={timeout[1]}s")

        return client

    except Exception as e:
        raise Exception(f"Failed to initialize ImageAnnotatorClient: {e}")
    
def load_pdf_pages(pdf_path: Path) -> fitz.Document:
    """
    Opens the PDF document and returns the fitz Document object.

    Parameters:
        pdf_path (Path): The path to the PDF file.

    Returns:
        fitz.Document: The loaded PDF document.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the file is not a valid PDF document.
        Exception: For any unexpected error.

    Example:
        >>> from pathlib import Path
        >>> pdf_path = Path("/path/to/example.pdf")
        >>> try:
        >>>     pdf_doc = load_pdf_pages(pdf_path)
        >>>     print(f"PDF contains {pdf_doc.page_count} pages.")
        >>> except Exception as e:
        >>>     print(f"Error loading PDF: {e}")
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"The file '{pdf_path}' does not exist.")

    if not pdf_path.suffix.lower() == ".pdf":
        raise ValueError(f"The file '{pdf_path}' is not a valid PDF document (expected '.pdf').")

    try:
        return fitz.open(str(pdf_path))  # PyMuPDF expects a string path
    except Exception as e:
        raise Exception(f"An unexpected error occurred while opening the PDF: {e}")


def extract_images_from_page(page: fitz.Page) -> bytes:
    """
    Extracts the first image from the given PDF page.

    Parameters:
        page (fitz.Page): The PDF page object.

    Returns:
        bytes: The raw byte content of the first image on the page.

    Raises:
        ValueError: If no images are found on the page.
        IndexError: If the image reference cannot be retrieved.
        Exception: For unexpected errors during image extraction.

    Example:
        >>> import fitz
        >>> doc = fitz.open("/path/to/document.pdf")
        >>> page = doc.load_page(0)  # Load the first page
        >>> try:
        >>>     image_bytes = extract_images_from_page(page)
        >>>     print(f"Extracted {len(image_bytes)} bytes from the image.")
        >>> except Exception as e:
        >>>     print(f"Error extracting image: {e}")
    """
    try:
        images = page.get_images(full=True)
        if not images:
            raise ValueError("No images found on the page.")

        xref = images[0][0]  # Get the first image reference
        base_image = page.parent.extract_image(xref)

        if "image" not in base_image:
            raise ValueError("The extracted image data is incomplete.")

        return base_image["image"]  # Get the raw JPEG byte content
    except ValueError as ve:
        raise ve  # Re-raise the ValueError for calling functions to handle.
    except IndexError as ie:
        raise IndexError("Failed to retrieve the image reference.") from ie
    except Exception as e:
        raise Exception(f"An unexpected error occurred during image extraction: {e}")


def annotate_image_with_text(image_bytes: bytes, 
                             text_annotations: List[vision.EntityAnnotation], 
                             annotation_font_path: str, 
                             font_size: int = DEFAULT_ANNOTATION_FONT_SIZE) -> Image.Image:
    """
    Annotates an image with bounding boxes and text descriptions from OCR results.

    Parameters:
        image_bytes (bytes): The raw byte content of the image.
        text_annotations (List[vision.EntityAnnotation]): OCR results containing bounding boxes and text.
        annotation_font_path (str): Path to the font file.
        font_size (int): Font size for text annotations.

    Returns:
        Image.Image: The annotated image.

    Raises:
        ValueError: If image_bytes is empty or None.
        OSError: If the image cannot be opened or processed.
        IOError: If the font file cannot be loaded.
        Exception: For any other unexpected errors.

    Example:
        >>> from google.cloud import vision
        >>> import io
        >>> from PIL import Image
        >>> # Example image bytes and annotations (replace with actual data)
        >>> image_bytes = open("/path/to/image.jpg", "rb").read()
        >>> text_annotations = [
        >>>     vision.EntityAnnotation(
        >>>         description="Example Text",
        >>>         bounding_poly=vision.BoundingPoly(
        >>>             vertices=[vision.Vertex(x=10, y=10), vision.Vertex(x=100, y=10),
        >>>                       vision.Vertex(x=100, y=50), vision.Vertex(x=10, y=50)]
        >>>         )
        >>>     )
        >>> ]
        >>> try:
        >>>     annotated_image = annotate_image_with_text(image_bytes, text_annotations, "/path/to/font.ttf", 15)
        >>>     annotated_image.show()
        >>> except Exception as e:
        >>>     print(f"Error during annotation: {e}")
    """
    if not image_bytes:
        raise ValueError("The image_bytes parameter is empty or None.")
    
    try:
        pil_image = Image.open(io.BytesIO(image_bytes))
    except OSError as e:
        raise OSError(f"Failed to open the image: {e}")

    try:
        font = ImageFont.truetype(annotation_font_path, font_size)
    except IOError as e:
        raise IOError(f"Failed to load the font from '{annotation_font_path}': {e}")

    draw = ImageDraw.Draw(pil_image)

    try:
        for i, text_obj in enumerate(text_annotations):
            vertices = [(vertex.x, vertex.y) for vertex in text_obj.bounding_poly.vertices]
            if len(vertices) == 4:  # Ensure there are exactly 4 vertices for a rectangle
                draw.polygon(vertices, outline="red", width=2)
                if i > 0:  # Skip the first bounding box (whole text region)
                    # Offset the text position by DEFAULT_ANNOTATION_OFFSET pixels
                    text_position = (vertices[0][0] + DEFAULT_ANNOTATION_OFFSET, 
                                     vertices[0][1] + DEFAULT_ANNOTATION_OFFSET)
                    draw.text(text_position, text_obj.description, fill="red", font=font)
    except AttributeError as e:
        raise ValueError(f"Invalid text annotation structure: {e}")
    except Exception as e:
        raise Exception(f"An error occurred during image annotation: {e}")

    return pil_image

def get_page_dimensions(page: fitz.Page) -> dict:
    """
    Extracts the width and height of a single PDF page in both inches and pixels.

    Args:
        page (fitz.Page): A single PDF page object from PyMuPDF.

    Returns:
        dict: A dictionary containing the width and height of the page in inches and pixels.
    """
    # Get page dimensions in points and convert to inches
    page_width_pts, page_height_pts = page.rect.width, page.rect.height
    page_width_in = page_width_pts / 72  # Convert points to inches
    page_height_in = page_height_pts / 72
    
    # Extract the first image on the page (if any) to get pixel dimensions
    images = page.get_images(full=True)
    if images:
        xref = images[0][0]
        base_image = page.parent.extract_image(xref)
        width_px = base_image["width"]
        height_px = base_image["height"]
    else:
        width_px, height_px = None, None  # No image found on the page

    # Return dimensions
    return {
        "width_in": page_width_in,
        "height_in": page_height_in,
        "width_px": width_px,
        "height_px": height_px
    }

def process_single_image(image_bytes: bytes, 
                         client: vision.ImageAnnotatorClient, 
                         feature_type: str = DEFAULT_ANNOTATION_METHOD, 
                         language_hints: List = DEFAULT_ANNOTATION_LANGUAGE_HINTS) -> List[vision.EntityAnnotation]:
    """
    Processes a single image with the Google Vision API and returns text annotations.

    Parameters:
        image_bytes (bytes): Raw bytes of the image.
        client (vision.ImageAnnotatorClient): Google Vision API client for text detection.
        feature_type (str): Type of text detection to use ('TEXT_DETECTION' or 'DOCUMENT_TEXT_DETECTION').

    Returns:
        List[vision.EntityAnnotation]: Text annotations from the Vision API response.

    Raises:
        ValueError: If no text is detected.
    """
    # Map feature type
    feature_map = {
        "TEXT_DETECTION": vision.Feature.Type.TEXT_DETECTION,
        "DOCUMENT_TEXT_DETECTION": vision.Feature.Type.DOCUMENT_TEXT_DETECTION,
    }
    if feature_type not in feature_map:
        raise ValueError(f"Invalid feature type '{feature_type}'. Use 'TEXT_DETECTION' or 'DOCUMENT_TEXT_DETECTION'.")

    # Prepare Vision API request
    image = vision.Image(content=image_bytes)
    features = [vision.Feature(type=feature_map[feature_type])]
    image_context = vision.ImageContext(language_hints=language_hints)

    # Make the API call
    response = client.annotate_image({
        "image": image,
        "features": features,
        "image_context": image_context,
    })
    
    if not response:
        raise ValueError("No Response from image processing!")
    return response

def process_page(page: fitz.Page, 
                 client: vision.ImageAnnotatorClient, 
                 annotation_font_path: str) -> Tuple[str, List[vision.EntityAnnotation], Image.Image, Image.Image, dict]:
    """
    Processes a single PDF page, extracting text, word locations, and annotated images.

    Parameters:
        page (fitz.Page): The PDF page object.
        client (vision.ImageAnnotatorClient): Google Vision API client for text detection.
        annotation_font_path (str): Path to the font file for annotations.

    Returns:
        Tuple[str, List[vision.EntityAnnotation], Image.Image, Image.Image, dict]: Full page text, word locations,
        annotated image, and unannotated image, page_dimensions
    """
    image_bytes = extract_images_from_page(page)
    unannotated_image = Image.open(io.BytesIO(image_bytes)).copy()

    # Annotate image with Vision API
    response = process_single_image(image_bytes, client)
    text_annotations = response.text_annotations

    full_page_text = text_annotations[0].description  # First element is the full page text
    word_locations = text_annotations[1:]  # Remaining elements are word locations

    annotated_image = annotate_image_with_text(image_bytes, text_annotations, annotation_font_path)
    page_dimensions =  get_page_dimensions(page)

    return full_page_text, word_locations, annotated_image, unannotated_image, page_dimensions

def build_processed_pdf(
    pdf_path: Path,
    client: vision.ImageAnnotatorClient,
    annotation_font_path: Path = DEFAULT_ANNOTATION_FONT_PATH
) -> Tuple[List[str], List[List[vision.EntityAnnotation]], List[Image.Image], List[Image.Image]]:
    """
    Processes a PDF document, extracting text, word locations, annotated images, and unannotated images.

    Parameters:
        pdf_path (Path): Path to the PDF file.
        client (vision.ImageAnnotatorClient): Google Vision API client for text detection.
        annotation_font_path (Path): Path to the font file for annotations.

    Returns:
        Tuple[List[str], List[List[vision.EntityAnnotation]], List[Image.Image], List[Image.Image]]:
            - List of extracted full-page texts (one entry per page).
            - List of word locations (list of `vision.EntityAnnotation` objects for each page).
            - List of annotated images (with bounding boxes and text annotations).
            - List of unannotated images (raw page images).

    Raises:
        FileNotFoundError: If the specified PDF file does not exist.
        ValueError: If the PDF file is invalid or contains no pages.
        Exception: For any unexpected errors during processing.

    Example:
        >>> from pathlib import Path
        >>> from google.cloud import vision
        >>> pdf_path = Path("/path/to/example.pdf")
        >>> font_path = Path("/path/to/fonts/Arial.ttf")
        >>> client = vision.ImageAnnotatorClient()
        >>> try:
        >>>     text_pages, word_locations_list, annotated_images, unannotated_images = build_processed_pdf(
        >>>         pdf_path, client, font_path
        >>>     )
        >>>     print(f"Processed {len(text_pages)} pages successfully!")
        >>> except Exception as e:
        >>>     print(f"Error processing PDF: {e}")
    """
    try:
        doc = load_pdf_pages(pdf_path)
    except FileNotFoundError as fnf_error:
        raise FileNotFoundError(f"Error loading PDF: {fnf_error}")
    except ValueError as ve:
        raise ValueError(f"Invalid PDF file: {ve}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred while loading the PDF: {e}")

    if doc.page_count == 0:
        raise ValueError(f"The PDF file '{pdf_path}' contains no pages.")

    print(f"Processing document with {doc.page_count} pages...")

    text_pages = []
    word_locations_list = []
    annotated_images = []
    unannotated_images = []
    first_page_dimensions = None

    for page_num in range(doc.page_count):
        print(f"Processing page {page_num + 1}/{doc.page_count}...")

        try:
            page = doc.load_page(page_num)
            full_page_text, word_locations, annotated_image, unannotated_image, page_dimensions = process_page(page, client, annotation_font_path)

            if page_num == 0: #save first page info
                first_page_dimensions = page_dimensions
            elif page_dimensions != first_page_dimensions: # verify page dimensions are consistent
                warnings.warn(
                f"Page {page_num + 1} has different dimensions than page 1."
                f"({page_dimensions}) compared to the first page: ({first_page_dimensions}).",
                PDFParseWarning
            )

            text_pages.append(full_page_text)
            word_locations_list.append(word_locations)
            annotated_images.append(annotated_image)
            unannotated_images.append(unannotated_image)

        except ValueError as ve:
            print(f"ValueError on page {page_num + 1}: {ve}")
        except OSError as oe:
            print(f"OSError on page {page_num + 1}: {oe}")
        except Exception as e:
            print(f"Unexpected error on page {page_num + 1}: {e}")

    print(f"page dimensions: {page_dimensions}")
    return text_pages, word_locations_list, annotated_images, unannotated_images

def serialize_entity_annotations_to_json(annotations: List[List[EntityAnnotation]]) -> str:
    """
    Serializes a nested list of EntityAnnotation objects into a JSON-compatible format using Base64 encoding.

    Parameters:
        annotations (List[List[EntityAnnotation]]): The nested list of EntityAnnotation objects.

    Returns:
        str: The serialized data in JSON format as a string.
    """
    serialized_data = []
    for page_annotations in annotations:
        serialized_page = [
            base64.b64encode(annotation.SerializeToString()).decode('utf-8')
            for annotation in page_annotations
        ]
        serialized_data.append(serialized_page)

    # Convert to a JSON string
    return json.dumps(serialized_data, indent=4)

def deserialize_entity_annotations_from_json(data: str) -> List[List[EntityAnnotation]]:
    """
    Deserializes JSON data into a nested list of EntityAnnotation objects.

    Parameters:
        data (str): The JSON string containing serialized annotations.

    Returns:
        List[List[EntityAnnotation]]: The reconstructed nested list of EntityAnnotation objects.
    """
    serialized_data = json.loads(data)
    deserialized_data = []

    for serialized_page in serialized_data:
        page_annotations = [
            EntityAnnotation.deserialize(base64.b64decode(serialized_annotation))
            for serialized_annotation in serialized_page
        ]
        deserialized_data.append(page_annotations)

    return deserialized_data

def save_processed_pdf_data(output_dir: Path, base_name: str, text_pages: List[str], 
                            word_locations: List[List[EntityAnnotation]], 
                            annotated_images: List[Image.Image], 
                            unannotated_images: List[Image.Image]):
    """
    Saves processed PDF data to files for later reloading.

    Parameters:
        output_dir (Path): Directory to save the data (as a Path object).
        base_name (str): Base name for the output directory (usually the PDF name without extension).
        text_pages (List[str]): Extracted full-page text.
        word_locations (List[List[EntityAnnotation]]): Word locations and annotations from Vision API.
        annotated_images (List[PIL.Image.Image]): Annotated images with bounding boxes.
        unannotated_images (List[PIL.Image.Image]): Raw unannotated images.

    Returns:
        None
    """
    # Create output directories
    base_path = output_dir / base_name
    images_dir = base_path / "images"

    base_path.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)

    # Save text data
    text_pages_file = base_path / "text_pages.json"
    with text_pages_file.open("w", encoding="utf-8") as f:
        json.dump(text_pages, f, indent=4, ensure_ascii=False)

    # Save word locations as JSON
    word_locations_file = base_path / "word_locations.json"
    serialized_word_locations = serialize_entity_annotations_to_json(word_locations)
    with word_locations_file.open("w", encoding="utf-8") as f:
        f.write(serialized_word_locations)

    # Save images
    for i, annotated_image in enumerate(annotated_images):
        annotated_file = images_dir / f"annotated_page_{i + 1}.png"
        annotated_image.save(annotated_file)
    for i, unannotated_image in enumerate(unannotated_images):
        unannotated_file = images_dir / f"unannotated_page_{i + 1}.png"
        unannotated_image.save(unannotated_file)

    # Save metadata
    metadata = {
        "source_pdf": base_name,
        "page_count": len(text_pages),
        "images_directory": str(images_dir),  # Convert Path to string for JSON serialization
        "files": {
            "text_pages": "text_pages.json",
            "word_locations": "word_locations.json",
        },
    }
    metadata_file = base_path / "metadata.json"
    with metadata_file.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)

    print(f"Processed data saved in: {base_path}")

def load_processed_PDF_data(output_dir: Path, base_name: str) -> Tuple[List[str], List[List[EntityAnnotation]], List[Image.Image], List[Image.Image]]:
    """
    Loads processed PDF data from files using metadata for file references.

    Parameters:
        output_dir (Path): Directory where the data is stored (as a Path object).
        base_name (str): Base name of the processed directory.

    Returns:
        Tuple[List[str], List[List[EntityAnnotation]], List[Image.Image], List[Image.Image]]:
            - Loaded text pages.
            - Word locations (list of `EntityAnnotation` objects for each page).
            - Annotated images.
            - Unannotated images.

    Raises:
        FileNotFoundError: If any required files are missing.
        ValueError: If the metadata file is incomplete or invalid.
    """
    base_path = output_dir / base_name
    metadata_file = base_path / "metadata.json"

    # Load metadata
    try:
        with metadata_file.open("r", encoding="utf-8") as f:
            metadata = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Metadata file '{metadata_file}' not found.")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid metadata file format: {e}")

    # Extract file paths from metadata
    text_pages_file = base_path / metadata.get("files", {}).get("text_pages", "text_pages.json")
    word_locations_file = base_path / metadata.get("files", {}).get("word_locations", "word_locations.json")
    images_dir = Path(metadata.get("images_directory", base_path / "images"))

    # Validate file paths
    if not text_pages_file.exists():
        raise FileNotFoundError(f"Text pages file '{text_pages_file}' not found.")
    if not word_locations_file.exists():
        raise FileNotFoundError(f"Word locations file '{word_locations_file}' not found.")
    if not images_dir.exists() or not images_dir.is_dir():
        raise FileNotFoundError(f"Images directory '{images_dir}' not found.")

    # Load text pages
    with text_pages_file.open("r", encoding="utf-8") as f:
        text_pages = json.load(f)

    # Load word locations
    with word_locations_file.open("r", encoding="utf-8") as f:
        serialized_word_locations = f.read()
        word_locations = deserialize_entity_annotations_from_json(serialized_word_locations)

    # Load images
    annotated_images = []
    unannotated_images = []
    for file in sorted(images_dir.iterdir()):  # Iterate over files in the images directory
        if file.name.startswith("annotated_page_") and file.suffix == ".png":
            annotated_images.append(Image.open(file))
        elif file.name.startswith("unannotated_page_") and file.suffix == ".png":
            unannotated_images.append(Image.open(file))

    # Ensure images were loaded correctly
    if not annotated_images or not unannotated_images:
        raise ValueError(f"No images found in the directory '{images_dir}'.")

    return text_pages, word_locations, annotated_images, unannotated_images