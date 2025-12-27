"""Test each import individually to find the hang"""
import sys

print("Step 1: Importing os...")
sys.stdout.flush()
import os

print("Step 2: Importing json...")
sys.stdout.flush()
import json

print("Step 3: Importing typing...")
sys.stdout.flush()
from typing import Optional, Dict, List, Any

print("Step 4: Importing datetime...")
sys.stdout.flush()
from datetime import datetime

print("Step 5: Importing psycopg2...")
sys.stdout.flush()
import psycopg2

print("Step 6: Importing psycopg2.extras...")
sys.stdout.flush()
import psycopg2.extras

print("Step 7: Importing dotenv...")
sys.stdout.flush()
from dotenv import load_dotenv

print("Step 8: Calling load_dotenv()...")
sys.stdout.flush()
load_dotenv()

print("Step 9: All imports successful!")
