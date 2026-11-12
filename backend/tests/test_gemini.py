# test_gemini.py
# Phase 4 test. Run from the project root:
#   python backend\tests\test_gemini.py

import os
import sys

TESTS_FOLDER = os.path.dirname(os.path.abspath(__file__))
BACKEND_FOLDER = os.path.dirname(TESTS_FOLDER)
sys.path.insert(0, BACKEND_FOLDER)

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage  # noqa: E402

from agent import gemini_connection  # noqa: E402
from database import schema_reader  # noqa: E402

print("=== Test 1: basic request ===")
try:
    messages = [
        SystemMessage(content="You are a helpful assistant. Answer in one short sentence."),
        HumanMessage(content="Say hello and tell me what a database is."),
    ]
    reply = gemini_connection.ask_gemini(messages)
    print("Gemini replied:", reply)
except gemini_connection.GeminiError as error:
    print("FAILED:", error)
    print("See backend\\logs\\app.log for technical details.")
    sys.exit(1)

print("\n=== Test 2: memory through message history ===")
# We pretend an earlier conversation happened, then ask a follow-up.
# If Gemini answers 'Belagavi', it understood the history.
messages = [
    SystemMessage(content="You are a helpful assistant. Answer very briefly."),
    HumanMessage(content="My favourite city is Belagavi."),
    AIMessage(content="Nice choice! Belagavi is in Karnataka."),
    HumanMessage(content="Which city did I just say was my favourite?"),
]
reply = gemini_connection.ask_gemini(messages)
print("Gemini replied:", reply)

print("\n=== Test 3: Gemini can read our real schema ===")
schema_text = schema_reader.get_schema_text_for_prompt()
messages = [
    SystemMessage(content="You answer questions about a database schema. Be brief."),
    HumanMessage(content="Here is the schema:\n\n" + schema_text
                 + "\n\nWhich tables must I join to connect Customers to Transactions? Answer in one sentence."),
]
reply = gemini_connection.ask_gemini(messages)
print("Gemini replied:", reply)

print("\nAll Gemini tests finished.")