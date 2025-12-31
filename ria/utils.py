from typing import List

# Helper function to recursively extract 'content' from all AIMessage instances
def extract_ai_message_content(stream) -> List[str]:
    # Extract AIMessage contents into an array as {key: value}
    ai_message_contents = []

    for key, value in stream.items():
            # We expect a 'messages' key
            if value is None:
                continue
            messages = value['messages']
            if isinstance(messages, list):  # Skip ToolMessages or others
                continue
            ai_message_contents.append((key, messages.content)) # Assuming messages is an AIMessage
            # print("ai_message_contents...\n")
            # print(ai_message_contents)
            # if isinstance(messages, dict):  # AIMessage will typically be a dict
            #     ai_message_contents.append((key, messages.content))
            #     # if 'content' in messages:
            #     #     ai_message_contents.append({key: messages['content']})
            # elif isinstance(messages, list):  # Skip ToolMessages or others
            #     continue
        
    return ai_message_contents

def parse_messages(result: dict):
    data = {
        "human": [],
        "ai": [],
        "tools": [],
    }

    for msg in result.get("messages", []):
        if hasattr(msg, "name"):  # ToolMessage (e.g., name='write_file')
            data["tools"].append({
                "tool_name": getattr(msg, "name", None),
                "tool_call_id": getattr(msg, "tool_call_id", None),
                "content": getattr(msg, "content", None)
            })
        elif hasattr(msg, "tool_calls") and msg.tool_calls:
            # AIMessage with tool calls (the reasoning + tool actions)
            calls = []
            for call in msg.tool_calls:
                calls.append({
                    "name": call["name"],
                    "args": call["args"]
                })
            data["ai"].append({
                "content": getattr(msg, "content", None),
                "tool_calls": calls
            })
        else:
            # HumanMessage or simple AIMessage
            msg_type = type(msg).__name__
            entry = {"type": msg_type, "content": getattr(msg, "content", None)}
            if msg_type.lower().startswith("human"):
                data["human"].append(entry)
            else:
                data["ai"].append(entry)
    return data
