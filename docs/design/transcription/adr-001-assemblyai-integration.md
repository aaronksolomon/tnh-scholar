# Transcription ADR 001: AssemblyAI Integration for Transcription Service

## Status

Proposed

## Context

The TNH Scholar project currently uses OpenAI's Whisper API for audio transcription services, while using PyAnnote for speaker diarization. We wish to explore alternative transcription providers to potentially improve quality, gain additional features, and create a more modular architecture that allows for multiple transcription backends.

AssemblyAI offers a comprehensive speech-to-text API with advanced features including high-quality transcription, support for multiple languages, and additional capabilities such as entity detection that could be valuable in future development. Integrating AssemblyAI as an alternative transcription backend would provide flexibility while allowing us to continue using PyAnnote for language-independent diarization.

## Decision Drivers

1. Need for a pluggable transcription service architecture that supports multiple backends
2. Desire to access AssemblyAI's transcription quality and feature set
3. Requirement to maintain compatibility with the existing diarization system
4. Support for rapid prototyping while enabling future production-quality implementations
5. Consistent authentication and configuration management across services

## Proposed Decision

We will create a modular transcription service architecture with AssemblyAI as an additional backend option. The implementation will:

1. Define an abstract `TranscriptionService` interface that various providers can implement
2. Create concrete implementations for both OpenAI Whisper (current) and AssemblyAI (new)
3. Implement a factory pattern to select the appropriate service at runtime
4. Support consistent configuration and authentication across services

## Design Details

### Class Structure

```
TranscriptionService (ABC)
├── WhisperTranscriptionService
└── AssemblyAITranscriptionService
```

### Interface Definition

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional, Any, BinaryIO, Union

class TranscriptionService(ABC):
    """Abstract base class defining the interface for transcription services."""
    
    @abstractmethod
    def transcribe(
        self,
        audio_file: Union[Path, BinaryIO],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio file to text.
        
        Args:
            audio_file: Path to audio file or file-like object
            options: Provider-specific options for transcription
            
        Returns:
            Dictionary containing transcription results with standardized keys
            and provider-specific data
        """
        pass
    
    @abstractmethod
    def get_result(self, job_id: str) -> Dict[str, Any]:
        """
        Get results for an existing transcription job.
        
        Args:
            job_id: ID of the transcription job
            
        Returns:
            Dictionary containing transcription results
        """
        pass
```

### Factory Implementation

```python
class TranscriptionServiceFactory:
    """Factory for creating transcription service instances."""
    
    @staticmethod
    def create_service(
        provider: str = "whisper",
        api_key: Optional[str] = None,
        **kwargs
    ) -> TranscriptionService:
        """
        Create a transcription service instance.
        
        Args:
            provider: Service provider ("whisper" or "assemblyai")
            api_key: API key for the service
            **kwargs: Additional provider-specific configuration
            
        Returns:
            TranscriptionService instance
        """
        if provider.lower() == "whisper":
            from .whisper_service import WhisperTranscriptionService
            return WhisperTranscriptionService(api_key=api_key, **kwargs)
        elif provider.lower() == "assemblyai":
            from .assemblyai_service import AssemblyAITranscriptionService
            return AssemblyAITranscriptionService(api_key=api_key, **kwargs)
        else:
            raise ValueError(f"Unsupported transcription provider: {provider}")
```

### Authentication Management

Authentication will be managed using environment variables with consistent naming conventions:

- `OPENAI_API_KEY` - for OpenAI Whisper API (existing)
- `ASSEMBLYAI_API_KEY` - for AssemblyAI API (new)

The system will look for these variables directly or in a `.env` file, with appropriate fallbacks and error messages.

### Configuration Design

Configuration will be managed through a hierarchical approach:

1. Default configurations defined at the class level
2. Configuration via constructor parameters
3. Per-request options for fine-grained control

### AssemblyAI Implementation

The AssemblyAI implementation will use the AssemblyAI REST API with the following components:

1. File upload endpoint (`https://api.assemblyai.com/v2/upload`)
2. Transcription endpoint (`https://api.assemblyai.com/v2/transcript`)
3. Polling mechanism for async job completion
4. Result standardization for compatibility with existing systems

## Consequences

### Advantages

1. **Modularity**: Clear separation of concerns with a pluggable architecture
2. **Feature Access**: Enables use of AssemblyAI's advanced features
3. **Flexibility**: Allows switching between providers without changing client code
4. **Future-proofing**: Architecture supports adding additional providers
5. **Consistency**: Standardized result format regardless of backend

### Disadvantages

1. **Complexity**: Additional abstraction layer increases system complexity
2. **Integration Effort**: Requires implementing and testing a new service
3. **Maintenance Overhead**: Multiple implementations to maintain
4. **Dependency Management**: New external dependency to manage

### Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| API compatibility changes | Encapsulate provider-specific code in concrete implementations |
| Authentication failures | Clear error messages and validation for API keys |
| Result format inconsistencies | Standardized result mapping in each implementation |
| Performance differences | Documentation of expected behavior differences |

## Implementation Plan

### Phase 1: Core Interface (Week 1)

1. Define the `TranscriptionService` abstract base class
2. Create a simple adapter for the existing Whisper implementation
3. Implement basic factory pattern

### Phase 2: AssemblyAI Integration (Week 2)

1. Implement `AssemblyAITranscriptionService` for basic transcription
2. Add authentication and configuration management
3. Implement result standardization

### Phase 3: Feature Parity and Testing (Week 3)

1. Ensure feature parity with the current Whisper implementation
2. Add comprehensive testing
3. Update documentation

### Phase 4: Integration with Existing Systems (Week 4)

1. Modify `audio_transcribe.py` to use the new abstraction
2. Add configuration options for selecting the transcription provider
3. Validate integration with the diarization system

## References

1. [AssemblyAI API Documentation](https://www.assemblyai.com/docs/api-reference/overview)
2. [Current OpenAI Whisper Integration Code](src/tnh_scholar/audio_processing/transcription.py)
3. [Diarization System Design](docs/design/diarization-system1.md)