"""Subprocess-only service fixture; never calls production network transports."""

import os
import time
from pathlib import Path

from tnh_scholar.cli_tools.tnh_gen import tnh_gen
from tnh_scholar.cli_tools.tnh_gen.commands import run as run_module
from tnh_scholar.cli_tools.tnh_gen.config_loader import CLIConfig
from tnh_scholar.cli_tools.tnh_gen.factory import ServiceOverrides
from tnh_scholar.cli_tools.tnh_gen.run_status.emitter import RunStatusEmitter
from tnh_scholar.cli_tools.tnh_gen.run_status.factory import create_emitter
from tnh_scholar.cli_tools.tnh_gen.run_status.models import RunStatusMetadata
from tnh_scholar.cli_tools.tnh_gen.run_status.policy import RunStatusConfig
from tnh_scholar.cli_tools.tnh_gen.state import ctx
from tnh_scholar.gen_ai_service.models.domain import CompletionEnvelope, RenderRequest
from tnh_scholar.gen_ai_service.pattern_catalog.adapters.prompts_adapter import PromptsAdapter


class FixtureService:
    """Read actual prompts and wait for the parent to observe a heartbeat."""

    def __init__(self) -> None:
        self.catalog = PromptsAdapter(prompts_base=Path(os.environ["TG06_PROMPTS"]))

    def generate(self, request: RenderRequest) -> CompletionEnvelope:
        deadline = time.monotonic() + 15
        release = Path(os.environ["TG06_RELEASE"])
        while not release.exists():
            if time.monotonic() >= deadline:
                raise TimeoutError("Parent did not observe status")
            time.sleep(0.01)
        return CompletionEnvelope.model_validate_json(Path(os.environ["TG06_RESPONSE"]).read_text())


class FixtureFactory:
    def create_genai_service(self, config: CLIConfig, overrides: ServiceOverrides) -> FixtureService:
        return FixtureService()


def fast_emitter(metadata: RunStatusMetadata, config: RunStatusConfig) -> RunStatusEmitter:
    """Accelerate heartbeat tests without introducing a production env override."""
    return create_emitter(metadata, config.model_copy(update={"heartbeat_seconds": 0.05}))


if __name__ == "__main__":
    ctx.service_factory = FixtureFactory()
    run_module.create_emitter = fast_emitter
    tnh_gen.main()
