# AI Startup Investment Copilot - Gemini CLI Workspace

## Project Goal
Build a functional "AI Startup Investment Copilot" demo . The tool should showcase agentic workflows in Deal Sourcing, Analysis, or Due Diligence.

## Workflow Mandates
This project follows a strict subagent-driven development lifecycle using the skills located in `gemini/skills/`.

1. **Research & Brainstorming**: Always start with `brainstorming`. Do NOT write code until a design doc is approved and saved to `docs/plans/`.
2. **Implementation Planning**: Use `writing-plans` to break down the approved design into TDD-based tasks.
3. **Execution**: Use `subagent-driven-development` for task execution, ensuring each task is implemented by a fresh subagent and reviewed for spec compliance and code quality.

## Interview Preparation Focus
- **Technical Depth**: Focus on RAG (Retrieval-Augmented Generation), Agentic Tool Use, and Evaluation.
- **VC Domain Knowledge**: Ensure the AI's output reflects VC-standard metrics (TAM/SAM/SOM, MoM growth, Burn Multiple, etc.).
- **System Design**: Keep the architecture clean and explainable.

## Coding Standards (Strict)
- **File Length**: No individual file should exceed **150 lines**. Refactor into smaller modules if this limit is reached.
- **Component Architecture**: 
  - Each component must have its own directory (e.g., `src/components/MyComponent/`).
  - The component logic must reside in `index.tsx` (or `.js`).
  - **Hooks**: Component-specific hooks must be placed in a `hooks/` subdirectory within the component folder.
  - Use `export default` for all component exports.

## Directory Structure
- `gemini/skills/`: Custom agent skills.
- `docs/plans/`: Design documents and implementation plans.
- `src/`: Application source code.
- `tests/`: TDD test suite.
