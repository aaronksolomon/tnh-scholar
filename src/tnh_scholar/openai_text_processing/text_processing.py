from pathlib import Path
from typing import List, Dict
import logging
import json

from typing import List, Optional

from tnh_scholar.xml_processing import wrap_lines, unwrap_lines, lines_from_wrapped_text
from tnh_scholar.text_processing import get_text_from_file, write_text_to_file
from tnh_scholar.utils import iterate_subdir, load_json_into_model, save_model_to_json
from .response_objects import BaseSection, SectionEn, SectionVi, DharmaTalkEn, DharmaTalkVi

from .text_process_interface import process_text
