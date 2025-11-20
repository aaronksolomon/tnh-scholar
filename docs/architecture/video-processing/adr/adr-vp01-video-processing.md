---
title: "ADR-VP01: Video Processing Return Types and Configuration"
description: "Centralizes yt-dlp configuration and return types so video tooling emits consistent metadata."
owner: ""
author: ""
status: processing
created: "2025-02-01"
---
# ADR-VP01: Video Processing Return Types and Configuration

Unifies yt-dlp configuration and return shapes so download, transcript, and metadata operations stay consistent.

- **Status**: Proposed
- **Date**: 2025-02-01

### Context

The video processing module currently handles YouTube operations (transcript retrieval, audio download) through separate functions with different return types and repeated configuration settings. Each operation independently manages yt-dlp options and metadata extraction.

Current structure:

- Independent functions for download, transcript, and metadata operations
- Repeated yt-dlp configuration in multiple places
- No standardized metadata collection
- Different return types per function

### Decision

We will:

#### 1. Create centralized configuration constants for yt-dlp options

```python
DEFAULT_YDL_OPTIONS = {...}
TRANSCRIPT_OPTIONS = DEFAULT_YDL_OPTIONS | {...}
AUDIO_DOWNLOAD_OPTIONS = DEFAULT_YDL_OPTIONS | {
    "format": "bestaudio/best",
    "postprocessors": [...],
    "noplaylist": True,
    ...
}
```

#### 2. Define a standard return type using dataclass

```python
@dataclass
class VideoResult:
    metadata: Dict[str, Any]
    content: Optional[str] = None  # For transcripts
    filepath: Optional[Path] = None  # For downloads
```

#### 3. Establish configurable metadata selection

```python
DEFAULT_METADATA_FIELDS = [...]
DUBLIN_CORE_MAPPING = {...}
```

### Consequences

Positive:

- Single source of truth for yt-dlp configurations
- Consistent metadata collection across operations
- Unified return type simplifies function interfaces
- Easier configuration management through constants
- Better support for Dublin Core metadata standards

Negative:

- Requires refactoring existing function calls
- Slightly more complex return type handling
- May need migration period for API changes

### Notes

This change builds on the existing video_processing.py structure while standardizing the interface and reducing configuration duplication. It maintains the module's current functionality while making it more maintainable and consistent.

### Related Documents

- video_processing.py
- TextObject New Design.md (for Dublin Core metadata alignment)

## ADR 002: YouTube Interface Redesign

### Status

Proposed

### Context

The current YouTube interface implementation in TNH Scholar, while functional, has become unwieldy and complex. The implementation mixes concerns across different tools and lacks a clear architectural boundary. As the system grows and evolves, we need a more maintainable and extensible approach to handling YouTube content acquisition.

The current implementation has several issues:

- Mixed responsibilities between content acquisition and processing
- Duplicated code across tools (audio-transcribe and ytt-fetch)
- Complex error handling and configuration management
- Limited flexibility for future enhancements or backend changes

This decision is being made in the context of our broader system architecture, which emphasizes modular design and the potential for continuous improvement through AI processing and training data generation.

### Decision

We will implement a new YouTube interface based on a clear abstraction layer with separate interface definition and implementation. The core of this design will be an abstract YouTubeDownloader class with a concrete implementation using yt-dlp.

The new architecture will consist of:

```python
class YTDownloader:
    """Abstract base class for YouTube content retrieval."""
    
    def get_transcript(self, url: str, lang: str = "en") -> VideoTranscript:
        """Retrieve video transcript with associated metadata."""
        pass
        
    def get_audio(self, url: str) -> VideoAudio:
        """Extract audio with associated metadata."""
        pass
        
    def get_metadata(self, url: str) -> VideoMetadata:
        """Retrieve video metadata only."""
        pass
```

With an initial implementation:

```python
class DLPDownloader(YTDownloader):
    """yt-dlp based implementation of YouTube content retrieval."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or DEFAULT_CONFIG
        self._setup_ytdlp()
```

### Consequences

#### Positive

- Clear separation of concerns improves maintainability
- Consistent interface across tools reduces code duplication
- Abstract base class enables future backend alternatives
- Standardized metadata handling across operations
- Simpler integration with existing tools
- Clearer path for future enhancements

#### Negative

- Initial overhead of creating abstraction layer
- Need to refactor existing tools to use new interface
- Potential for increased complexity in configuration management
- May need to maintain backward compatibility during transition

#### Neutral

- Shifts complexity from implementation to interface design
- Changes how tools interact with YouTube functionality
- Requires updates to documentation and examples

### Implementation Approach

The implementation will proceed in phases:

1. Create core interface and yt-dlp implementation
2. Refactor audio-transcribe to use new interface
3. Update ytt-fetch to align with new design
4. Enhance metadata handling and persistence
5. Add support for additional features (playlists, caching)

### Alternatives Considered

1. Enhance Existing Implementation
   - Would require less immediate work
   - Wouldn't address fundamental design issues
   - Would limit future flexibility

2. Multiple Specialized Interfaces
   - Could optimize for specific use cases
   - Would increase complexity and duplication
   - Would make maintenance more difficult

3. Direct yt-dlp Integration
   - Simpler implementation
   - Would limit flexibility for backend changes
   - Would maintain current architectural issues

### Related Decisions

- Overall TNH Scholar system architecture
- Pattern system design
- Metadata standardization
- Content processing pipeline design

### Additional Notes

This design aligns with our system's broader goals of modularity, extensibility, and support for AI-driven improvement. The abstract interface approach provides a foundation for future enhancements while maintaining the simplicity needed for rapid prototyping.

## ADR 003: Resource Management Strategy Aligned with Use Cases

### Status

Proposed

### Context

The TNH Scholar project serves three distinct use cases with different requirements for resource management:

1. CLI tools for technical users who manage their own data
2. GUI interface for users who need structured defaults
3. API access for programmatic integration

The current implementation lacks clear separation between system configuration and data management. We need to establish principles that serve all use cases while maintaining flexibility.

### Decision

We will implement a tiered approach to resource management that separates system configuration from data storage and adapts to each use case's needs.

**System Configuration**

All system configuration will reside in ~/.config/tnh-scholar/:

- Processing patterns
- Tool configurations
- Logging settings
- Default operational parameters

**Data Management Strategy**

For CLI Tools (Primary Use Case):

- Default to working directory for all operations
- Allow explicit path specification through command options
- Maintain pipeline-friendly interfaces
- Keep data management under user control
- Use system config only for operational settings

For GUI Interface (Secondary Use Case):

- Provide structured defaults in ~/Library/Application Support/tnh-scholar/
- Maintain clear separation between user data and system configuration
- Allow advanced users to modify defaults through configuration
- Implement automated data management for ease of use

For API Usage (Tertiary Use Case):

- Provide flexible interfaces for resource management
- Allow complete configuration of data locations
- Make no assumptions about storage locations
- Focus on functional interfaces over data management

### Consequences

Positive:

- Clear separation of configuration and data
- Flexibility for different user needs
- Simplified CLI tool development
- Structured defaults for GUI users
- Clean API interfaces

Negative:

- More complex initial setup for GUI interface
- Need to maintain multiple data management approaches
- Potential for confusion about data locations
- Additional documentation requirements

### Implementation Notes

The implementation will follow these principles:

- System configuration always uses ~/.config/tnh-scholar/
- CLI tools prioritize working directory operations
- GUI interface provides structured defaults
- API remains neutral on data location
- All tools support explicit path specification

### Related Decisions

- ADR 001: Video Processing Return Types and Configuration
- ADR 002: YouTube Interface Redesign

### Additional Notes

This design supports the project's rapid prototyping phase by:

- Maintaining simplicity for CLI tools
- Providing clear extension points for GUI development
- Keeping API interfaces clean and flexible
- Allowing for future enhancement of data management

The approach can evolve as the project matures, with potential for:

- Enhanced metadata management
- More sophisticated data organization
- Improved resource tracking
- Advanced configuration options
