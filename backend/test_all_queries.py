import sys
from services.chat_service import process_chat

queries = [
    "Surprise me! Pick a random active ARGO float and tell me its story in one sentence.",
    "Show depth profile and QC flags for float 2905105",
    "Calculate thermocline depth and MLD for float 2905105",
    "Compare floats 2905105 and 2902183 across depth bins",
]

for q in queries:
    res = process_chat(q, mode="researcher")
    sys.stdout.buffer.write(f"\n========================================\nQUESTION: {q}\n".encode("utf-8"))
    sys.stdout.buffer.write(f"SQL: {res.get('explainability', {}).get('sql')}\n".encode("utf-8"))
    sys.stdout.buffer.write(f"ANSWER: {res['answer']}\n".encode("utf-8"))
    sys.stdout.buffer.write(f"VIZ_TYPE: {res.get('viz', {}).get('viz_type')}\n".encode("utf-8"))
    sys.stdout.buffer.write(f"ROWS: {res.get('row_count')}\n".encode("utf-8"))
