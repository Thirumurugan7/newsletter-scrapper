from telethon import TelegramClient, events
from telethon.tl.functions.messages import GetHistoryRequest
import json
import os
from datetime import datetime
import asyncio

# Your Telegram API credentials
# Get these from https://my.telegram.org/auth
API_ID = 'your_api_id'
API_HASH = 'your_api_hash'
PHONE = 'your_phone_number'  # Your phone number with country code
GROUP_USERNAME = 'joescrypt'  # The group username without @ symbol

class TelegramScraper:
    def __init__(self):
        self.client = TelegramClient('scraper_session', API_ID, API_HASH)
        
    async def connect(self):
        await self.client.start()
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(PHONE)
            await self.client.sign_in(PHONE, input('Enter the code: '))
    
    async def scrape_messages(self, limit=None):
        messages = []
        
        try:
            channel = await self.client.get_entity(GROUP_USERNAME)
            
            # Get messages
            async for message in self.client.iter_messages(channel, limit=limit):
                msg_data = {
                    'id': message.id,
                    'date': message.date.isoformat(),
                    'text': message.text,
                    'views': message.views,
                    'forwards': message.forwards,
                    'reply_to_msg_id': message.reply_to_msg_id,
                }
                
                # Handle media
                if message.media:
                    if hasattr(message.media, 'photo'):
                        msg_data['media_type'] = 'photo'
                        # Download photos to a directory
                        path = f'downloads/photos/{message.id}.jpg'
                        os.makedirs(os.path.dirname(path), exist_ok=True)
                        await message.download_media(path)
                        msg_data['media_path'] = path
                    elif hasattr(message.media, 'document'):
                        msg_data['media_type'] = 'document'
                        # Download documents to a directory
                        path = f'downloads/documents/{message.id}_{message.file.name}'
                        os.makedirs(os.path.dirname(path), exist_ok=True)
                        await message.download_media(path)
                        msg_data['media_path'] = path
                
                messages.append(msg_data)
                print(f"Scraped message {message.id}")
                
                # Save progress periodically
                if len(messages) % 100 == 0:
                    self.save_messages(messages)
            
            return messages
            
        except Exception as e:
            print(f"Error scraping messages: {str(e)}")
            return messages
    
    def save_messages(self, messages):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'joescrypt_messages_{timestamp}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(messages)} messages to {filename}")

async def main():
    scraper = TelegramScraper()
    await scraper.connect()
    
    # Scrape all messages (or set a limit)
    messages = await scraper.scrape_messages(limit=None)
    scraper.save_messages(messages)
    
    await scraper.client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
