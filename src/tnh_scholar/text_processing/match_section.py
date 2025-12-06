import re
from typing import List, Optional

from pydantic import BaseModel

# Import from tnh_scholar for TextObject compatibility


class MatchObject(BaseModel):
    """Basic Match Object definition."""
    type: str
    level: Optional[int] = None
    words: Optional[List[str]] = None
    case_sensitive: Optional[bool] = False
    decorator: Optional[str] = None
    pattern: Optional[str] = None

class SectionConfig(BaseModel):
    """Configuration for section detection."""
    name: str
    description: Optional[str] = None
    patterns: List[MatchObject]

def find_markdown_header(line: str, level: int) -> bool:
    """Check if line matches markdown header pattern."""
    stripped = line.lstrip()
    return stripped.startswith('#' * level + ' ')

def find_keyword(
    line: str, 
    words: List[str], 
    case_sensitive: bool, 
    decorator: Optional[str]
    ) -> bool:
    """Check if line matches keyword pattern."""
    if not case_sensitive:
        line = line.lower()
        words = [w.lower() for w in words]

    # Check if line starts with any keyword
    if not any(line.lstrip().startswith(word) for word in words):
        return False

    # If decorator specified, check if it appears in line
    return not decorator or decorator in line

def find_regex(line: str, pattern: str) -> bool:
    """Check if line matches regex pattern."""
    return bool(re.match(pattern, line))

def find_section_boundaries(text: str, config: SectionConfig) -> List[int]:
    """Find all section boundary line numbers."""
    boundaries = []
    
    for i, line in enumerate(text.splitlines(), 1):
        for pattern in config.patterns:
            matched = False
            
            if pattern.type == "markdown_header" and pattern.level:
                matched = find_markdown_header(line, pattern.level)
                
            elif pattern.type == "keyword" and pattern.words:
                matched = find_keyword(
                    line, 
                    pattern.words,
                    pattern.case_sensitive or False,
                    pattern.decorator
                )
                
            elif pattern.type == "regex" and pattern.pattern:
                matched = find_regex(line, pattern.pattern)
            
            if matched:
                boundaries.append(i)
                break  # Stop checking patterns if we found a match
                
    return boundaries

# Following Needs refactor to work with new TextObject class

# def create_text_object(text: str, boundaries: List[int]) -> TextObject:
#     """Create TextObject from text and section boundaries."""
#     lines = text.splitlines()
#     sections = []
    
#     # Handle first section starting after line 1
#     if not boundaries or boundaries[0] != 1:
#         boundaries.insert(0, 1)
        
#     # Create sections from boundaries
#     for i in range(len(boundaries)):
#         start = boundaries[i]
#         end = boundaries[i + 1] - 1 if i + 1 < len(boundaries) else len(lines)
        
#         # Get section title from first line
#         title = lines[start - 1].strip()
        
#         section = LogicalSection(
#             title=title,
#             start_line=start,
#             end_line=end
#         )
#         sections.append(section)
    
#     return TextObject(
#         language="en",  # Default to English for PoC
#         sections=sections
#     )