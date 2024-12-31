from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import yaml
from pathlib import Path
from typing import Dict, Optional, List, Set, Any
import re

class ContentType(Enum):
    DHARMA_TALK = "dharma_talk"
    CHAPTER = "chapter"
    BOOK = "book"
    NEWSLETTER = "newsletter"
    TRANSLATION = "translation"
    ARTICLE = "article"

class TaskType(Enum):
    TRANSLATE = "translate"
    SECTION = "section"
    SUMMARIZE = "summarize"
    FORMAT = "format"

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, List

@dataclass
class SystemMessage:
    task_type: TaskType
    content_type: ContentType
    input_language: str
    instructions: str
    keyword: str = "default"
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    template_fields: Dict[str, str] = field(default_factory=dict)
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """
        Post-initialization hook to set timestamps if not provided.
        Called automatically after the default __init__.
        """
        current_time = datetime.now()
        self.created_at = current_time
        self.updated_at = current_time

    @staticmethod
    def generate_msg_id(
        task_type: TaskType,
        content_type: ContentType,
        input_language: str,
        keyword: str,
        timestamp: datetime
    ) -> str:
        return f"{task_type.value}_{content_type.value}_{input_language}_{keyword}_{timestamp.isoformat()}"

    @property
    def msg_id(self) -> str:
        return self.generate_msg_id(
            self.task_type,
            self.content_type,
            self.input_language,
            self.keyword,
            self.updated_at
        )

class SystemMessageManager:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.messages: Dict[str, SystemMessage] = {}
        self._load_messages()

    def _load_messages(self):
        """Load all system messages from YAML files."""
        for file_path in self.base_path.glob("**/*.yaml"):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                message = SystemMessage(
                    task_type=TaskType(data['task_type']),
                    content_type=ContentType(data['content_type']),
                    input_language=data['input_language'],
                    keyword=data['keyword'],
                    created_at=data['created_at'],
                    updated_at=data['updated_at'],
                    instructions=data['instructions'],
                    template_fields=data.get('template_fields', {}),
                    description=data.get('description'),
                    tags=data.get('tags', []),
                    author=data.get('author')
                )
                self.messages[message.msg_id] = message
                
    def _match_messages(
        self,
        criteria: Dict[str, Any]
    ) -> List[SystemMessage]:
        """
        Internal method to get all messages matching the given criteria.
        
        Args:
            criteria: Dictionary of attribute names and values to match
            
        Returns:
            List of matching SystemMessage objects
        """
        return [
            msg for msg in self.messages.values()
            if all(getattr(msg, attr) == value for attr, value in criteria.items())
        ]

    def get_latest_message(
        self,
        task_type: TaskType,
        content_type: ContentType,
        input_language: str,
        keyword: str = "default"
    ) -> Optional[SystemMessage]:
        """Get the most recent message matching the identifiers."""
        criteria = {
            "task_type": task_type,
            "content_type": content_type,
            "input_language": input_language,
            "keyword": keyword
        }
        matching_messages = self._match_messages(criteria)
        if not matching_messages:
            return None
        return max(matching_messages, key=lambda x: x.updated_at)

    def get_message_history(
        self,
        task_type: TaskType,
        content_type: ContentType,
        input_language: str,
        keyword: str = "default"
    ) -> List[SystemMessage]:
        """Get all versions of a message sorted by updated_at."""
        criteria = {
            "task_type": task_type,
            "content_type": content_type,
            "input_language": input_language,
            "keyword": keyword
        }
        matching_messages = self._match_messages(criteria)
        return sorted(matching_messages, key=lambda x: x.updated_at)

    def save_message(self, message: SystemMessage):
        """Save a new system message."""
        # Validate template fields
        actual_fields = set(re.findall(r'{(\w+)}', message.instructions))
        declared_fields = set(message.template_fields.keys())
        if actual_fields != declared_fields:
            raise ValueError(
                f"Template fields mismatch:\n"
                f"Extra declared fields: {declared_fields - actual_fields}\n"
                f"Undeclared used fields: {actual_fields - declared_fields}"
            )
        
        # Create the YAML structure
        data = {
            'task_type': message.task_type.value,
            'content_type': message.content_type.value,
            'input_language': message.input_language,
            'created_at': message.created_at,
            'updated_at': message.updated_at,
            'instructions': message.instructions,
            'template_fields': message.template_fields,
            'description': message.description,
            'tags': message.tags,
            'author': message.author
        }
        
        # Save to file using message ID for the filename
        file_path = self.base_path / message.task_type.value / f"{message.msg_id}.yaml"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True)
        
        self.messages[message.msg_id] = message

    def update_message(
        self,
        task_type: TaskType,
        content_type: ContentType,
        input_language: str,
        instructions: Optional[str] = None,
        description: Optional[str] = None,
        template_fields: Optional[Dict[str, str]] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[SystemMessage]:
        """Create a new version of an existing message with updates."""
        # Get the latest version of the message
        original = self.get_latest_message(task_type, content_type, input_language)
        if not original:
            return None

        # Create new message with updated fields
        new_message = SystemMessage(
            task_type=original.task_type,
            content_type=original.content_type,
            input_language=original.input_language,
            created_at=original.created_at,  # Keep original creation time
            updated_at=datetime.now(),       # New update time
            instructions=instructions if instructions is not None else original.instructions,
            template_fields=template_fields if template_fields is not None else original.template_fields.copy(),
            description=description if description is not None else original.description,
            tags=tags if tags is not None else original.tags.copy(),
            author=original.author
        )

        # Save the new version
        self.save_message(new_message)
        return new_message

    def apply_template(
        self,
        message: SystemMessage,
        field_values: Optional[Dict[str, str]] = None
    ) -> str:
        """Apply template values to instructions, using defaults where needed."""
        # Start with default values
        values = message.template_fields.copy()
        
        # Override with provided values if any
        if field_values:
            values.update(field_values)
            
        # Any missing fields get empty string
        actual_fields = set(re.findall(r'{(\w+)}', message.instructions))
        for field in actual_fields:
            if field not in values:
                values[field] = ""
                
        return message.instructions.format(**values)