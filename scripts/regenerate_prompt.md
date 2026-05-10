# Spec Regeneration Prompt

You are an expert software engineer. Given the system specification below, generate a complete, working implementation of the SA New Resident Agent system.

## Instructions

1. Read the specification carefully, paying attention to:
   - Component Inventory (module paths)
   - Public Interfaces (API endpoints and their request/response schemas)
   - Data Flow (how components interact)
   - Model and Prompt Selection (LLM config, prompts, chunking parameters)

2. Generate source code for each component listed in the Component Inventory.

3. Each generated file must:
   - Match the module path specified in the Component Inventory
   - Implement all interfaces defined in Section 4 (Public Interfaces)
   - Use the exact prompt templates defined in Section 5.3
   - Use the exact chunking parameters defined in Section 5.4

4. The generated code must pass the user story acceptance tests in `tests/user_stories/`.

5. Do not add features not described in the spec. Do not change API signatures.

## Specification

{SPEC_CONTENT}

## Output Format

Generate each file as a separate code block with the file path as the header:

```python
# path/to/module.py
[code here]
```
