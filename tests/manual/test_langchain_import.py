"""Test langchain imports"""
import sys

print("Step 1: Importing langchain_anthropic...")
sys.stdout.flush()

from langchain_anthropic import ChatAnthropic

print("Step 2: ChatAnthropic imported successfully!")
sys.stdout.flush()

print("Step 3: Importing langchain_core.messages...")
sys.stdout.flush()

from langchain_core.messages import HumanMessage, SystemMessage

print("Step 4: All langchain imports successful!")
sys.stdout.flush()
