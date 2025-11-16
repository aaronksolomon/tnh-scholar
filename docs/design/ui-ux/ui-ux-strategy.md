
# Design Strategy: VS Code as UI/UX Platform for TNH Scholar

---

## Abstract

This document proposes a comprehensive UI/UX design strategy for the TNH Scholar project, advocating for Visual Studio Code (VS Code) as the core user experience platform. It outlines the rationale, layering approach, user profiles, and surface strategies that leverage VS Code’s extensibility and ecosystem to deliver a powerful, maintainable, and familiar environment for scholarly editing, reading, and collaboration.

## Context and Motivation

UI/UX is central to the TNH Scholar mission: enabling scholars, editors, and readers to interact fluidly with complex, multilingual, and richly annotated textual corpora. Previous approaches using bespoke FastAPI/Tailwind viewers, though valuable for surfacing data issues, demanded significant engineering effort to achieve even basic UI/UX parity with modern editors. These solutions suffered from slow iteration, limited feature sets, and high maintenance overhead. In contrast, VS Code offers a thriving extension ecosystem, robust editor features, and a familiar interface for many users. Its support for extension packs, custom profiles, and webviews makes it uniquely suited to serve as both a deep editorial platform and a customizable reading environment.

## Design Strategy

We propose adopting VS Code as the primary UI/UX base for TNH Scholar. This involves:

- Developing a suite of TNH Scholar extensions targeting key layers of functionality.
- Packaging these extensions into curated profiles and extension packs for different user cohorts.
- Leveraging VS Code’s webview APIs for custom document viewers and interactive panels.
- Using VS Code’s settings, keybindings, and workspace configurations to tailor experiences for diverse roles.
This strategy ensures rapid feature development, maintainability, and access to a mature ecosystem, while allowing us to focus on domain-specific value rather than reinventing core editor capabilities.

## Layering Approach

The functional architecture is mapped to discrete VS Code extensions, each corresponding to a layer of the user experience:

1. **Viewer Extension**: Parallel text viewer (e.g., Vietnamese/English, images, annotations), leveraging custom editors and webviews.
2. **Corpus & TOC Extension**: Navigation of corpora, table of contents, and structural metadata.
3. **Authoring & Metadata Extension**: Editing, annotation, and metadata management tools.
4. **Search & Insights Extension**: Advanced search, concordance, and data insights panels.
5. **Pipelines Extension**: Integration with data processing and the TNH pattern system, validation, and export pipelines.
6. **Collaboration Extension**: Real-time or asynchronous collaboration features, comments, and versioning.
Extensions are bundled into extension packs and surfaced via curated profiles.

## Profiles and User Cohorts

To accommodate diverse workflows, we define simplified, curated VS Code profiles for major user roles:

- **Reader/Annotator**: Clean, distraction-free interface; parallel viewer; annotation tools.
- **Scholar/Editor**: Full editorial features; metadata editing; advanced search; scripting support.
- **Maintainer**: Data validation, pipeline integration, and export tools.
Profiles are distributed as extension packs with pre-configured settings, keybindings, and UI layouts, reducing onboarding friction and ensuring consistency across user cohorts.

## Web vs Desktop Surfaces

Our dual-surface strategy balances accessibility and power:

- **VS Code Web (vscode.dev)**: Instant, installation-free access for lightweight reading, annotation, and review tasks.
- **VS Code Desktop**: Full-featured editorial environment, supporting local workflows, advanced scripting, and deep extension integration.
This approach enables casual users to engage with the corpus easily while providing power users with the tools needed for high-touch editorial work. Trade-offs include limited local file access and extension support on the web, versus richer capabilities and offline access on desktop.

## Evaluation Test for Viability

A quick “walking skeleton” test will validate the approach: implement a custom editor extension that opens a `bundle.json` file, displaying parallel Vietnamese/English text alongside images in split panes. This minimal prototype exercises the core VS Code APIs (custom editors, webviews, extension activation) and demonstrates the feasibility of the layered, extension-based approach.

## Rationale

Adopting VS Code as the UI/UX platform is preferable to forking the codebase or persisting with web-only solutions for several reasons:

- **Maintainability**: Leverages ongoing improvements and bug fixes from the VS Code core and extension ecosystem.
- **Ecosystem**: Access to a vast library of extensions (e.g., language support, version control, formatting).
- **Speed**: Focuses engineering effort on domain-specific features, reducing time-to-value.
- **Familiarity**: Many users are already comfortable with VS Code, lowering the learning curve.
Forking VS Code would incur significant long-term maintenance costs, while web-only solutions struggle to match the maturity and feature set of VS Code’s editor and extension APIs.

## Historical Discussion Notes

Initial work with FastAPI/Tailwind-based viewers surfaced important data and modeling issues but required substantial engineering to approach the UX and productivity of modern editors. Feature iteration was slow, and the gap between custom-built viewers and user expectations remained wide. In contrast, VS Code provides a robust, extensible foundation, allowing us to deliver rich experiences with less effort by building on a mature platform.

## Open Questions and Alternatives

Several open issues and alternatives remain:

- **Real-time Collaboration**: To what extent can VS Code extensions support multi-user, real-time editing? Is Live Share sufficient?
- **Multi-user Editing**: How will session management, conflict resolution, and user attribution be handled?
- **Publishing/Export Integration**: What is the best way to integrate publishing pipelines—extension, external app, or hybrid?
- **Extension vs External Web App Roles**: Where should the boundary lie between VS Code extensions and standalone web apps for specialized tasks or public access?
- **Accessibility and Onboarding**: Are there user groups for whom VS Code is a barrier? How can onboarding and accessibility be improved?

## Next Steps

This document serves as a strategic foundation. The next phase involves authoring detailed Architectural Decision Records (ADRs) to specify and refine key components, such as:

- ADR: “Parallel Viewer Extension Skeleton”
- ADR: “Profiles and Extension Pack Packaging”
- ADR: “Corpus Navigation and TOC Extension”
These ADRs will guide the technical implementation and inform ongoing evaluation of the VS Code-based strategy.
