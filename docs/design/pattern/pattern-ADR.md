# ADR: Pattern Access Strategy

## Status

Accepted

## Context

The TNH Scholar system needs a pattern management strategy that:

- Supports rapid prototyping now
- Provides clean transition to production architecture
- Maintains system modularity
- Enables proper testing

Currently using a singleton LocalPatternManager for global pattern access.

## Decision

Implement pattern access in two phases:

### Phase 1 (Prototype)

Keep LocalPatternManager in patterns.py for simple global access:

```python
class LocalPatternManager:
    _instance: Optional["LocalPatternManager"] = None
    
    @property
    def pattern_manager(self) -> PatternManager:
        if self._pattern_manager is None:
            self._pattern_manager = PatternManager(TNH_DEFAULT_PATTERN_DIR)
        return self._pattern_manager
```

### Phase 2 (Production)

Transition to configuration-based pattern access:

```python
@dataclass
class ProcessConfig:
    pattern_manager: PatternManager
    model_config: Optional[Dict[str, Any]] = None

class TextProcessor:
    def __init__(self, config: ProcessConfig):
        self.pattern_manager = config.pattern_manager
```

## Rationale

- Phase 1 prioritizes rapid development and testing
- Phase 2 enables proper dependency injection
- Staged approach balances immediate needs with good architecture
- Clear transition path maintains system stability

## Consequences

### Positive

- Simple pattern access during prototyping
- Clean path to proper dependency injection
- Better testing in Phase 2
- Maintains system modularity

### Negative

- Temporary acceptance of global state
- Will require coordinated transition
- Some refactoring needed in Phase 2

### Migration Strategy

1. Keep pattern access centralized in patterns.py
2. Document singleton usage as temporary
3. Implement ProcessConfig when transitioning key components
4. Gradually migrate processors to configuration-based pattern access
