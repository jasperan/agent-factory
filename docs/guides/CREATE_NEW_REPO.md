# How to Create a New Repository with Agent Factory

This guide explains how to use the Agent Factory (specifically OpenHands integration) to bootstrap a new software repository using AI.

## Prerequisites

1.  **Environment**: Ensure you are in the `agentfactory` conda environment.
    ```bash
    conda activate agentfactory
    ```
2.  **Dependencies**: Ensure Docker and Ollama (or API keys) are set up.
    - Check Ollama: `ollama list`
    - Check Docker: `docker ps`

## Method 1: Using the CLI (Recommended)

The `agentcli` tool is the primary interface.

1.  **Run the CLI**:
    ```bash
    python agentcli.py
    ```
    *Note: If installed via pip, you might use `agentcli` directly.*

2.  **Select "New Project"** (if available) or simply prompt the agent:
    > "Create a new directory called 'my-new-app' and initialize a basic Python project with poetry."

## Method 2: Using the Free Local LLM Demo (Ollama)

If you successfully ran the verification script, you can adapt it to create new projects without API costs.

1.  **Edit `examples/openhands_ollama_demo.py`**:
    Modify the `task` variable in the `main()` function:
    ```python
    task = """
    Create a new folder 'my_weather_app'.
    Inside it, create a main.py that fetches weather from an API.
    Include a README.md and requirements.txt.
    """
    ```

2.  **Run the script**:
    ```bash
    python examples/openhands_ollama_demo.py
    ```

3.  **Retrieve Output**:
    The agent will perform the work inside the Docker container.
    - The results are usually in `workspace/` or the directory mounted by the worker.
    - Check `agent-factory/openhands_workspace/` for the generated files.

## Troubleshooting

- **405 Method Not Allowed**: This indicates an API mismatch. Ensure you are using the updated `OpenHandsWorker` or the CLI execution verification script.
- **Docker Errors**: Ensure `/var/run/docker.sock` is accessible.
- **Sandbox Failures**: If the runtime exits immediately, it might be due to nesting limitations in your environment. Try running small, non-docker tasks first.
