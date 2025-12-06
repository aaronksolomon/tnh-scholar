---
title: "Contributing to TNH Scholar (Prototype Phase)"
description: "TNH Scholar is currently in rapid prototype phase, focusing on core functionality and basic usability. We welcome contributions that help validate and improve the prototype implementation."
owner: ""
author: ""
status: processing
created: "2025-01-19"
updated: "2025-12-06"
---
# Contributing to TNH Scholar (Prototype Phase)

TNH Scholar is currently in rapid prototype phase, focusing on core functionality and basic usability. We welcome contributions that help validate and improve the prototype implementation.

## Rapid Prototype Versioning Policy

**IMPORTANT**: During the 0.x release series, TNH Scholar follows **rapid prototype versioning**:

- **Breaking changes are acceptable in ANY 0.x release** (including patch versions)
- **No backward compatibility guarantees** during rapid prototype phase
- **Immediate deprecation and removal** of legacy APIs when replaced
- **All dependents must be updated** when core systems change

See [VERSIONING.md](/VERSIONING.md) for complete policy. This approach enables fast iteration and architectural improvements during prototyping.

## We Need Testers and Experimenters

**You don't need coding experience to contribute meaningfully!** The TNH Scholar project is actively seeking community members to:

- **Explore the software** - Try the CLI tools with real dharma talk content and see what works (and what doesn't)
- **Report your experience** - Share what you discover: pain points, confusing behavior, missing features, or delightful surprises
- **Experiment with workflows** - Test different command pipelines and patterns to process your materials
- **Identify needs** - Help us understand what practitioners and scholars actually need from these tools

Your perspective as a practitioner, translator, or researcher using the tools is invaluable during this prototype phase.

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

### Getting Started as a Tester

1. **Install TNH Scholar**

   ```bash
   pip install tnh-scholar
   ```

2. **Try the Quick Start Guide**

   Follow the [Quick Start Guide](/getting-started/quick-start-guide.md) to get familiar with basic operations

3. **Test with Your Own Materials**

   Experiment with real dharma talk content using commands like:

   ```bash
   # Test basic commands
   tnh-fab punctuate input.txt
   tnh-fab section input.txt
   tnh-fab translate input.txt
   tnh-fab process -p pattern_name input.txt

   # Test pipeline operations
   cat input.txt | tnh-fab punctuate | tnh-fab section
   ```

4. **Explore the Pattern System**

   - Create test patterns in `~/.config/tnh-scholar/patterns/`
   - Test pattern loading and application
   - Try custom workflow combinations

5. **Report What You Find**

   Share your discoveries via [GitHub Issues](https://github.com/aaronksolomon/tnh-scholar/issues):
   - Clear description of the problem or observation
   - Steps to reproduce (include the command used)
   - Expected vs actual behavior
   - Your environment (OS, Python version)
   - Example files (if helpful)

## Code Contributions

At this prototype stage:

- Start with bug fixes
- Keep changes focused
- Include tests for new functionality
- Follow existing code style
- See [style guide](style-guide.md) and [design principles](design-principles.md) for coding standards and architectural patterns.

## Questions and Discussion

- Use GitHub Issues for feature discussions
- Tag issues with 'question' or 'discussion'
- Focus on prototype phase functionality

This is a project in rapid prototype - we're looking for practical feedback on core functionality as well as possible new feature additions and new tools.