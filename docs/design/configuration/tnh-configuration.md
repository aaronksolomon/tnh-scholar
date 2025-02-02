# TNH Configuration Management

## ADR 002: Overall Strategy

### Status

Proposed

### Context

The tnh-scholar project currently uses module-level constants for configuration, defined at module headers. As the project grows, we need a structured approach to configuration management that maintains simplicity while providing necessary flexibility.

Current approach:

- Module-level constants (e.g., DEFAULT_YDL_OPTIONS, DEFAULT_PATTERN_DIR)
- Some environment variables for critical values (e.g., OPENAI_API_KEY)
- CLI flags for runtime behavior (e.g., --verbose)

### Decision

We will implement configuration management in phases, prioritizing simplicity and common use cases over excessive flexibility.

#### Phase 1: Current (Prototype)

- Continue using module-level constants for defaults
- Maintain minimal environment variables (only for essential credentials)
- Pass CLI flags through call chain where needed

#### Phase 2: User Configuration (Next Step)

Implement user configuration file:

```yaml
# ~/.config/tnh_scholar/settings/config.yaml
video_processing:
  yt_dlp_verbose: false
  default_language: en
patterns:
  path: ~/.config/tnh_scholar/patterns
```

Standard locations:

- Linux/Mac: ~/.config/tnh_scholar/settings/config.yaml
- Windows: %APPDATA%/tnh_scholar/settings/config.yaml

Configuration precedence:

1. CLI arguments (highest)
2. User config file (~/.config/tnh_scholar/settings/config.yaml)
3. Module defaults (lowest)

#### Phase 3: Component Configuration (Future)

Introduce configuration classes for major components:

```python
@dataclass
class VideoConfig:
    verbose: bool = False
    default_language: str = "en"
    yt_dlp_options: Dict[str, Any] = field(default_factory=dict)
```

### Explicitly Out of Scope

- Project-level configuration files
- Complex environment variable mapping
- Multiple configuration file locations
- Configuration profiles/environments

### Rationale

- Keep configuration simple and predictable
- Minimize cognitive overhead for users
- Focus on common use cases
- Avoid configuration sprawl

### Consequences

Positive:

- Clear, simple configuration path
- Single user configuration file
- Predictable behavior
- Easy to maintain and document

Negative:

- Less flexibility for advanced users
- Some use cases may require code changes
- Limited environment-specific configuration

### Implementation Notes

#### 1. Configuration File Location

- Single location: ~/.config/tnh_scholar/config.yaml
- Created by tnh-setup command
- Simple YAML format
- Clear documentation of available options

#### 2. Configuration Loading

```python
def load_config() -> Dict[str, Any]:
    """Load configuration with simple precedence."""
    config_path = Path.home() / ".config/tnh_scholar/config.yaml"
    defaults = get_default_config()
    
    if config_path.exists():
        user_config = yaml.safe_load(config_path.read_text())
        return {**defaults, **user_config}
    return defaults
```

#### 3. CLI Integration

```python
@click.option("--verbose", is_flag=True)
def command(verbose: bool):
    """CLI flags override config file."""
    config = load_config()
    if verbose:
        config["verbose"] = True
```

### Migration Strategy

1. Document all current module-level constants
2. Create template config file with current defaults
3. Implement config file loading
4. Update modules to use configuration values
5. Add configuration classes as needed

### Related Documents

- ADR 001: Video Processing Return Types and Configuration
- installation.md (for tnh-setup documentation)

This ADR emphasizes your preference for simplicity while providing a clear path for necessary configuration management. It explicitly excludes potentially complex configuration options to maintain focus on making the tool approachable and maintainable.

Does this align with your vision for the project's configuration management? Would you like me to adjust any aspects of it?
