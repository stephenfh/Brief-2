"""Quick CLI check: python chatbot/try_agent.py <role> "<question>" """
import sys
import server
role, q = sys.argv[1], sys.argv[2]
reply, trace, _cv = server.agent.run(server.client, server.MODEL, role, [{"role": "user", "content": q}])
for t in trace:
    print("  tool:", t["tool"], t["args"], "->", t["result"][:110])
print("\n" + reply)
