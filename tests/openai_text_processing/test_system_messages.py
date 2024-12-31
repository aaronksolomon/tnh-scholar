import unittest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil
from typing import Dict
import yaml

from tnh_scholar.openai_text_processing import ( 
    SystemMessage,
    SystemMessageManager,
    TaskType,
    ContentType
)

class TestSystemMessage(unittest.TestCase):
    def setUp(self):
        self.base_time = datetime(2024, 1, 1, 12, 0)
        self.basic_message = SystemMessage(
            task_type=TaskType.FORMAT,
            content_type=ContentType.DHARMA_TALK,
            input_language="en",
            created_at=self.base_time,
            updated_at=self.base_time,
            instructions="Format the {section_title}",
            template_fields={"section_title": ""}
        )

    def test_msg_id_generation(self):
        """Test message ID generation is consistent and contains required components."""
        msg_id = self.basic_message.msg_id
        
        # Check all components are present
        self.assertIn(TaskType.FORMAT.value, msg_id)
        self.assertIn(ContentType.DHARMA_TALK.value, msg_id)
        self.assertIn("en", msg_id)
        self.assertIn(self.base_time.isoformat(), msg_id)

    def test_static_msg_id_generation(self):
        """Test static message ID generation method."""
        static_id = SystemMessage.generate_msg_id(
            TaskType.FORMAT,
            ContentType.DHARMA_TALK,
            "en",
            self.base_time
        )
        instance_id = self.basic_message.msg_id
        self.assertEqual(static_id, instance_id)

class TestSystemMessageManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = SystemMessageManager(self.test_dir)
        self.base_time = datetime(2024, 1, 1, 12, 0)

    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.test_dir)

    def create_test_message(self, 
                          task_type: TaskType = TaskType.FORMAT,
                          content_type: ContentType = ContentType.DHARMA_TALK,
                          input_language: str = "en",
                          time_offset: int = 0) -> SystemMessage:
        """Helper method to create test messages."""
        message_time = self.base_time + timedelta(hours=time_offset)
        return SystemMessage(
            task_type=task_type,
            content_type=content_type,
            input_language=input_language,
            created_at=self.base_time,
            updated_at=message_time,
            instructions="Test {placeholder}",
            template_fields={"placeholder": ""}
        )

    def test_save_message(self):
        """Test saving a new message."""
        message = self.create_test_message()
        self.manager.save_message(message)
        
        # Check file exists
        file_path = self.test_dir / TaskType.FORMAT.value / f"{message.msg_id}.yaml"
        self.assertTrue(file_path.exists())
        
        # Check content
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
            self.assertEqual(data['task_type'], TaskType.FORMAT.value)
            self.assertEqual(data['content_type'], ContentType.DHARMA_TALK.value)

    def test_get_latest_message(self):
        """Test retrieving the latest message version."""
        # Create messages with different timestamps
        for i in range(3):
            message = self.create_test_message(time_offset=i)
            self.manager.save_message(message)

        latest = self.manager.get_latest_message(
            TaskType.FORMAT,
            ContentType.DHARMA_TALK,
            "en"
        )
        
        self.assertIsNotNone(latest)
        self.assertEqual(latest.updated_at, self.base_time + timedelta(hours=2))

    def test_get_message_history(self):
        """Test retrieving message history."""
        # Create messages with different timestamps
        messages = []
        for i in range(3):
            message = self.create_test_message(time_offset=i)
            self.manager.save_message(message)
            messages.append(message)

        history = self.manager.get_message_history(
            TaskType.FORMAT,
            ContentType.DHARMA_TALK,
            "en"
        )
        
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0].updated_at, messages[0].updated_at)
        self.assertEqual(history[-1].updated_at, messages[-1].updated_at)

    def test_update_message(self):
        """Test updating a message creates new version."""
        # Create initial message
        original = self.create_test_message()
        self.manager.save_message(original)

        # Update message
        updated = self.manager.update_message(
            TaskType.FORMAT,
            ContentType.DHARMA_TALK,
            "en",
            instructions="Updated {placeholder}",
            description="Updated description"
        )

        self.assertIsNotNone(updated)
        self.assertNotEqual(updated.msg_id, original.msg_id)
        self.assertEqual(updated.instructions, "Updated {placeholder}")
        self.assertEqual(updated.created_at, original.created_at)
        self.assertGreater(updated.updated_at, original.updated_at)

    def test_apply_template(self):
        """Test template application with various scenarios."""
        message = self.create_test_message()
        
        # Test with provided values
        result = self.manager.apply_template(message, {"placeholder": "value"})
        self.assertEqual(result, "Test value")
        
        # Test with default values
        result = self.manager.apply_template(message)
        self.assertEqual(result, "Test ")

    def test_invalid_template_fields(self):
        """Test validation of template fields."""
        message = SystemMessage(
            task_type=TaskType.FORMAT,
            content_type=ContentType.DHARMA_TALK,
            input_language="en",
            created_at=self.base_time,
            updated_at=self.base_time,
            instructions="Test {placeholder}",
            template_fields={"wrong_field": ""}  # Mismatched field
        )
        
        with self.assertRaises(ValueError):
            self.manager.save_message(message)

if __name__ == '__main__':
    unittest.main()