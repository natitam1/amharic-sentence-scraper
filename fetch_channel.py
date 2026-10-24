import sys
import os
import requests
from bs4 import BeautifulSoup

sys.path.append(os.path.join(os.path.dirname(__file__), 'data'))
import clean_sentences

def get_telegram_messages(channel_name, pages=50):
    messages = []
    url = f"https://t.me/s/{channel_name}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    for i in range(pages):
        print(f"Fetching {url}")
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch. Status code: {response.status_code}")
            break
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        text_nodes = soup.select(".tgme_widget_message_text")
        for node in text_nodes:
            messages.append(node.get_text("\n"))
            
        more_link = soup.select_one(".tme_messages_more")
        if more_link and more_link.has_attr("href"):
            url = "https://t.me" + more_link["href"]
        else:
            break
            
    return messages

def scrape_channel(channel):
    print(f"\n--- Scraping messages from {channel} ---")
    messages = get_telegram_messages(channel, pages=100)
    print(f"Extracted {len(messages)} messages.")
    
    all_text = "\n\n".join(messages)
    
    sentences = clean_sentences.split_into_sentences(all_text)
    
    valid_sentences = []
    for s in sentences:
        s_clean = s.rstrip(' ።').strip()
        words = s_clean.split()
        if 15 <= len(words) <= 28:
            valid_sentences.append(s)
            
    valid_sentences = list(dict.fromkeys(valid_sentences))
    
    if len(valid_sentences) > 0:
        output_file = f"data/{channel}_all_single_sentences_15_to_28_words.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            for s in valid_sentences:
                f.write(s + "\n")
        print(f"Saved {len(valid_sentences)} sentences to {output_file}")
    else:
        print(f"No valid sentences found for {channel}")

def main():
    if len(sys.argv) > 1:
        channels = sys.argv[1:]
    else:
        channels = ["inspireethiopia"]
        
    for channel in channels:
        scrape_channel(channel)

if __name__ == "__main__":
    main()
