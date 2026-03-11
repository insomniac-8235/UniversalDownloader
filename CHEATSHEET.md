# Aider Brain Cabinet (2026)

## Core Modes
- `hybrid`: Gemini 2.5 Pro (Architect) + Local Qwen (Editor). Best for complex features.
- `local`: 100% Local RTX 5070 Ti. Private and fast.
- `surgeon`: Direct local editing. No architectural planning.
- `thinker`: Gemini reasoning mode. Best for deep debugging.
- `auditor`: Read-only mode. Exploration without risk of changes.
- `voice`: Hands-free dictation mode.

## Workflow Commands
- `/architect <task>`: The mode you're in. Good for "Plan then Execute."
- `/ask <question>`: Use this for brainstorming. It prevents the Editor from touching your files.
- `/run <cmd>`: Run your code (e.g., `/run python main.py`). Aider sees the output and can fix bugs.
- `/test <cmd>`: Like `/run`, but if it fails, the AI automatically starts a fix loop.

## File Management & Context
- `/add <file>`: Bring a file into the "Brain" for editing.
- `/read-only <file>`: Let the AI see the file (e.g., docs) without wasting energy on editing logic.
- `/drop <file>`: Use this often. Once a file is fixed, drop it to free up VRAM.
- `/tokens`: Check how much of your 16GB limit is being used.

## Productivity & Debugging Tips
- Use `/think-tokens 0` to hide long reasoning blocks.
- Use `/map` to see what files are in the Project Map.
- Use `/undo` to revert the last edit and commit instantly.
- `{`: Type `{` on a blank line to start a multi-line prompt (great for pasting long errors). Type `}` on its own line to finish.
- **Up Arrow**: Cycle through your previous commands.
- **Ctrl-C**: The "Kill Switch." Stops the AI immediately if it goes off the rails.
- `/clear`: Clears the chat history (helps the AI refocus if it gets confused).

## Custom Aliases
I recommend saving these in your Mac's `~/.zshrc`:
- `brain`: Launches your high-speed dual-model setup.
- `brain-slow`: Launches a larger, smarter model (like a 27B or 32B) for when you have a truly difficult logic bug.
