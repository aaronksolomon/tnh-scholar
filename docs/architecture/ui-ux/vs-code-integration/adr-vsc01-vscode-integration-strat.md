# ADR-VSC01: VS Code Integration Strategy (TNH-Scholar Extension v0.1.0)

**Status:** Proposed  
**Author:** Aaron Solomon  
**Date:** 2025-02-XX  
**Tags:** strategy, vscode, genai, architecture, integration  
**Context:** Long-term TNH-Scholar UX roadmap; GenAIService maturity; PromptCatalog stability.

---

## 1. Context

TNH-Scholar is evolving into a multi-layer system with:

- a structured corpus,
- data-processing pipelines,
- a pattern/prompt-driven GenAIService,
- provenance-first transformations,
- and a growing collection of CLI tools and automation flows.

A next logical frontier is **developer-facing integration** within **VS Code**, enabling:

- fast interaction with patterns,
- file-level and selection-level transformations,
- agent-assisted workflows,
- clearer UX pathways for developers, researchers, and contributors,
- and eventually: semi-autonomous loops for corpus processing or code maintenance.

This ADR establishes the **strategic foundation** for VS Code integration and describes the intended shape of v0.1.0 of the TNH-Scholar VS Code Extension.

It is **not** an implementation ADR — it defines the approach, boundaries, responsibilities, and rationale behind the first integration.

---

## 2. Problem / Motivation

Developers and contributors currently:

- run patterns via CLI or Python,
- manually open and inspect results,
- must jump between terminal + editor + documentation,
- have no discoverability for the PromptCatalog,
- and cannot easily apply transformations to the currently open file or selection.

Desired improvements:

1. **Simple UX slice:**  
   Selecting a prompt → running it → producing an output file → opening it automatically.

2. **Discoverability:**  
   QuickPick-like interfaces to browse prompt metadata.

3. **Developer ergonomics:**  
   Minimize friction; enable quick prototyping and evaluation of patterns.

4. **Clear architecture seam:**  
   VS Code should be a thin client — not aware of Python internals — and communicate via well-defined, stable interfaces.

5. **Long-term extensibility:**  
   Future support for:
   - selections,
   - inline replacements,
   - multi-file batches,
   - agentic loops,
   - or fully autonomous flows.

This ADR sets the direction for achieving these goals.

---

## 3. Decision

### **3.1 The VS Code Extension will communicate with TNH-Scholar exclusively via a small CLI interface.**

This is the core architectural decision.

The extension will **not**:

- import Python modules directly,
- embed Python,
- run Python LSP servers,
- or invoke TNH-Scholar internals through ad hoc mechanisms.

Instead, we define a stable CLI integration seam:

### **Core CLI commands (v0.1.0):**

````bash
tnh-genai list-prompts --format json
tnh-genai run --prompt-key <key> --input-file <path> --output-file <path>
````

These commands serve as the *public contract* between VS Code and TNH-Scholar, allowing:

- discoverability (prompt list),
- execution (transformations),
- provenance and fingerprinting (already handled internally),
- predictable IO semantics.

---

### **3.2 The extension’s first MVP command set:**

**Command 1: “TNH Scholar: Run Prompt on Active File”**  

- Uses `list-prompts` to show available patterns  
- Prompts user to select one  
- Executes `tnh-genai run`  
- Opens generated file  

**Command 2: “TNH Scholar: Refresh Prompt Catalog”**  

- Re-runs `list-prompts`  
- Clears any local cache  

This is a **walking skeleton**: minimal, end-to-end, testable.

---

### **3.3 Output Strategy (v0.1.0)**

- Never overwrite the original file.
- Write output files next to the input using a deterministic naming scheme:  

  ```plaintext
  <basename>.<prompt_key>.<ext>
  ```

- Open the output automatically in a split editor.
- Include provenance markers at the top of the generated file (handled by GenAIService).

Later enhancements may support inline edits, diff views, or overwrite confirmations.

---

### **3.4 Prompt Metadata Source of Truth**

PromptCatalog remains the **only authoritative source** for:

- prompt keys,
- human-readable names,
- descriptions,
- tags,
- recommended filetypes (future),
- versioning info (future).

The extension must **never duplicate** prompt metadata.

---

### **3.5 Minimal Workspace Configuration**

For v0.1.0:

- The extension assumes `tnh-genai` exists on the `$PATH`.
- A project-level config (`docs/project/…`, `tnh-scholar.config.json`, or future config layer) may specify:
  - prompt catalog location,
  - default model,
  - environment settings.

Later:
Auto-detect Poetry virtualenv, discover in-project venv, etc.

---

## 4. Rationale

### **4.1 Stability**

The CLI boundary isolates VS Code from Python changes.

### **4.2 Replaceability**

Later, the extension could point to:

- a local HTTP service,
- a remote execution runner,
- an LSP-like agent gateway.

### **4.3 Discoverability & UX**

Developers can browse pattern keys without manual file digging.

### **4.4 Future-Agent Compatibility**

Agent loops require:

- explicit boundaries,
- reproducible inputs and outputs,
- provenance tracking.

The CLI seam provides all three.

### **4.5 Simplicity**

Minimal effort to ship something useful immediately.

---

## 5. Alternatives Considered (and Rejected)

### **5.1 Embedding Python in the extension**

Too heavy and fragile.

### **5.2 HTTP service inside TNH-Scholar**

Likely future enhancement, not needed now.

### **5.3 Direct Node <-> Python RPC**

Adds unnecessary coupling.

---

## 6. Impact

### **On developers**

- Makes patterns easy to run.
- Provides intuitive access to prompt catalog.

### **On codebase**

- Requires a thin CLI wrapper.
- Clarifies boundaries of GenAIService.

### **On documentation**

- Expands CLI docs.
- Adds new VS Code integration docs.

---

## 7. Future Extensions

This ADR defines the **strategic foundation** only.

Later ADRs will cover:

- inline transformations  
- batch operations  
- selection-level transforms  
- evaluation flows  
- agent-assisted loops  
- side-panel prompt browsers  
- notebook integration  
- autonomous orchestration  

---

## 8. Decision Summary

TNH-Scholar will integrate with VS Code via a **minimal, stable CLI boundary**, with a first walking skeleton consisting of:

- `list-prompts`
- `run`

The extension acts as a thin client, avoiding coupling to Python internals.

---

## 9. Status & Next Steps

1. Implement `tnh-genai list-prompts`.  
2. Implement `tnh-genai run`.  
3. Create extension scaffold.  
4. Add QuickPick UI.  
5. Define output file handling.  
6. Document extension.  
7. Follow-up ADRs for richer UX flows.
