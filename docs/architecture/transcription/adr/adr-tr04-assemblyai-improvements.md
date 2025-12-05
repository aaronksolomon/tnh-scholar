---
title: "ADR-TR04: AssemblyAI Service Implementation Improvements"
description: "Refactors the AssemblyAI adapter to use the official SDK, richer options, and better error handling."
owner: ""
author: ""
status: processing
created: "2025-05-01"
---
# ADR-TR04: AssemblyAI Service Implementation Improvements

Modernizes the AssemblyAI integration by adopting the official SDK, exposing advanced options, and hardening error handling.

- **Status**: Proposed
- **Date**: 2025-05-01

## Context

The current implementation of `assemblyai_service.py` provides basic functionality but fails to leverage many powerful features of the AssemblyAI API. After a thorough review of the API documentation and capabilities, we've identified several limitations in the current implementation:

1. **Limited Configuration Options**: The implementation hardcodes many options, including defaulting to English language.
2. **Missing Advanced Features**: No support for many audio intelligence features like sentiment analysis, entity detection, etc.
3. **Inefficient Implementation**: Current implementation doesn't use the official SDK and contains redundant code.
4. **Lack of Error Handling**: Minimal error handling for common failure scenarios.
5. **Missing Regional Support**: No support for EU region endpoints for data residency compliance.
6. **Hardcoded Paths**: API endpoints and configuration options are hardcoded.
7. **Incomplete Documentation**: Documentation doesn't cover all available options.

## Decision Drivers

1. **API Feature Coverage**: Desire to expose as much of AssemblyAI's feature set as possible through our service layer.
2. **Maintainability**: Reduce code complexity and leverage the official SDK.
3. **Type Safety**: Improve type annotations for better IDE support and error checking.
4. **Flexibility**: Enable configuration of all major API parameters.
5. **Error Recovery**: Improve handling of common failure scenarios.
6. **Performance**: Optimize API interactions.
7. **Developer Experience**: Make the service intuitive and well-documented.

## Proposed Decision

We will significantly refactor the AssemblyAI service implementation to address these limitations using the following approaches:

1. **Use Official SDK**: Replace low-level HTTP calls with the official AssemblyAI Python SDK where appropriate.
2. **Enhanced Configuration Model**: Implement a comprehensive configuration model that exposes all major API options.
3. **Complete Feature Coverage**: Add support for all major AssemblyAI features.
4. **Improved Error Handling**: Implement better error handling with specific exception types.
5. **Regional Support**: Add EU region support with configuration options.
6. **Callback Improvements**: Add support for all callback patterns.

## Design Details

### 1. Configuration Model

Create a nested configuration model that exposes all major API options:

```python
@dataclass
class AssemblyAIConfig:
    """Configuration for AssemblyAI service."""
    
    # Base configuration
    api_key: Optional[str] = None
    base_url: str = "https://api.assemblyai.com/v2"  # or EU endpoint
    
    # Connection configuration
    polling_interval: int = 3  # seconds
    max_polling_time: int = 300  # seconds
    
    # Core transcription configuration
    model: Literal["best", "nano"] = "best"
    language_code: Optional[str] = None
    language_detection: bool = False
    language_detection_confidence_threshold: float = 0.5
    
    # Text formatting options
    format_text: bool = True
    punctuate: bool = True
    disfluencies: bool = False
    filter_profanity: bool = False
    
    # Speaker options
    speaker_labels: bool = False
    speakers_expected: Optional[int] = None
    
    # Audio channel options
    multichannel: bool = False
    
    # Accuracy enhancement options
    word_boost: Optional[List[str]] = None
    boost_param: Optional[Literal["low", "default", "high"]] = None
    custom_spelling: Optional[Dict[str, str]] = None
    
    # Audio intelligence configuration
    auto_chapters: bool = False
    auto_highlights: bool = False
    entity_detection: bool = False
    iab_categories: bool = False
    sentiment_analysis: bool = False
    summarization: bool = False
    
    # Callback options
    webhook_url: Optional[str] = None
    webhook_auth_header_name: Optional[str] = None
    webhook_auth_header_value: Optional[str] = None
```

### 2. Service Interface Update

Update the service interface to use the configuration model and support all major features:

```python
class AssemblyAITranscriptionService(TranscriptionService):
    """Enhanced AssemblyAI implementation of the TranscriptionService interface."""
    
    def __init__(self, config: Optional[AssemblyAIConfig] = None):
        """Initialize with comprehensive configuration options."""
        self.config = config or AssemblyAIConfig()
        self._initialize_sdk()
    
    def _initialize_sdk(self) -> None:
        """Initialize the AssemblyAI SDK with current configuration."""
        import assemblyai as aai
        
        # Set API key and base URL
        aai.settings.api_key = self.config.api_key or os.getenv("ASSEMBLYAI_API_KEY")
        if not aai.settings.api_key:
            raise ValueError("AssemblyAI API key is required")
            
        # Set base URL for regional support
        if "eu" in self.config.base_url:
            aai.settings.base_url = "https://api.eu.assemblyai.com/v2"
        
        # Initialize transcriber
        self.transcriber = aai.Transcriber()
    
    def transcribe(
        self,
        audio_file: Union[Path, BinaryIO],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio with full feature support.
        
        Args:
            audio_file: Path or file-like object
            options: Override configuration options
            
        Returns:
            Standardized transcription result
        """
        # Create transcription config by merging base config with options
        import assemblyai as aai
        
        # Prepare configuration
        tx_config = self._prepare_transcription_config(options)
        
        # Handle different input types
        file_path = self._get_file_path(audio_file)
        
        # Perform transcription
        transcript = self.transcriber.transcribe(file_path, config=tx_config)
        
        # Convert to standardized format
        return self._standardize_result(transcript)
```

### 3. Subtitle Generation Enhancement

Improve subtitle generation capabilities:

```python
def get_subtitles(
    self,
    transcript_id: str,
    format_type: str = "srt",
    chars_per_caption: int = 42,
    speaker_labels: bool = False
) -> str:
    """
    Get subtitles directly from AssemblyAI.
    
    Args:
        transcript_id: ID of completed transcript
        format_type: Format type ("srt" or "vtt")
        chars_per_caption: Maximum characters per caption
        speaker_labels: Include speaker labels in subtitle
        
    Returns:
        Formatted subtitle content
    """
    # Direct SDK method if available
    if hasattr(self.transcript, f"export_subtitles_{format_type.lower()}"):
        method = getattr(self.transcript, f"export_subtitles_{format_type.lower()}")
        return method(chars_per_caption=chars_per_caption)
        
    # Fallback to API call
    params = {
        "chars_per_caption": chars_per_caption,
        "speaker_labels": speaker_labels
    }
    
    endpoint = f"{self.config.base_url}/transcript/{transcript_id}/{format_type.lower()}"
    response = requests.get(
        endpoint,
        params=params,
        headers={"authorization": aai.settings.api_key}
    )
    
    response.raise_for_status()
    return response.text
```

### 4. Audio Intelligence Methods

Add support for audio intelligence features:

```python
def get_intelligence_features(
    self,
    transcript: Any
) -> Dict[str, Any]:
    """
    Extract intelligence features if enabled in configuration.
    
    Args:
        transcript: AssemblyAI transcript object
        
    Returns:
        Dictionary with available intelligence features
    """
    features = {}
    
    # Add sentiment analysis
    if hasattr(transcript, "sentiment_analysis") and transcript.sentiment_analysis:
        features["sentiment_analysis"] = transcript.sentiment_analysis
    
    # Add auto chapters
    if hasattr(transcript, "chapters") and transcript.chapters:
        features["chapters"] = transcript.chapters
        
    # Add entity detection
    if hasattr(transcript, "entities") and transcript.entities:
        features["entities"] = transcript.entities
    
    # Add auto highlights
    if hasattr(transcript, "auto_highlights") and transcript.auto_highlights:
        features["highlights"] = transcript.auto_highlights
        
    # Add topic classification
    if hasattr(transcript, "iab_categories") and transcript.iab_categories:
        features["topics"] = {
            "results": transcript.iab_categories.results,
            "summary": transcript.iab_categories.summary
        }
        
    return features
```

### 5. Region Support

Add EU region support with configuration detection:

```python
def _is_eu_region(self) -> bool:
    """Detect if service is configured for EU region."""
    return "eu" in self.config.base_url.lower()

def _get_appropriate_base_url(self) -> str:
    """Get the appropriate base URL based on configuration."""
    if self._is_eu_region():
        return "https://api.eu.assemblyai.com/v2"
    return "https://api.assemblyai.com/v2"
```

### 6. Webhook Support

Add webhook support for asynchronous processing:

```python
def _configure_webhook(self, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Configure webhook parameters if enabled.
    
    Args:
        config: Current configuration dictionary
        
    Returns:
        Updated configuration with webhook parameters
    """
    if self.config.webhook_url:
        config["webhook_url"] = self.config.webhook_url
        
        if self.config.webhook_auth_header_name and self.config.webhook_auth_header_value:
            config["webhook_auth_header_name"] = self.config.webhook_auth_header_name
            config["webhook_auth_header_value"] = self.config.webhook_auth_header_value
            
    return config
```

## Consequences

### Advantages

1. **Complete API Coverage**: Access to all AssemblyAI features through our service layer.
2. **Improved Maintainability**: Less code through SDK usage and better organization.
3. **Type Safety**: Enhanced type annotations for better IDE support.
4. **Configuration Flexibility**: All API options available through configuration.
5. **Better Error Handling**: Specific exception types for common failures.
6. **Regional Compliance**: EU region support for data residency requirements.

### Disadvantages

1. **Migration Effort**: Existing code using the service will need updates.
2. **SDK Dependency**: Introduces dependency on the official SDK.
3. **Complexity**: More configuration options increase initial learning curve.
4. **Version Tracking**: Need to track SDK version compatibility.

## Implementation Plan

1. **Core Service Update**: Replace HTTP calls with SDK usage.
2. **Configuration Model**: Implement comprehensive configuration model.
3. **Feature Implementation**: Add support for all major features.
4. **Testing**: Add tests for new functionality.
5. **Documentation**: Update documentation with new features and examples.
6. **Migration Guide**: Create guide for transitioning from old implementation.

## References

1. [AssemblyAI API Documentation](https://www.assemblyai.com/docs)
2. [AssemblyAI Python SDK](https://github.com/AssemblyAI/assemblyai-python-sdk)
3. [TranscriptionService Interface Design](https://github.com/aaronksolomon/tnh-scholar/blob/main/src/tnh_scholar/audio_processing/transcription/transcription_service.py)
