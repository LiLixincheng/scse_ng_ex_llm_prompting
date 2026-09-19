import json
import os
from pathlib import Path

import ollama

from parse_data import get_unclaimed_items, load_items, save_result


def build_prompt(description, available_items):
    system_prompt = (
        "You are a campus lost-and-found matching assistant. "
        "Use only the items in the JSON data supplied by the user. "
        "An item can be a possible match even when not every detail matches. "
        "Return only valid JSON with exactly this structure: "
        '{"matches": ["ITEM_ID"], "confidence": "LOW"}. '
        "The matches list must contain every possible matching item ID. "
        "Confidence must be exactly LOW, MEDIUM, or HIGH. "
        "If there is no possible match, return an empty matches list."
    )
    items_json = json.dumps(available_items, ensure_ascii=False, indent=2)
    user_prompt = (
        f"Lost item description:\n{description}\n\n"
        f"Available unclaimed items:\n{items_json}"
    )
    return system_prompt, user_prompt


def ask_qwen(system_prompt, user_prompt):
    response = ollama.chat(
        model=os.environ.get("QWEN_MODEL", "qwen2.5:3b"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        format="json",
        options={"temperature": 0},
    )
    if isinstance(response, dict):
        return response["message"]["content"]
    return response.message.content


def parse_response(response_text):
    text = response_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return json.loads(text)


def validate_result(result, available_items):
    if not isinstance(result, dict):
        return False
    if "matches" not in result or "confidence" not in result:
        return False
    if not isinstance(result["matches"], list):
        return False
    if not isinstance(result["confidence"], str):
        return False
    if result["confidence"] not in {"LOW", "MEDIUM", "HIGH"}:
        return False
    valid_ids = {item.get("id") for item in available_items}
    return all(isinstance(item_id, str) and item_id in valid_ids for item_id in result["matches"])


def display_matches(result, available_items):
    print("\nMATCH RESULT")
    print("-" * 50)
    print(f'Confidence: {result["confidence"]}')
    matches = result["matches"]
    if not matches:
        print("\nNo possible matches were found.")
        print("Matches: []")
        return
    items_by_id = {item["id"]: item for item in available_items}
    print("\nPossible matches:")
    for item_id in matches:
        item = items_by_id[item_id]
        print(f"\nID: {item['id']}")
        print(f"Item: {item['item']}")
        print(f"Color: {item['color']}")
        print(f"Location: {item['location']}")
        print(f"Date found: {item['date']}")


def main():
    project_directory = Path(__file__).resolve().parent
    items = load_items(project_directory / "found_items.json")
    available_items = get_unclaimed_items(items)
    print("CAMPUS LOST-AND-FOUND ASSISTANT")
    print("=" * 50)
    description = input("\nDescribe the item you lost: ").strip()
    if not description:
        print("\nPlease provide a description of the lost item.")
        return
    print("\nSearching for possible matches...")
    system_prompt, user_prompt = build_prompt(description, available_items)
    try:
        response_text = ask_qwen(system_prompt, user_prompt)
        result = parse_response(response_text)
    except Exception as error:
        print(f"\nUnable to search for matches: {error}")
        return
    if not validate_result(result, available_items):
        print("\nThe model returned an invalid result.")
        return
    output_path = project_directory / "output" / "match_result.json"
    save_result(result, output_path)
    display_matches(result, available_items)
    print("\nResult saved to output/match_result.json")


if __name__ == "__main__":
    main()
