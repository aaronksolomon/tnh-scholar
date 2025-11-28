---
title: "Documentation Design"
description: "Reference for the documentation stack, covering tooling choices, information architecture, and publishing workflow."
owner: ""
author: ""
status: processing
created: "2025-01-19"
---
# Documentation Design

Reference for the documentation stack, covering tooling choices, information architecture, and publishing workflow.

## Tools & Technology Choices

### Static Site Generator
- **Choice**: MkDocs with Material theme
- **Rationale**: 
  - Markdown-based for ease of writing
  - Good integration with Python tooling
  - Modern, responsive design
  - Active community support

### API Documentation
- **Choice**: MkDocstrings
- **Rationale**:
  - Native MkDocs integration
  - Support for Google-style docstrings
  - Clean, hierarchical output
  - Good code navigation features

### Version Control
- **Choice**: Git + GitHub Pages
- **Rationale**:
  - Free hosting
  - Automatic deployment
  - Version tracking
  - PR-based reviews

## Structure Decisions

### Documentation Types
1. User Documentation (Markdown)
   - Installation guides
   - User manuals
   - Tutorials

2. API Documentation (Docstrings)
   - Class/function documentation
   - Code examples
   - Type hints

3. Development Documentation
   - Architecture decisions
   - Contribution guides
   - Development setup

### File Organization
- User-facing content in /user_guide
- API reference in /api
- Development docs in /development

