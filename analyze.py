import anthropic
from dotenv import load_dotenv
import sys

load_dotenv()
client = anthropic.Anthropic()

def load_file(file_path):
    with open(file_path, 'r') as file:
        return file.read().strip()

def send_message(system_prompt, message_history):
    message = client.messages.create(
        model="claude-3-opus-20240229",
        #model="claude-3-sonnet-20240229",
        #model="claude-3-haiku-20240307",
        max_tokens=4000,
        temperature=0,
        system=system_prompt,
        messages=message_history
    )
    return message.content[0].text

def analyze_farb(letter_file, invoice_file):

    system_prompt = load_file("whitepaper.md")
    letter_text = load_file(letter_file)
    invoice_text = load_file(invoice_file)

    message_history = []
    message_history.append({
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": f"Use this engagement letter for your FARB analysis:\n<letter>\n{letter_text}\n</letter>\n\nThis is the invoice you are analyzing line items from:\n<invoice>\n{invoice_text}\n</invoice>"
            }
        ]
    })
    message_history.append({
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": "Thank you, I will be your expert legal professional and am now prepared to thoroughly analyze individual line items from the invoice using the cover letter as context and apply the FARB principles, giving you accurate and insightful comments on each item."
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
                    "text": f"Focus on the {position} 5 line items from the invoice and analyze each one against the FARB principles. If you have completed ALL of the line items and there are no more line items left in the invoice, only then respond with <invoice_completed>."
                }
            ]
        })
        result = send_message(system_prompt, message_history)
        print(result)
        items.append(result)

        if "<invoice_completed>" in result:
            break

        message_history.append({
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": result
                }
            ]
        })
        position = "next"

    return items

def summarize_farb(letter_file, items):

    system_prompt = load_file("whitepaper.md")
    letter_text = load_file(letter_file)

    message_history = []
    message_history.append({
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": f"Use this engagement letter for your FARB analysis:\n<letter>\n{letter_text}\n</letter>\n\nHere are the line items you analyzed:\n<items>\n{items}\n</items>\n\nNow please consider all of the items and write a professional and well formatted summary of your findings from those items.  Make sure to include which items are most in need of further attention based on the FARB principles. Don't include any other thoughts or comments outside of the scope of applying FARB to the items you analyzed."
            }
        ]
    })

    result = send_message(system_prompt, message_history)
    print(result)
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py letter.txt invoice.txt")
        sys.exit(1)
    analyze_farb(sys.argv[1], sys.argv[2])