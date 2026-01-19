
import gradio as gr
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import time

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agent_factory.core.agent_factory import AgentFactory
from agent_factory.workers.openhands_worker import OpenHandsWorker

load_dotenv()

def run_agent_task(repo_path, task_desc, model_selection):
    """
    Wrapper to run the agent task and return logs.
    """
    if not repo_path or not task_desc:
        return "❌ Error: Please provide both Repository Path and Task Description."
    
    if not os.path.isdir(repo_path):
        return f"❌ Error: Directory not found: {repo_path}"

    model_id = model_selection.split(" ")[0]
    use_ollama = "Free/Local" in model_selection

    logs = []
    logs.append(f"🚀 Starting Agent...")
    logs.append(f"📂 Workspace: {repo_path}")
    logs.append(f"🤖 Model: {model_id}")
    logs.append(f"📝 Task: {task_desc}")
    logs.append("-" * 40)
    
    yield "\n".join(logs)
    
    try:
        factory = AgentFactory(verbose=True)
        worker = factory.create_openhands_agent(
            model=model_id,
            use_ollama=use_ollama,
            workspace_dir=Path(repo_path)
        )
        
        logs.append("⏳ Agent is working... (Task started)")
        yield "\n".join(logs)
        
        # Synchronous execution
        # In a real async setup, we'd stream logs. 
        # Here we just wait and show result.
        result = worker.run_task(task_desc, timeout=600)
        
        if result.success:
            logs.append("\n✅ Task Completed Successfully!")
            logs.append(f"Message: {result.message}")
            if result.files_changed:
                logs.append("\nFiles Modified:")
                for f in result.files_changed:
                    logs.append(f"- {f}")
        else:
            logs.append("\n❌ Task Failed.")
            logs.append(f"Message: {result.message}")
            if result.logs:
                logs.append(f"\nDebug Logs:\n{result.logs[-1000:]}")
                
    except Exception as e:
        logs.append(f"\n❌ Exception occurred: {str(e)}")
        
    yield "\n".join(logs)

# --- Gradio UI ---

with gr.Blocks(title="Agent Factory", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 🏭 Agent Factory
        ### Autonomous Coding Agents Powered by Ollama
        """
    )
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### ⚙️  Configuration")
            repo_input = gr.Textbox(
                label="Repository / Workspace Path", 
                value=os.getcwd(),
                placeholder="/path/to/your/project"
            )
            model_input = gr.Dropdown(
                label="Select Model", 
                choices=[
                    "deepseek-coder:6.7b (Free/Local)",
                    "deepseek-coder:33b (Free/Local - Requires 32GB RAM)",
                    "claude-3-5-sonnet (Paid API)",
                    "gpt-4o (Paid API)"
                ],
                value="deepseek-coder:6.7b (Free/Local)"
            )
            
            gr.Markdown("### 📝 Task")
            task_input = gr.Textbox(
                label="Instructions",
                placeholder="Describe what you want the agent to do...",
                lines=5
            )
            
            submit_btn = gr.Button("🚀 Start Agent", variant="primary", size="lg")
            
        with gr.Column(scale=2):
            gr.Markdown("### 🖥️  Live Output")
            output_log = gr.Code(label="Agent Status & Logs", language="markdown")

    submit_btn.click(
        fn=run_agent_task,
        inputs=[repo_input, task_input, model_input],
        outputs=output_log
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
