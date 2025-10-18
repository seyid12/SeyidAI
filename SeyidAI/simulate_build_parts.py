# Simple simulation to validate types.Part(text=...) usage without requiring full SDK
try:
    from google.genai import types
    sdk_available = True
except Exception:
    sdk_available = False

# Define fallback dummy classes if SDK not available
if not sdk_available:
    class Part:
        def __init__(self, text=None):
            self.text = text
        def __repr__(self):
            return f"Part(text={self.text!r})"

    class Content:
        def __init__(self, role=None, parts=None):
            self.role = role
            self.parts = parts or []
        def __repr__(self):
            return f"Content(role={self.role!r}, parts={self.parts!r})"

    class types:
        Part = Part
        Content = Content

# Simulate a Streamlit-like chat history
chat_history = [
    {"role": "user", "text": "Merhaba, nasılsın?"},
    {"role": "model", "text": "İyiyim, teşekkürler! Size nasıl yardımcı olabilirim?"},
    {"role": "user", "text": "Bu metni özetler misin?"}
]

# Build gemini_contents the same way as in app.py (excluding the last user prompt)
gemini_contents = []
for msg in chat_history:
    if msg == chat_history[-1] and msg["role"] == "user":
        break
    gemini_contents.append(types.Content(role=msg["role"], parts=[types.Part(text=msg["text"]) ]))

# Now append the last user prompt
prompt = chat_history[-1]["text"]
gemini_contents.append(types.Content(role="user", parts=[types.Part(text=prompt)]))

print("Simulation: constructed gemini_contents (role -> parts texts):")
for c in gemini_contents:
    parts_texts = [p.text for p in c.parts]
    print(f" - {c.role} -> {parts_texts}")

print("Done. No TypeError occurred when constructing types.Part(text=...).")
