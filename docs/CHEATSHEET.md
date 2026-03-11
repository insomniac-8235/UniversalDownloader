# Hey there! Welcome to Aider Brain Cabinet (2026)

## Core Modes
Here are the primary modes for Aider Brain Cabinet:

1. **RESIDENT** - Resident RTX 5070 Ti. Private and fast.
   - Uses deepcoder:14b (architect) and qwen3.5:9b (editor)

2. **HYBRID** - Gemini 2.5 Pro (Architect) + Local Qwen (Editor). Best for complex features.
   - Combines Gemini's power with local editing efficiency

3. **SURGEON** - Direct local editing. No architectural planning.
   - Uses qwen3.5:9b for focused editing tasks

4. **THINKER** - Deep reasoning for hard bugs - Gemini Flash
   - Specialized for complex problem-solving and reasoning

5. **AUDITOR** - Safe mode - Read the whole repo, no editing
   - Read-only mode for reviewing and analysis

6. **VOICE** - Dictate code changes using your Mac's mic
   - Voice-controlled code editing

7. **BIGBRAIN** - The Heavyweight - Gemini 3.1 Pro
   - Best for: "Explain how this whole app works" or "Refactor the entire API layer"

8. **BOSS** - The Local Heavyweight - DeepSeekR1 Qwen 2.5 Coder 7B
   - Best for: Truly difficult logic bugs where 14B models fail

## Workflow Commands
- `/architect <task>`: The mode you're in. Good for "Plan then Execute."
- `/ask <question>`: Use this for brainstorming (prevents editing)
- `/run <cmd>`: Run your code (e.g., `/run python main.py`)
- `/test <cmd>`: Run with automatic fix loop on failure

## File Management & Context
- `/add <file>`: Bring a file into the "Brain" for editing
- `/read-only <file>`: Let AI analyze without editing
- `/drop <file>`: Free up VRAM after fixes
- `/tokens`: Check usage of your 16GB limit

## Productivity & Debugging Tips
- **/think-tokens 0**: Hide long reasoning blocks
- **/map**: See project files
- **/undo**: Revert changes
- **{**: Start multi-line prompt (paste long errors)
- **Up Arrow**: Cycle previous commands
- **Ctrl-C**: Emergency stop
- **/clear**: Clear chat history
