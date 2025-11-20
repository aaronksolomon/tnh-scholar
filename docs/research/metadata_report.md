---
title: "**Summary Report on Metadata Extraction, Source Parsing, and Model Training for TNH-Scholar**"
description: "## **Overview**"
owner: ""
status: processing
created: "2024-10-24"
---
# **Summary Report on Metadata Extraction, Source Parsing, and Model Training for TNH-Scholar**

## **Overview**
The process of extracting and handling metadata for training models from Thich Nhat Hanh’s works has proven to be a complex but feasible task. While initial expectations were that this would be straightforward, we’ve learned that every book and text source has its own formatting and structural peculiarities, requiring tailored approaches for each. As we move forward with building the three primary models (search, conversation, and translation), it’s clear that managing metadata correctly will be essential for effective training and retrieval.

---

## **1. Key Learnings on Metadata Extraction & Source Parsing**

### **Challenges Identified**:
- **Inconsistent formatting**: Each book (or other source) has unique formatting, especially when comparing different types of publications (e.g., EPUBs vs PDFs).
- **Non-uniform structure**: Some books have chapters, others have only sections or exercises, while some include quotes and author signatures that are not always easily distinguishable from other text elements.
- **Manual intervention**: Parsing tools help automate much of the extraction, but each book requires some degree of human intervention or book-specific rules.

### **Tools Used So Far**:
- **ebooklib**: Used to read and extract content from EPUB books, providing access to the structural elements present in the ebook’s HTML.
- **BeautifulSoup**: For parsing the HTML content extracted from EPUBs, allowing for extraction based on tags and attributes (e.g., `<p>`, `<blockquote>`, and class names).
- **Regular Expressions (Regex)**: Used for detecting patterns in text, such as chapter titles, quotes, and headings.
- **SpaCy**: Considered for creating custom NLP models for detecting metadata like "paragraphs" or "quotes," but this would require additional training data.

### **Potential Tools for Further Exploration**:
- **Prodigy**: A powerful annotation tool designed for training NLP models. It can be used to manually annotate text for metadata like "heading," "paragraph," "quote," etc. This helps create a labeled dataset that can train models to automatically identify such elements.
- **Label Studio**: An open-source data labeling tool that supports text, image, and audio annotation. It can be used to manually annotate and label different structural elements like chapters, quotes, and sections for model training or evaluation.
- **LayoutParser**: A deep learning-based tool for document layout analysis. It can be useful for extracting structural information from scanned PDFs or documents with more complex layouts. This would be particularly useful if you're dealing with non-EPUB formatted books or sources.
- **Tesseract OCR**: An open-source optical character recognition (OCR) engine, useful for converting scanned images and PDFs into text that can then be processed for structural extraction. If you have scanned books, Tesseract can be the starting point for transforming them into searchable text.
- **PDFMiner**: A library for extracting text and metadata from PDFs. It can be used when working with PDF versions of books and helps retain the structure of the content for further processing.
- **Hugging Face Transformers**: A versatile library that offers pre-trained models for text classification, zero-shot classification, and other tasks. It can be leveraged to automate the detection of structural elements, such as headings, quotes, or sections, without the need for extensive manual training.
- **Fairseq**: An open-source sequence-to-sequence learning library from Facebook AI. It can be explored for training custom translation models or for tasks that require document-level context understanding across large texts.
- **OpenRefine**: A tool for cleaning and transforming data. It could be useful for preprocessing and standardizing the extracted text metadata, ensuring consistency across your dataset.
- **Whoosh**: A fast, featureful full-text indexing and searching library. Once the metadata is extracted, Whoosh can be used to build a lightweight search engine for indexing and retrieving relevant text chunks.
- NLTK
- Textacy
- Tika
- Polyglot
- Gensim
- Doccano

### **Current Approaches for Metadata Extraction**:

#### **A. Rule-Based Extraction**:
   - **Strategy**: Use HTML tags and class attributes to map elements like chapters, paragraphs, headings, quotes, and exercises to custom markers (e.g., `<<Chapter>>`, `<<Quote>>`).
   - **Tools**: BeautifulSoup, regex.
   - **Pros**: Can automate a large portion of the process for well-structured EPUBs.
   - **Cons**: Requires manual tweaking for each source, not suitable for handling inconsistencies or malformed HTML.

#### **B. Custom Metadata Labeling**:
   - **Strategy**: Create custom training data to fine-tune NLP models for metadata labeling, detecting structural elements like "quote," "exercise," "chapter," and "paragraph."
   - **Tools**: SpaCy for NER (Named Entity Recognition).
   - **Pros**: Once trained, the model can generalize to new books, reducing the need for manual intervention.
   - **Cons**: Requires significant upfront work in annotating data, time-consuming.

#### **C. PDF Extraction (Last Resort)**:
   - **Strategy**: For books only available as PDFs, use OCR tools to extract text, then apply regex or rule-based extraction.
   - **Tools**: PDFMiner, Tesseract OCR.
   - **Pros**: Works when EPUB or other formats are not available.
   - **Cons**: PDF extraction tends to lose structural fidelity, making it harder to recover headings and paragraphs.

### **Lessons Learned**:
- **Structural extraction complexity**: Parsing books is harder than expected, and managing structural elements (headings, chapters, etc.) requires a flexible, multi-step approach.
- **Time and resource investment**: Extracting metadata is time-consuming, and managing multiple books will require templated rules or automation combined with manual oversight.

---

## **2. Approaches to Train 3 Primary Models**

We aim to create three primary models: **search**, **conversational**, and **translation**. Each model requires a different approach to training, with metadata playing various roles in enhancing the model’s functionality.

### **A. Search Model (Fine-Tuned BERT)**

**Goal**: Retrieve relevant passages when users search for topics (e.g., "mindfulness and compassion").

**Training Strategy**:
   - **Text Segmentation**: Fine-tune BERT on text **chunks** (paragraphs, sections) without metadata.
   - **Metadata Use**: Metadata like "Introduction," "Quote," or "Chapter" can be used to **rank results** or **filter** them during retrieval but should be excluded during training.
   - **Inclusion Criteria**: Include all relevant content, including quotes and cited sutras.

**Considerations**:
   - Metadata helps provide context in the search results (e.g., “This passage is from the introduction to *Love in Action*”).
   - Ranking by metadata (e.g., prioritize results from exercises or introductions) will improve user experience.

### **B. Conversational Model (Fine-Tuned GPT-like)**

**Goal**: Simulate conversations with the text in Thay’s voice, responding naturally to user questions.

**Training Strategy**:
   - **Voice Consistency**: Exclude quotes, sutras, or references that are not directly in Thich Nhat Hanh’s voice. Focus on Thay’s personal writings and speeches.
   - **Metadata Use**: Metadata such as "Chapter" or "Section" might not be as useful here. Instead, focus on ensuring that only relevant content is included for training.
   - **Fine-tuning**: Use conversation datasets to improve the model’s ability to respond in Thay’s style.

**Considerations**:
   - Metadata isn’t as critical for training but will be important when parsing the data (i.e., excluding non-Thay voice content).

### **C. Translation Model (Fine-Tuned MarianMT or mBART)**

**Goal**: Provide high-quality translations between English, Vietnamese, and French for Thich Nhat Hanh’s teachings.

**Training Strategy**:
   - **Parallel Texts**: Align bilingual or multilingual texts from Thich Nhat Hanh’s works.
   - **Metadata Use**: Metadata should be stripped from the training data, focusing purely on the text for translation.
   - **Fine-tuning**: Use existing pre-trained translation models (MarianMT, mBART) and fine-tune on the specific language pairs and content relevant to Thich Nhat Hanh’s works.

**Considerations**:
   - Metadata is largely irrelevant for the translation task but could be helpful when cross-referencing translations back to the original text.

---

## **3. Summary of Current Tools and Their Roles**

| **Tool**         | **Purpose**                                    | **Role in Project**                                                |
|------------------|------------------------------------------------|--------------------------------------------------------------------|
| **ebooklib**     | EPUB parsing                                   | Extracts content and structure from EPUB books.                    |
| **BeautifulSoup**| HTML parsing                                   | Processes HTML from EPUBs to extract structured elements.           |
| **Regex**        | Pattern matching                               | Identifies chapters, quotes, and headings via patterns.             |
| **SpaCy**        | Custom NLP model for metadata extraction       | Can be used for fine-tuning to detect specific metadata entities.    |
| **PDFMiner**     | PDF text extraction                            | Alternative for PDF books (fallback).                              |
| **Tesseract**    | OCR for scanned documents                      | Used if only image-based PDFs are available.                       |
| **Hugging Face** | Model fine-tuning                              | BERT for search, GPT-like models for conversation, MarianMT for translation. |

---

## **4. Important Considerations Going Forward**

- **Refining Extraction**: Further experiments with rule-based extraction or custom models for metadata will be essential.
- **Model-Specific Training**: The distinction between training data for **search**, **conversation**, and **translation** must be carefully managed (e.g., include sutras for search, exclude for conversational training).
- **Proof of Concept Focus**: While full automation is a long-term goal, manual handling will be required in the short term, especially for book-specific edge cases.