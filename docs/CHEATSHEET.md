# Aider Brain Cabinet (2026)

## Core Modes
Here are the primary modes for Aider Brain Cabinet:

1. **Local** - 100% Local RTX 5070 Ti. Private and fast.
   ```bash
   local() {
     aider --architect --model ollama_chat/deepcoder:14b --editor-model ollama_chat/qwen3.5:9b --no-auto-accept-architect
   }
   ```

2. **Hybrid** - Gemini 2.5 Pro (Architect) + Local Qwen (Editor). Best for complex features.
   ```bash
   hybrid() {
     aider --architect --model gemini/gemini-2.5-pro --editor-model ollama_chat/qwen3.5:9b --no-auto-accept-architect
   }
   ```

3. **Surgeon** - Direct local editing. No architectural planning.
   ```bash
   surgeon() {
     aider --model ollama_chat/qwen3.5:9b
   }
   ```

4. **Thinker** - Deep reasoning for hard bugs - Gemini Flash
   ```bash
   thinker() {
     aider --model gemini/gemini-2.5-flash --no-auto-accept-architect --no-check-model-accepts-settings
   }
   ```

5. **Auditor** - Safe mode - Read the whole repo, no editing
   ```bash
   auditor() {
     aider --model gemini/gemini-2.5-pro --read-only --map-tokens 4096
   }
   ```

6. **Voice** - Dictate code changes using your Mac's mic
   ```bash
   voice() {
     aider --voice --model ollama_chat/qwen3.5:9b
   }
   ```

7. **BigBrain** - The Heavyweight - Gemini 3.1 Pro
   Best for: "Explain how this whole app works" or "Refactor the entire API layer"
   ```bash
   bigbrain() {
     aider --architect --model gemini/gemini-3.1-pro --map-tokens 8192 --dark-mode --no-auto-accept-architect
   }
   ```

8. **Boss** - The Local Heavyweight - DeepSeekR1 Qwen 2.5 Coder 7B
   Best for: Truly difficult logic bugs where 14B models fail
   ```bash
   boss() {
     aider --architect \
           --model ollama_chat/deepseek-r1:14b \
           --editor-model ollama_chat/qwen2.5-coder:7b \
           --dark-mode \
           --no-auto-accept-architect
   }
   ```

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
