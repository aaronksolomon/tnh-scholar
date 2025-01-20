from typing import List

from pydantic import BaseModel, Field

TEXT_SECTIONS_DESCRIPTION = (
    "Ordered list of logical sections for the text. "
    "The sequence of line ranges for the sections must cover every line "
    "from start to finish without any overlaps or gaps."
)


class LogicalSection(BaseModel):
    """
    A logically coherent section of text.
    """

    title: str = Field(
        ...,
        description="Meaningful title for the section in the original language of the section.",
    )
    start_line: int = Field(
        ..., description="Starting line number of the section (inclusive)."
    )
    end_line: int = Field(
        ..., description="Ending line number of the section (inclusive)."
    )


class TextObject(BaseModel):
    """
    Represents a text in any language broken into coherent logical sections.
    """

    language: str = Field(..., description="ISO 639-1 language code of the text.")
    sections: List[LogicalSection] = Field(..., description=TEXT_SECTIONS_DESCRIPTION)


# class BaseSection(BaseModel):
#     """
#     Base class for a section, containing shared attributes.
#     """
#     start_line: int = Field(
#         ...,
#         description="Starting line number of the section (inclusive)."
#     )
#     end_line: int = Field(
#         ...,
#         description="Ending line number of the section (inclusive)."
#     )

# class SectionEn(BaseSection):
#     """
#     Represents a section of a Dharma talk in English with a title and summary.
#     """
#     title: str = Field(
#         ...,
#         description="Title of the section in English."
#     )
#     summary: str = Field(
#         ...,
#         description="Summary of the section content in English."
#     )

# class SectionVi(BaseSection):
#     """
#     Represents a section of a Dharma talk in a Language other than English.
#     English translation of the title, and summary.
#     """
#     title_vi: str = Field(
#         ...,
#         description="Title of the section in Vietnamese."
#     )
#     title_en: str = Field(
#         ...,
#         description="Translated title of the section in English."
#     )
#     summary: str = Field(
#         ...,
#         description="Summary of the section content in English."
#     )

# class DharmaTalkEn(BaseModel):
#     """
#     Represents an English Dharma Talk, including a summary
#     and sections.
#     """
#     talk_summary: str = Field(
#         ...,
#         description="Overall summary of the Dharma talk in English."
#     )
#     sections: List[SectionEn] = Field(
#         ...,
#         description=TALK_SECTIONS_DESCRIPTION
#     )

# class DharmaTalkVi(BaseModel):
#     """
#     Represents a Vietnamese Dharma Talk, including a summary in English
#     and sections
#     """
#     talk_summary: str = Field(
#         ...,
#         description="Overall summary of the Dharma talk in English."
#     )
#     sections: List[SectionVi] = Field(
#         ...,
#         description=TALK_SECTIONS_DESCRIPTION
#     )

# class BaseSection(BaseModel):
#     start_line: int = Field(..., description="Starting line number of the section (inclusive).")
#     end_line: int = Field(..., description="Ending line number of the section (inclusive).")

# class SectionEn(BaseSection):
#     title: str = Field(..., description="Title of the section")
#     summary: str = Field(..., description="Summary of the section")

# class SectionVi(BaseSection):
#     title_vi: str = Field(..., description="Section title (Vietnamese).")
#     title_en: str = Field(..., description="Translated title (English).")
#     summary: str = Field(..., description="Section summary (English).")

# class DharmaTalkEn(BaseModel):
#     talk_summary: str = Field(..., description="Dharma talk summary in English.")
#     sections: List[SectionEn] = Field(..., description="Ordered list of sections.")

# class DharmaTalkVi(BaseModel):
#     talk_summary: str = Field(..., description="Dharma talk summary in English.")
#     sections: List[SectionVi] = Field(..., description="Ordered list of sections. The sequence of line ranges for the sections must cover every line from start to finish without any overlaps or gaps.")

# class Section(BaseModel):
#     title: str = Field(
#         ...,
#         description="The title of the section"
#     )
#     summary: str = Field(
#         ...,
#         description="A summary of the section"
#     )
#     start_line: int = Field(
#         ...,
#         description="The starting line number of the section."
#     )
#     end_line: int = Field(
#         ...,
#         description="The ending line number of the section."
#     )

# class DharmaTalkSections(BaseModel):
#     talk_summary: str = Field(
#         ...,
#         description="A summary of the Dharma talk content."
#     )
#     sections: List[Section] = Field(
#         ...,
#         description="An ordered list of sections with their titles and included start and end line numbers."
#     )

# class Section(BaseModel):
#     title_vi: str = Field(
#         ...,
#         description="The title of the section in Vietnamese."
#     )
#     title_en: str = Field(
#         ...,
#         description="The translation of the title of the section in English."
#     )
#     summary: str = Field(
#         ...,
#         description="A summary of the section in English."
#     )
#     start_line: int = Field(
#         ...,
#         description="The starting line number of this section."
#     )
#     end_line: int = Field(
#         ...,
#         description="The ending line number of this section."
#     )

# class DharmaTalkSections(BaseModel):
#     talk_summary: str = Field(
#         ...,
#         description="A summary of the Dharma talk in English."
#     )
#     sections: List[Section] = Field(
#         ...,
#         description="An ordered list of sections with their titles and included start and end line numbers. The sequence of line ranges for the sections must cover every line from start to finish without any overlaps or gaps."
#     )
# class Section(BaseSection):
#     """
#     Represents a section of a text in any language with English translations.
#     For English sections, title_orig and title_en will be identical.
#     """
#     title_orig: str = Field(
#         ...,
#         description="Title of the section in original language."
#     )
#     title_en: str = Field(
#         ...,
#         description="Title of the section in English."
#     )
#     summary: str = Field(
#         ...,
#         description="Summary of the section content in English."
#     )
