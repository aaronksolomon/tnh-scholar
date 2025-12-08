from tnh_scholar.prompt_system.config.policy import ValidationPolicy
from tnh_scholar.prompt_system.domain.models import Prompt, PromptMetadata
from tnh_scholar.prompt_system.service.loader import PromptLoader
from tnh_scholar.prompt_system.service.validator import PromptValidator


def test_loader_delegates_to_validator():
    validator = PromptValidator(ValidationPolicy())
    loader = PromptLoader(validator)
    prompt = Prompt(
        name="test",
        version="1.0.0",
        template="Hello",
        metadata=PromptMetadata(
            key="test",
            name="test",
            version="1.0.0",
            description="desc",
            task_type="test",
            required_variables=[],
        ),
    )

    result = loader.validate(prompt)

    assert result.valid
