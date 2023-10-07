import requests
from bs4 import BeautifulSoup
import re
import os

# Constants
URL = "https://eitaa.com/valiasrstudents"
LAST_MESSAGE_ID_FILE = "last_message_id.txt"
TELEGRAM_TOKEN = os.environ.get("TOKEN")
TELEGRAM_CHANNEL = os.environ.get("CHANNEL")



def get_last_message_id():
    try:
        with open(LAST_MESSAGE_ID_FILE, "r") as f:
            return int(f.read().strip())
    except FileNotFoundError:
        return None


def save_last_message_id(message_id):
    with open(LAST_MESSAGE_ID_FILE, "w") as f:
        f.write(str(message_id))

def send_to_telegram(message, image_url=None):
    # If image_url is provided, send the image with the caption
    if image_url:
        img_response = requests.get(image_url, stream=True)
        img_response.raise_for_status()

        with open("temp_img.jpg", 'wb') as f:
            for chunk in img_response.iter_content(8192):
                f.write(chunk)

        url_photo = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        with open("temp_img.jpg", "rb") as img_file:
            response_photo = requests.post(url_photo, data={"chat_id": TELEGRAM_CHANNEL, "caption": message, "parse_mode": "HTML"}, files={"photo": img_file})

        os.remove("temp_img.jpg")
        return response_photo.status_code == 200  # Return True if the photo was sent successfully

    # If no image is provided, just send the message
    else:
        url_message = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHANNEL,
            "text": message,
            "parse_mode": "HTML"
        }
        response_message = requests.post(url_message, data=payload)
        return response_message.status_code == 200  # Return True if the message was sent successfully



def main():
    response = requests.get(URL)
    soup = BeautifulSoup(response.content, "html.parser")
    messages = soup.find_all("div", class_="etme_widget_message_wrap")
    
    last_message_id = get_last_message_id()
    
    for message in messages:  # Process older messages first
        message_id = int(message["id"])
        save_last_message_id(message_id)
        
        if last_message_id is None or message_id > last_message_id:
            message_text = message.find("div", class_="etme_widget_message_text").text
            message_image = message.find("a", class_="etme_widget_message_photo_wrap")
            # use regex to find the image url
            if message_image:
                url_match = re.search(r"url\('([^']+)'\)", message_image.get("style"))
                message_image = "https://eitaa.com" + url_match.group(1)
            else:
                message_image = None

            
            if send_to_telegram(message_text, message_image):
                print(f"Sent message {message_id} Telegram.")
            else:
                print(f"Failed to send message {message_id} to Telegram.")
        else:
            print(f"Message {message_id} is not new. Skipping...")

if __name__ == "__main__":
    main()