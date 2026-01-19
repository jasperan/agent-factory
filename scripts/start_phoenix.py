#!/usr/bin/env python3
"""Start Phoenix server on port 6006."""
import phoenix as px

if __name__ == "__main__":
    # Launch Phoenix UI on port 6006
    print("Starting Phoenix UI on http://localhost:6006")
    px.launch_app(port=6006)
    print("Phoenix UI started successfully!")
    print("Keep this terminal open to maintain Phoenix connection.")

    # Keep the server running
    input("Press Enter to stop Phoenix server...")
