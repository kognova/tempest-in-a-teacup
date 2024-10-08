import anthropic
import os
from dotenv import load_dotenv
import sys
import json
import streamlit as st

def load_file(file_path):
    with open(file_path, 'r') as file:
        return file.read().strip()

def send_message(client, system_prompt, message_history):
    message = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        #model="claude-3-sonnet-20240229",
        #model="claude-3-haiku-20240307",
        max_tokens=4000,
        temperature=0,
        system=system_prompt,
        messages=message_history
    )
    return message

def main():
    if len(sys.argv) < 2:
        print("Please provide the path to the file as a command line argument.")
        sys.exit(1)

    invoice_file = load_file(sys.argv[1])
    system_prompt = load_file("extract.txt")

    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if api_key is None:
        print("ANTHROPIC_API_KEY not found in .env file.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=st.secrets['api_keys']['anthropic'])

    message_history = []
    message_history.append({
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": f"You are extracting line items from this invoice:\n<INVOICE>\n{invoice_file}\n</INVOICE>"
            }
        ]
    })
    message_history.append({
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": "Thank you, how many line items would you like to extract?"
            }
        ]
    })

    position = "first"
    items = []
    for i in range(10):
        message_history.append({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Please extract the {position} 5 line items from the INVOICE. If there are no more then please respond with <END>."
                }
            ]
        })
        message = send_message(client, system_prompt, message_history)
        print(message.content[0].text)

        # in the text if there's an <ITEMS>[json]</ITEMS> then extract the json and append the items to the items array
        if "<ITEMS>" in message.content[0].text:
            json_text = message.content[0].text.split("<ITEMS>")[1].split("</ITEMS>")[0]
            items.extend(json.loads(json_text))

        # if message content contains "<END>" then break
        if "<END>" in message.content[0].text:
            break

        message_history.append({
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": message.content[0].text
                }
            ]
        })
        position = "next"
    
    print(json.dumps(items, indent=2))

if __name__ == "__main__":
    main()