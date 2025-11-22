---
title: "Contributing to TNH Scholar (Prototype Phase)"
description: "TNH Scholar is currently in rapid prototype phase, focusing on core functionality and basic usability. We welcome contributions that help validate and improve the prototype implementation."
owner: ""
author: ""
status: processing
created: "2025-01-19"
---
# Contributing to TNH Scholar (Prototype Phase)

TNH Scholar is currently in rapid prototype phase, focusing on core functionality and basic usability. We welcome contributions that help validate and improve the prototype implementation.

## Current Focus Areas

1. **TNH-FAB Command Line Tool**
    - Basic functionality testing
    - Error case identification
    - Command pipeline testing
    - Pattern system integration

2. **Pattern System**
    - Pattern usage testing
    - Pattern creation testing
    - Version control functionality
    - Concurrent access testing

3. **AUDIO-TRANSCRIBE Command Line Tool**
    - Basic functionality testing
    - Error case identification

## How to Help

### Testing

#### 1. Install the package

```bash
   pip install tnh-scholar
```

#### 2. Try basic operations

```bash
    # Test basic commands
    tnh-fab punctuate input.txt
    tnh-fab section input.txt
    tnh-fab translate input.txt
    tnh-fab process -p pattern_name input.txt

    # Test pipeline operations
    cat input.txt | tnh-fab punctuate | tnh-fab section
```

#### 3. Report issues

- Use GitHub Issues
- Include command used
- Provide minimal example that reproduces the issue
- Note your environment (OS, Python version)

### Pattern Testing

1. Create test patterns in `~/.config/tnh-scholar/patterns/`
2. Test pattern loading and application
3. Report any issues with pattern system

## Reporting Issues

Create issues on GitHub with:

- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Example files (if needed)

## Code Contributions

At this prototype stage:

- Start with bug fixes
- Keep changes focused
- Include tests for new functionality
- Follow existing code style
- See [design guide](/development/design-guide) for coding style and requirements.

## Questions and Discussion

- Use GitHub Issues for feature discussions
- Tag issues with 'question' or 'discussion'
- Focus on prototype phase functionality

This is a project in rapid prototype - we're looking for practical feedback on core functionality as well as possible new feature additions and new tools.