from .xml_processing import (
    FormattingError as FormattingError,
)
from .xml_processing import (
    PagebreakXMLParser as PagebreakXMLParser,
)
from .xml_processing import (
    join_xml_data_to_doc as join_xml_data_to_doc,
)
from .xml_processing import (
    remove_page_tags as remove_page_tags,
)
from .xml_processing import (
    save_pages_to_xml as save_pages_to_xml,
)
from .xml_processing import (
    split_xml_on_pagebreaks as split_xml_on_pagebreaks,
)
from .xml_processing import (
    split_xml_pages as split_xml_pages,
)

__all__ = [
    "FormattingError",
    "PagebreakXMLParser",
    "join_xml_data_to_doc",
    "remove_page_tags",
    "save_pages_to_xml",
    "split_xml_on_pagebreaks",
    "split_xml_pages",
]
