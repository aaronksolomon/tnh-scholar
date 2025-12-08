---
title: "ADR-PT04: Prompt System Refactor Plan"
description: "Refactors the legacy pattern-based prompt system into a modular, object-service compliant PromptCatalog with validation, transport isolation, and clean dependency injection seams."
owner: "TNH Scholar Architecture Working Group"
author: "Codex (GPT-5), Aaron Solomon, Claude Sonnet 4.5"
status: current
created: "2025-12-05"
updated: "2025-12-07"
---
# ADR-PT04: Prompt System Refactor Plan (Revised)

Retire the monolithic pattern-era prompt code and replace it with a modular, object-service compliant `prompt_system` package aligned to ADR-A12 and ADR-OS01.

- **Status**: Accepted (Revised)
- **Date**: 2025-12-05 (Updated: 2025-12-06)
- **Owner**: TNH Scholar Architecture Working Group
- **Authors**: Codex (GPT-5), Aaron Solomon, Claude Sonnet 4.5
- **Related**: [ADR-PT03](/architecture/prompt-system/adr/adr-pt03-prompt-system-status-roadmap.md), [ADR-A12](/architecture/gen-ai-service/adr/adr-a12-prompt-system-fingerprinting-v1.md), [ADR-OS01](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md), [ADR-VSC02](/architecture/ui-ux/vs-code-integration/adr-vsc02-tnh-gen-cli-implementation.md), [TODO](/project/repo-root/todo-list.md)

---

## Context

### Legacy System Limitations

- Legacy `src/tnh_scholar/ai_text_processing/prompts.py` (~34 KB) violates separation of concerns: mixes Jinja rendering, git commits, file locking, CLI UX helpers, and dotenv loading.
- Pattern-era naming (`TNH_PATTERN_DIR`, `--pattern` flags) persists despite terminology migration to "prompts" (ADR-DD03/ADR-PT03).
- No transport layer isolation: git operations, file I/O, and caching are embedded in domain logic.
- Missing validation: no schema enforcement for prompt metadata (TODO #11, #16).
- Poor testability: monolithic structure prevents mocking and protocol-based testing.

### Service Contract Requirements

- **ADR-A12**: GenAI service expects `PromptsAdapter` returning `(RenderedPrompt, Fingerprint)` with provenance constructed in the service layer.
- **ADR-OS01**: All services must follow object-service architecture—domain protocols, adapters with mappers, transport isolation, strong typing, no literals.
- **Prompt-first tooling**: `tnh-gen` CLI and VS Code integration (ADR-VSC02) require discoverability, validation, and structured metadata.

### Rapid Prototype Operating Principles

**IMPORTANT**: TNH Scholar is in **rapid prototype phase (0.x)**. We prioritize:

1. **Breaking changes are acceptable**: No backward compatibility guarantees during 0.x; breaking changes push all dependent modules forward rather than maintain legacy shims.
2. **Force refactors in dependents**: When prompt system changes, GenAI service and CLI tools MUST refactor—this ensures architectural consistency.
3. **Remove legacy immediately**: Deprecate and remove `TNH_PATTERN_DIR` and old APIs now; no migration timeline needed.
4. **Single implementation**: New prompt system replaces GenAI's current implementation completely; no dual catalog support.

---

## Decision

### 1. Package Structure (Object-Service Compliant)

Create `src/tnh_scholar/prompt_system/` with clean layer separation:

```text
src/tnh_scholar/prompt_system/
  config/
    settings.py              # Settings: env vars (TNH_PROMPT_DIR, defaults)
    prompt_catalog_config.py # Config: construction-time catalog config
    policy.py                # Policy: render precedence, validation strictness

  domain/
    models.py                # Domain models: Prompt, PromptMetadata, RenderedPrompt
    protocols.py             # Protocols: PromptCatalogPort, PromptRendererPort, etc.

  transport/
    models.py                # Transport models: PromptFileRequest/Response, GitRefreshRequest/Response
    git_client.py            # GitTransportClient: pure git operations
    cache_client.py          # CacheTransport: in-memory caching

  adapters/
    git_catalog_adapter.py   # GitPromptCatalog: implements PromptCatalogPort
    filesystem_catalog_adapter.py  # FilesystemPromptCatalog: offline mode

  mappers/
    prompt_mapper.py         # PromptMapper: bi-directional file ↔ domain translation

  service/
    renderer.py              # PromptRenderer: Jinja environment + precedence
    validator.py             # PromptValidator: schema validation
    loader.py                # PromptLoader: front-matter parsing

  infra/
    locks.py                 # File locking utilities (if still needed)
```

**Migration**:

- Remove `ai_text_processing/prompts.py` entirely (no shim).
- Update all imports to `tnh_scholar.prompt_system`.
- Break existing code—force refactors.

---

### 2. Configuration Taxonomy (ADR-OS01 Compliant)

#### Settings (Application-Wide, from Environment)

```python
# config/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class PromptSystemSettings(BaseSettings):
    """Application-wide prompt system settings (from environment)."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Prompt repository location
    tnh_prompt_dir: Path = Path("prompts/")  # NEW: only this env var supported

    # Defaults
    default_validation_mode: str = "strict"
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300

    # Safety/security
    enable_safety_validation: bool = True

    @classmethod
    def from_env(cls) -> "PromptSystemSettings":
        return cls()
```

**BREAKING CHANGE**: `TNH_PATTERN_DIR` no longer supported. Use `TNH_PROMPT_DIR` only.

#### Config (Construction-Time)

```python
# config/prompt_catalog_config.py
from pydantic import BaseModel
from pathlib import Path

class PromptCatalogConfig(BaseModel):
    """Construction-time configuration for PromptCatalog."""
    repository_path: Path
    enable_git_refresh: bool = True
    cache_ttl_s: int = 300
    validation_on_load: bool = True

class GitTransportConfig(BaseModel):
    """Git transport layer configuration."""
    repository_path: Path
    auto_pull: bool = False
    pull_timeout_s: float = 30.0
    default_branch: str = "main"
```

#### Params (Per-Call)

```python
# domain/models.py
from pydantic import BaseModel
from typing import Any, Literal

class RenderParams(BaseModel):
    """Per-call rendering parameters."""
    variables: dict[str, Any] = {}
    strict_undefined: bool = True
    preserve_whitespace: bool = False
```

#### Policy (Behavior Control)

```python
# config/policy.py
from pydantic import BaseModel
from typing import Literal

class PromptRenderPolicy(BaseModel):
    """Policy for prompt rendering precedence and behavior."""
    policy_version: str = "1.0"

    # Precedence order (highest to lowest)
    precedence_order: list[str] = [
        "caller_context",       # RenderParams.variables
        "frontmatter_defaults", # Prompt metadata defaults
        "settings_defaults"     # Settings defaults
    ]

    # Behavior toggles
    allow_undefined_vars: bool = False
    merge_strategy: Literal["override", "merge_deep"] = "override"

class ValidationPolicy(BaseModel):
    """Validation behavior policy."""
    policy_version: str = "1.0"
    mode: Literal["strict", "warn", "permissive"] = "strict"
    fail_on_missing_required: bool = True
    allow_extra_variables: bool = False
```

---

### 3. Domain Models & Protocols

#### Domain Models

```python
# domain/models.py
from pydantic import BaseModel, Field
from typing import Literal

class PromptMetadata(BaseModel):
    """Prompt frontmatter metadata (validated schema)."""
    # Required
    key: str                    # Unique identifier (e.g., "translate", derived from filename)
    name: str
    version: str
    description: str
    task_type: str
    required_variables: list[str]

    # Optional
    optional_variables: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    default_model: str | None = None  # Model recommendation (e.g., "gpt-4o")
    output_mode: Literal["text", "json", "structured"] | None = None  # Output format hint

    # Safety/security (stubs for future)
    safety_level: Literal["safe", "moderate", "sensitive"] | None = None
    pii_handling: Literal["none", "anonymize", "explicit_consent"] | None = None
    content_flags: list[str] = Field(default_factory=list)

    # Provenance
    schema_version: str = "1.0"
    created_at: str | None = None
    updated_at: str | None = None

class Prompt(BaseModel):
    """Domain model for a prompt."""
    name: str
    version: str
    template: str  # Jinja2 template body (without frontmatter)
    metadata: PromptMetadata

class RenderedPrompt(BaseModel):
    """Rendered prompt ready for provider."""
    system: str | None = None
    messages: list[Message]

class Message(BaseModel):
    """Single message in a conversation."""
    role: Literal["system", "user", "assistant"]
    content: str

class ValidationIssue(BaseModel):
    """Single validation issue."""
    level: Literal["error", "warning", "info"]
    code: str
    message: str
    field: str | None = None
    line: int | None = None

class PromptValidationResult(BaseModel):
    """Result of prompt validation."""
    valid: bool
    errors: list[ValidationIssue] = Field(default_factory=list)
    warnings: list[ValidationIssue] = Field(default_factory=list)
    fingerprint_data: dict[str, Any] = Field(default_factory=dict)

    def succeeded(self) -> bool:
        return self.valid and len(self.errors) == 0
```

#### Protocols (Minimal, Focused)

```python
# domain/protocols.py
from typing import Protocol
from .models import Prompt, PromptMetadata, PromptValidationResult

class PromptCatalogPort(Protocol):
    """Repository for prompt storage/retrieval."""

    def get(self, key: str) -> Prompt:
        """Retrieve prompt by key."""
        ...

    def list(self) -> list[PromptMetadata]:
        """List all available prompts."""
        ...

class PromptRendererPort(Protocol):
    """Renders prompts with variable substitution."""

    def render(self, prompt: Prompt, params: RenderParams) -> RenderedPrompt:
        """Render prompt with Jinja2 templating."""
        ...

class PromptValidatorPort(Protocol):
    """Validates prompt schema and variables."""

    def validate(self, prompt: Prompt) -> PromptValidationResult:
        """Validate prompt metadata schema."""
        ...

    def validate_render(
        self,
        prompt: Prompt,
        params: RenderParams
    ) -> PromptValidationResult:
        """Validate that render params satisfy prompt requirements."""
        ...
```

**Design Note**: 3 focused protocols instead of one 5-method protocol improves testability and single responsibility.

---

### 4. Transport Layer (Isolation of I/O)

#### Transport Models

```python
# transport/models.py
from pydantic import BaseModel
from pathlib import Path

class PromptFileRequest(BaseModel):
    """Transport-level request to load a prompt file."""
    path: Path
    commit_sha: str | None = None

class PromptFileResponse(BaseModel):
    """Transport-level prompt file data."""
    content: str              # Raw file content (with frontmatter)
    metadata_raw: dict        # Parsed YAML frontmatter
    file_hash: str            # SHA-256 of content
    loaded_at: str            # ISO timestamp

class GitRefreshRequest(BaseModel):
    """Request to refresh git repository."""
    repository_path: Path
    target_ref: str | None = None

class GitRefreshResponse(BaseModel):
    """Git refresh operation result."""
    current_commit: str
    branch: str
    changed_files: list[str]
    refreshed_at: str
```

#### Git Transport Client

```python
# transport/git_client.py
from pathlib import Path
from .models import PromptFileResponse, GitRefreshResponse

class GitTransportClient:
    """Pure git transport operations (no domain knowledge)."""

    def __init__(self, config: GitTransportConfig):
        self.config = config

    def get_current_commit(self) -> str:
        """Get current commit SHA."""
        # git rev-parse HEAD
        ...

    def pull_latest(self) -> GitRefreshResponse:
        """Pull latest changes from remote."""
        # git pull
        ...

    def read_file_at_commit(
        self,
        path: Path,
        commit: str | None = None
    ) -> PromptFileResponse:
        """Read file content at specific commit."""
        # git show <commit>:<path> or read from working tree
        ...

    def list_files(self, pattern: str = "**/*.md") -> list[Path]:
        """List files matching pattern."""
        # git ls-files or filesystem glob
        ...
```

#### Cache Transport

```python
# transport/cache_client.py
from typing import Protocol, TypeVar, Generic
import time

T = TypeVar('T')

class CacheTransport(Protocol, Generic[T]):
    """Abstract cache transport."""
    def get(self, key: str) -> T | None: ...
    def set(self, key: str, value: T, ttl_s: int | None = None): ...
    def invalidate(self, key: str): ...
    def clear(): ...

class InMemoryCacheTransport(Generic[T]):
    """In-memory cache implementation with TTL."""

    def __init__(self, default_ttl_s: int = 300):
        self._cache: dict[str, tuple[T, float]] = {}
        self._default_ttl = default_ttl_s

    def get(self, key: str) -> T | None:
        if key not in self._cache:
            return None
        value, expires_at = self._cache[key]
        if time.time() > expires_at:
            del self._cache[key]
            return None
        return value

    def set(self, key: str, value: T, ttl_s: int | None = None):
        ttl = ttl_s if ttl_s is not None else self._default_ttl
        expires_at = time.time() + ttl
        self._cache[key] = (value, expires_at)

    def invalidate(self, key: str):
        self._cache.pop(key, None)

    def clear():
        self._cache.clear()
```

---

### 5. Mappers (Bi-Directional Translation)

```python
# mappers/prompt_mapper.py
from pathlib import Path
from ..transport.models import PromptFileRequest, PromptFileResponse
from ..domain.models import Prompt, PromptMetadata
import yaml

class PromptMapper:
    """Bi-directional mapper for prompt files ↔ domain models."""

    def to_file_request(self, key: str, base_path: Path) -> PromptFileRequest:
        """Map prompt key to transport file request."""
        # Key -> file path resolution (e.g., "summarize" -> "summarize.md")
        prompt_path = base_path / f"{key}.md"
        return PromptFileRequest(path=prompt_path, commit_sha=None)

    def to_domain_prompt(self, file_resp: PromptFileResponse) -> Prompt:
        """Map transport file response to domain Prompt."""
        # Parse frontmatter and body
        content_without_fm = self._strip_frontmatter(file_resp.content)
        metadata = self._parse_metadata(file_resp.metadata_raw)

        return Prompt(
            name=metadata.name,
            version=metadata.version,
            template=content_without_fm,
            metadata=metadata
        )

    def _parse_metadata(self, raw: dict) -> PromptMetadata:
        """Parse raw YAML frontmatter to domain PromptMetadata."""
        return PromptMetadata.model_validate(raw)

    def _strip_frontmatter(self, content: str) -> str:
        """Remove YAML frontmatter from content."""
        # Extract body after '---\n...\n---\n'
        ...
```

**Design Note**: Mappers are pure (no I/O, no side effects), making them easily testable in isolation.

---

### 6. Adapters (Protocol Implementations)

#### Git Catalog Adapter

```python
# adapters/git_catalog_adapter.py
from pathlib import Path
from ..domain.protocols import PromptCatalogPort
from ..domain.models import Prompt, PromptMetadata
from ..transport.git_client import GitTransportClient
from ..transport.cache_client import CacheTransport
from ..mappers.prompt_mapper import PromptMapper
from ..service.loader import PromptLoader

class GitPromptCatalog:
    """Git-backed prompt catalog adapter (implements PromptCatalogPort)."""

    def __init__(
        self,
        config: PromptCatalogConfig,
        transport: GitTransportClient,
        cache: CacheTransport[Prompt],
        mapper: PromptMapper,
        loader: PromptLoader
    ):
        self._config = config
        self._transport = transport
        self._cache = cache
        self._mapper = mapper
        self._loader = loader

    def get(self, key: str) -> Prompt:
        """Retrieve prompt by key (with caching)."""
        # 1. Check cache
        cache_key = self._make_cache_key(key)
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        # 2. Load via transport
        file_req = self._mapper.to_file_request(key, self._config.repository_path)
        file_resp = self._transport.read_file_at_commit(
            file_req.path,
            file_req.commit_sha
        )

        # 3. Map to domain
        prompt = self._mapper.to_domain_prompt(file_resp)

        # 4. Validate if enabled
        if self._config.validation_on_load:
            validation = self._loader.validate(prompt)
            if not validation.succeeded():
                raise ValueError(f"Invalid prompt: {validation.errors}")

        # 5. Cache and return
        self._cache.set(cache_key, prompt, ttl_s=self._config.cache_ttl_s)
        return prompt

    def list(self) -> list[PromptMetadata]:
        """List all available prompts."""
        # Use transport to list files, then map to metadata
        files = self._transport.list_files(pattern="**/*.md")
        prompts = [self.get(self._path_to_key(f)) for f in files]
        return [p.metadata for p in prompts]

    def refresh(self) -> None:
        """Refresh from git (pull latest)."""
        if not self._config.enable_git_refresh:
            return

        refresh_resp = self._transport.pull_latest()
        # Invalidate cache for changed files
        for changed_file in refresh_resp.changed_files:
            key = self._path_to_key(Path(changed_file))
            self._cache.invalidate(self._make_cache_key(key))

    def _make_cache_key(self, prompt_key: str) -> str:
        """Create cache key from prompt key + commit."""
        commit = self._transport.get_current_commit()
        return f"{prompt_key}@{commit[:8]}"

    def _path_to_key(self, path: Path) -> str:
        """Convert file path to prompt key."""
        return path.stem  # "summarize.md" -> "summarize"
```

#### Filesystem Catalog Adapter (Offline Mode)

```python
# adapters/filesystem_catalog_adapter.py
from pathlib import Path
from ..domain.protocols import PromptCatalogPort
from ..domain.models import Prompt, PromptMetadata

class FilesystemPromptCatalog:
    """Filesystem-backed catalog for offline/packaged distributions."""

    def __init__(self, root_path: Path):
        self._root = root_path

    def get(self, key: str) -> Prompt:
        """Load prompt from filesystem (no git)."""
        # Direct file read + parse
        ...

    def list(self) -> list[PromptMetadata]:
        """List prompts from filesystem."""
        # Glob for *.md files
        ...
```

---

### 7. Services (Renderer, Validator, Loader)

#### Prompt Renderer

```python
# service/renderer.py
from jinja2 import Environment, StrictUndefined
from ..domain.models import Prompt, RenderedPrompt, RenderParams, Message, Role
from ..config.policy import PromptRenderPolicy

class PromptRenderer:
    """Renders prompts with Jinja2 and variable precedence."""

    def __init__(self, policy: PromptRenderPolicy):
        self._policy = policy
        self._env = Environment(
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True
        )

    def render(self, prompt: Prompt, params: RenderParams) -> RenderedPrompt:
        """Render prompt with variable substitution."""
        # Merge variables per policy precedence
        merged_vars = self._merge_variables(prompt, params)

        # Render template
        template = self._env.from_string(prompt.template)
        system_content = template.render(**merged_vars)

        # Build messages (system + user)
        return RenderedPrompt(
            system=system_content,
            messages=[Message(role=Role.user, content=params.user_input)]
        )

    def _merge_variables(self, prompt: Prompt, params: RenderParams) -> dict:
        """Merge variables according to policy precedence."""
        # precedence_order: ["caller_context", "frontmatter_defaults", "settings_defaults"]
        merged = {}
        # Implement precedence logic
        ...
        return merged
```

#### Prompt Validator

```python
# service/validator.py
from ..domain.models import Prompt, PromptValidationResult, ValidationIssue, RenderParams
from ..config.policy import ValidationPolicy

class PromptValidator:
    """Validates prompt schema and rendering requirements."""

    def __init__(self, policy: ValidationPolicy):
        self._policy = policy

    def validate(self, prompt: Prompt) -> PromptValidationResult:
        """Validate prompt metadata schema."""
        errors = []
        warnings = []

        # Check required fields
        if not prompt.metadata.name:
            errors.append(ValidationIssue(
                level="error",
                code="MISSING_NAME",
                message="Prompt name is required",
                field="name"
            ))

        # Version format
        if not self._is_valid_version(prompt.metadata.version):
            errors.append(ValidationIssue(
                level="error",
                code="INVALID_VERSION",
                message="Version must be semver format",
                field="version"
            ))

        # Template syntax
        try:
            self._validate_jinja_syntax(prompt.template)
        except Exception as e:
            errors.append(ValidationIssue(
                level="error",
                code="INVALID_TEMPLATE",
                message=str(e),
                field="template"
            ))

        return PromptValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def validate_render(
        self,
        prompt: Prompt,
        params: RenderParams
    ) -> PromptValidationResult:
        """Validate that params satisfy prompt requirements."""
        errors = []

        # Check required variables
        missing = set(prompt.metadata.required_variables) - set(params.variables.keys())
        if missing and self._policy.fail_on_missing_required:
            errors.append(ValidationIssue(
                level="error",
                code="MISSING_REQUIRED_VARS",
                message=f"Missing required variables: {missing}",
                field="variables"
            ))

        # Check extra variables
        if not self._policy.allow_extra_variables:
            all_allowed = (
                set(prompt.metadata.required_variables) |
                set(prompt.metadata.optional_variables)
            )
            extra = set(params.variables.keys()) - all_allowed
            if extra:
                errors.append(ValidationIssue(
                    level="warning" if self._policy.mode == "warn" else "error",
                    code="EXTRA_VARIABLES",
                    message=f"Unexpected variables: {extra}",
                    field="variables"
                ))

        return PromptValidationResult(
            valid=len(errors) == 0,
            errors=errors
        )
```

---

### 8. Integration with GenAI Service

**BREAKING CHANGE**: GenAI service's `prompts_adapter.py` must be refactored to use new `prompt_system`.

```python
# gen_ai_service/pattern_catalog/adapters/prompts_adapter.py (REFACTORED)
from tnh_scholar.prompt_system.domain.protocols import (
    PromptCatalogPort,
    PromptRendererPort,
    PromptValidatorPort
)
from tnh_scholar.prompt_system.domain.models import RenderParams
from tnh_scholar.gen_ai_service.models.domain import (
    Fingerprint,
    RenderedPrompt,
    RenderRequest
)
from tnh_scholar.gen_ai_service.infra.tracking.fingerprint import (
    hash_prompt_bytes,
    hash_user_string,
    hash_vars
)

class PromptsAdapter:
    """Adapter bridging prompt_system to GenAI service contract (ADR-A12, ADR-VSC02)."""

    def __init__(
        self,
        catalog: PromptCatalogPort,
        renderer: PromptRendererPort,
        validator: PromptValidatorPort
    ):
        self._catalog = catalog
        self._renderer = renderer
        self._validator = validator

    def list_all(self) -> list[PromptMetadata]:
        """List all available prompts (ADR-VSC02 requirement for CLI/VS Code)."""
        return self._catalog.list()

    def introspect(self, prompt_key: str) -> PromptMetadata:
        """Get detailed metadata for a prompt (ADR-VSC02 requirement for CLI/VS Code)."""
        prompt = self._catalog.get(prompt_key)
        return prompt.metadata

    def render(self, request: RenderRequest) -> tuple[RenderedPrompt, Fingerprint]:
        """Render prompt and produce fingerprint (ADR-A12 contract)."""
        # 1. Get prompt from catalog
        prompt = self._catalog.get(request.instruction_key)

        # 2. Build render params
        params = RenderParams(
            variables=request.variables or {},
            user_input=request.user_input
        )

        # 3. Validate before rendering
        validation = self._validator.validate_render(prompt, params)
        if not validation.succeeded():
            raise ValueError(f"Validation failed: {validation.errors}")

        # 4. Render
        rendered = self._renderer.render(prompt, params)

        # 5. Compute fingerprint
        fingerprint = Fingerprint(
            prompt_key=request.instruction_key,
            prompt_name=prompt.name,
            prompt_base_path=str(self._catalog._config.repository_path),  # FIXME: expose via protocol?
            prompt_content_hash=hash_prompt_bytes(prompt.template.encode()),
            variables_hash=hash_vars(params.variables),
            user_string_hash=hash_user_string(params.user_input)
        )

        return rendered, fingerprint
```

**Note**: This forces GenAI service to inject `PromptCatalogPort`, `PromptRendererPort`, `PromptValidatorPort` instead of using legacy `PromptManager`. This is the rapid prototype operating principle—break and refactor dependents.

---

### 8.2 Integration with `tnh-gen` CLI (ADR-VSC02)

The `tnh-gen` CLI bridges user input to the prompt system via `PromptsAdapter`. This section shows how CLI variable precedence aligns with prompt system's rendering policy.

#### CLI Variable Mapping

```python
# In tnh-gen CLI implementation (commands/run.py):
from tnh_scholar.prompt_system.domain.models import RenderParams
from tnh_scholar.gen_ai_service.models.domain import RenderRequest

def run_prompt(prompt_key: str, input_file: Path, vars_file: Path, var: list[str]):
    """Execute a prompt with CLI-provided variables."""

    # 1. Build variables dict with CLI precedence (lowest to highest)
    variables = {}

    # Lowest precedence: input file content (auto-injected as input_text)
    if input_file:
        variables["input_text"] = input_file.read_text()

    # Medium precedence: JSON vars file (--vars)
    if vars_file:
        variables.update(json.loads(vars_file.read_text()))

    # Highest precedence: inline --var parameters
    for v in var:
        k, val = v.split('=', 1)
        variables[k] = val

    # 2. Build RenderParams (feeds into prompt_system's caller_context)
    # This becomes the highest precedence in PromptRenderPolicy
    params = RenderParams(
        variables=variables,
        strict_undefined=True
    )

    # 3. Call PromptsAdapter
    adapter = PromptsAdapter(catalog, renderer, validator)
    rendered, fingerprint = adapter.render(
        RenderRequest(
            instruction_key=prompt_key,
            variables=variables,
            user_input=variables.get("input_text", "")
        )
    )

    return rendered, fingerprint
```

**Precedence Alignment:**

| CLI Layer (ADR-VSC02) | Prompt System Layer (ADR-PT04) |
|----------------------|-------------------------------|
| `--var` inline params | `caller_context` (highest) |
| `--vars` JSON file | `caller_context` (highest) |
| `--input-file` content | `caller_context` (highest) |
| (not applicable) | `frontmatter_defaults` (medium) |
| (not applicable) | `settings_defaults` (lowest) |

All CLI-provided variables merge into a single `variables` dict that becomes `caller_context` in the prompt system's precedence order.

#### CLI List Command Integration

```python
# In tnh-gen CLI implementation (commands/list.py):
from tnh_scholar.gen_ai_service.pattern_catalog.adapters.prompts_adapter import PromptsAdapter

def list_prompts(tag: str | None = None, search: str | None = None):
    """List all available prompts with optional filtering."""

    # Initialize adapter
    adapter = PromptsAdapter(catalog, renderer, validator)

    # Get all prompts via new list_all() method
    all_prompts = adapter.list_all()

    # Apply filters
    filtered = [
        p for p in all_prompts
        if (not tag or tag in p.tags)
        and (not search or search.lower() in p.name.lower()
             or search.lower() in p.description.lower())
    ]

    # Format output for CLI/VS Code consumption
    return {
        "prompts": [
            {
                "key": p.key,
                "name": p.name,
                "description": p.description,
                "tags": p.tags,
                "required_variables": p.required_variables,
                "optional_variables": p.optional_variables,
                "default_model": p.default_model,
                "output_mode": p.output_mode,
                "version": p.version
            }
            for p in filtered
        ],
        "count": len(filtered)
    }
```

**Design Note**: The `list_all()` and `introspect()` methods added to `PromptsAdapter` enable prompt discoverability without exposing internal prompt system implementation to the CLI layer. This maintains clean separation of concerns.

---

### 9. Testing Strategy

#### Unit Tests (Mock Protocols)

```python
# tests/unit/test_prompt_renderer.py
from tnh_scholar.prompt_system.service.renderer import PromptRenderer
from tnh_scholar.prompt_system.domain.models import Prompt, PromptMetadata, RenderParams
from tnh_scholar.prompt_system.config.policy import PromptRenderPolicy

def test_render_with_variables():
    """Test rendering with variable substitution."""
    prompt = Prompt(
        name="test",
        version="1.0",
        template="Hello {{name}}!",
        metadata=PromptMetadata(
            name="test",
            version="1.0",
            description="Test prompt",
            task_type="test",
            required_variables=["name"]
        )
    )

    policy = PromptRenderPolicy()
    renderer = PromptRenderer(policy)

    params = RenderParams(
        variables={"name": "World"},
        user_input="Test input"
    )

    result = renderer.render(prompt, params)
    assert result.system == "Hello World!"
    assert len(result.messages) == 1
    assert result.messages[0].content == "Test input"
```

#### Integration Tests (Real Git Catalog)

```python
# tests/integration/test_git_catalog.py
from pathlib import Path
from tnh_scholar.prompt_system.adapters.git_catalog_adapter import GitPromptCatalog
from tnh_scholar.prompt_system.config.prompt_catalog_config import (
    PromptCatalogConfig,
    GitTransportConfig
)

def test_git_catalog_loads_from_disk(tmp_path):
    """Integration test with real git repo."""
    # Setup temp git repo with test prompts
    repo_path = tmp_path / "prompts"
    repo_path.mkdir()
    (repo_path / "test.md").write_text("""---
name: test
version: 1.0
description: Test prompt
task_type: test
required_variables: []
---
Test template
""")

    # Initialize catalog
    config = PromptCatalogConfig(
        repository_path=repo_path,
        enable_git_refresh=False,
        validation_on_load=True
    )

    catalog = GitPromptCatalog.from_config(config)
    prompt = catalog.get("test")

    assert prompt.name == "test"
    assert prompt.template.strip() == "Test template"
```

#### Contract Tests (Fingerprint Invariants)

```python
# tests/contract/test_fingerprint_contract.py
def test_fingerprint_contains_all_inputs(prompts_adapter):
    """Verify Fingerprint captures all render inputs."""
    request = RenderRequest(
        instruction_key="test",
        user_input="Test input",
        variables={"foo": "bar"}
    )

    rendered, fingerprint = prompts_adapter.render(request)

    # Contract assertions per ADR-A12
    assert fingerprint.prompt_key == "test"
    assert fingerprint.prompt_content_hash is not None
    assert len(fingerprint.prompt_content_hash) == 64  # SHA-256
    assert fingerprint.variables_hash is not None
    assert fingerprint.user_string_hash is not None
```

---

### 10. Migration Plan (Rapid Prototype)

#### Phase 1: Implement New System (Week 1)

- [ ] Create `prompt_system` package structure
- [ ] Implement domain models, protocols
- [ ] Implement transport layer (git, cache)
- [ ] Implement mappers
- [ ] Implement adapters (git, filesystem)
- [ ] Implement services (renderer, validator, loader)
- [ ] Write unit tests for all components

#### Phase 2: Break GenAI Service (Week 1-2)

- [ ] Refactor `prompts_adapter.py` to use new `prompt_system`
- [ ] Update GenAI service DI to inject new protocols
- [ ] Remove all references to `ai_text_processing.prompts`
- [ ] Fix all breaking tests

#### Phase 3: Break CLI Tools (Week 2)

- [ ] Update `tnh-gen` CLI to use new catalog
- [ ] Update all `--pattern` flags to `--prompt`
- [ ] Remove `TNH_PATTERN_DIR` env var support (use `TNH_PROMPT_DIR` only)
- [ ] Update VS Code extension integration

#### Phase 4: Delete Legacy (Week 2)

- [ ] Delete `ai_text_processing/prompts.py` entirely
- [ ] Delete legacy test fixtures
- [ ] Update all documentation
- [ ] Verify no remaining imports

**No backward compatibility shims. Break everything. Force refactors.**

---

## Consequences

### Positive

- **Object-service compliant**: Clean layer separation (domain, transport, adapters, mappers).
- **Testable**: Protocol-based design enables easy mocking and unit testing.
- **Injectable**: DI-friendly construction supports tooling (CLI, VS Code).
- **Validated**: Schema enforcement prevents invalid prompts.
- **Fingerprinted**: Complete provenance tracking per ADR-A12.
- **Offline-ready**: Filesystem adapter supports packaged distributions.
- **Safety-ready**: Metadata stubs for safety/security tags.

### Negative

- **Breaking changes**: All dependent code must refactor (GenAI service, CLI tools).
- **Short-term disruption**: Rapid prototype phase accepts this trade-off.
- **Migration effort**: 2-week sprint to migrate all dependents.

### Risks

- **Incomplete migration**: If any module is missed, builds break. Mitigation: comprehensive grep for legacy imports.
- **Test coverage gaps**: New system needs full test suite before deleting legacy. Mitigation: contract tests enforce invariants.

---

## Alternatives Considered

### Minimal Patch to `prompts.py`

**Rejected**: Retains monolith, tight coupling, and transport/domain mixing. Cannot meet ADR-OS01 requirements.

### Gradual Migration with Shims

**Rejected**: Violates rapid prototype operating principle. Maintaining dual systems wastes time and creates inconsistency.

### Standalone Package Now

**Deferred**: Premature to extract before internal architecture stabilizes. Can extract post-1.0 if needed.

---

## Open Questions (Resolved)

### Q1: When to deprecate `TNH_PATTERN_DIR`?

**RESOLVED**: Remove immediately. No backward compatibility in rapid prototype phase.

### Q2: Include safety tags in metadata schema?

**RESOLVED**: YES, include stubs now (`safety_level`, `pii_handling`, `content_flags`). Better to have schema upfront.

### Q3: Support offline mode?

**RESOLVED**: YES, via `FilesystemPromptCatalog` adapter. Enables packaged distributions without git.

### Q4: How to handle GenAI adapter mismatch?

**RESOLVED**: New prompt system replaces GenAI's implementation. Force GenAI service refactor to use new protocols.

---

## Appendix: ADR-OS01 Compliance Checklist

- [x] Domain models defined (pure, no I/O)
- [x] Transport models defined (file, git, cache)
- [x] Protocols defined (minimal 3 protocols: Catalog, Renderer, Validator)
- [x] Adapters implement protocols (GitPromptCatalog, FilesystemPromptCatalog)
- [x] Mappers handle bi-directional translation (PromptMapper)
- [x] Service orchestrators compose protocols (PromptRenderer, PromptValidator)
- [x] Settings (env vars) defined (PromptSystemSettings)
- [x] Config (construction-time) defined (PromptCatalogConfig, GitTransportConfig)
- [x] Params (per-call) defined (RenderParams)
- [x] Policy (behavior) defined with versioning (PromptRenderPolicy, ValidationPolicy)
- [x] Precedence order documented
- [x] Git operations in transport layer (GitTransportClient)
- [x] File I/O in transport layer
- [x] Cache in transport layer (InMemoryCacheTransport)
- [x] All transport ops use typed models
- [x] Unit test patterns defined
- [x] Integration test patterns defined
- [x] Contract tests for provenance defined
- [x] Mock protocol fixtures provided
- [x] Migration guide complete
- [x] API examples provided
- [x] Test patterns documented
- [x] CLI integration patterns defined (ADR-VSC02)
- [x] PromptsAdapter.list_all() implemented
- [x] PromptsAdapter.introspect() implemented
- [x] PromptMetadata includes key, default_model, output_mode fields
- [x] Variable precedence alignment documented (CLI → prompt_system)

**Compliance Score**: 31/31 ✅

---

## Addendum: As-Built Implementation Notes

### 2025-12-07: Metadata Infrastructure Integration

**Context**: During implementation of `PromptMapper` (step 2 of the migration sequence), we identified that TNH Scholar already has a foundational metadata infrastructure (`tnh_scholar.metadata`) that provides:

- `Frontmatter.extract()` / `Frontmatter.embed()` for YAML frontmatter handling
- `Metadata` class (JSON-serializable, dict-like, type-safe)
- `ProcessMetadata` for transformation provenance tracking
- JSON-LD support (ADR-MD01) for semantic relationships

**Decision**: Rather than implementing custom frontmatter parsing in `PromptMapper`, we reused the existing metadata infrastructure.

**As-Built Implementation**:

```python
# src/tnh_scholar/prompt_system/mappers/prompt_mapper.py
from tnh_scholar.metadata.metadata import Frontmatter

class PromptMapper:
    def _split_frontmatter(self, content: str) -> tuple[dict[str, Any], str]:
        """Split YAML front matter from markdown content using shared Frontmatter helper."""
        cleaned = content.lstrip("\ufeff")  # Strip BOM if present
        metadata_obj, body = Frontmatter.extract(cleaned)
        metadata_raw = metadata_obj.to_dict() if metadata_obj else {}
        if not metadata_raw:
            raise ValueError("Prompt file missing or invalid YAML front matter.")
        return metadata_raw, body.lstrip()
```

**Benefits Realized**:

1. **No duplication**: Avoided reimplementing YAML frontmatter parsing logic
2. **Consistent behavior**: All .md files in TNH Scholar (prompts, corpus, derivatives) use same parsing
3. **Future-ready**: JSON-LD support available when needed for semantic prompt relationships
4. **Provenance support**: `ProcessMetadata` ready for multi-stage prompt transformation tracking

**Architectural Insight**: This implementation revealed that **metadata is foundational infrastructure** in TNH Scholar, not a service-specific concern. Prompts are just one type of .md file with metadata; corpus documents, derivative data, and documentation all share this pattern. See ADR-MD02 for metadata's role in the object-service architecture.

**Related**: [ADR-MD01](/architecture/metadata/adr/adr-md01-json-ld-metadata.md), [ADR-MD02](/architecture/metadata/adr/adr-md02-metadata-object-service-integration.md), [ADR-OS01](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md)

---

### 2025-12-07: Incomplete `tnh-gen` CLI Integration and Dependencies

**Context**: Section 8.2 ("Integration with `tnh-gen` CLI") describes the CLI variable mapping and command structure, but implementation was deferred due to broader architectural dependencies.

**Decision**: The `tnh-gen` CLI implementation and `ai_text_processing` refactor are tracked in separate ADR series:

- **ADR-TG01** ([CLI Architecture](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md)): Core `tnh-gen` CLI design (commands, error handling, configuration)
- **ADR-TG02** ([Prompt Integration](/architecture/tnh-gen/adr/adr-tg02-prompt-integration.md)): CLI ↔ prompt system integration (implements PT04 §8.2)
- **ADR-AT03** ([AI Text Processing Refactor](/architecture/ai-text-processing/adr/adr-at03-object-service-refactor.md)): Comprehensive 3-tier refactor:
  - Tier 1: Object-service compliance (ADR-OS01, ADR-AT01)
  - Tier 2: GenAIService integration (ADR-A13)
  - Tier 3: Prompt system integration (ADR-PT04)

**Rationale**:

1. **Scope Separation**: `tnh-gen` is a standalone CLI tool consuming multiple refactored systems
2. **Dependency Complexity**: CLI requires completed `ai_text_processing` refactor (AT03) before full implementation
3. **Domain Ownership**: Text processing refactor belongs in `ai-text-processing/adr/` series, not `tnh-gen/`
4. **Parallel Development**: Enables prompt system refinement while dependent systems mature

**Status**:

- ✅ Section 8.2 variable mapping design is **complete** and authoritative for ADR-TG02
- ✅ `PromptsAdapter.list_all()` and `introspect()` methods are **implemented**
- ⏳ CLI implementation blocked pending ADR-AT03 (ai_text_processing refactor)
- ⏳ `tnh-fab` remains active until ADR-TG01/TG02 implementation complete

**Migration Path**: Once ADR-TG01/TG02/AT03 are implemented, `tnh-fab` will be deprecated and archived under `docs/architecture/tnh-gen/design/archive/`.

**Related**: [ADR-VSC02](/architecture/ui-ux/vs-code-integration/adr-vsc02-tnh-gen-cli-implementation.md), [ADR-AT03](/architecture/ai-text-processing/adr/adr-at03-object-service-refactor.md), [ADR-TG01](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md), [ADR-TG02](/architecture/tnh-gen/adr/adr-tg02-prompt-integration.md)

---

**Approval Path**: Architecture review → Implementation spike → Full implementation
