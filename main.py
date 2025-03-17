import os
from asyncio import events

from icrawler import ImageDownloader
from icrawler.builtin import GoogleImageCrawler

historical_periods = [
    "Pro-Trump supporters storm the Capitol building."
]


def download_images_to_folders(eventss):
    event_id = 171
    for event_name in historical_periods:
        # Create a folder for each event using the event ID
        event_dir = f"cardImages/"


        crawler = GoogleImageCrawler(storage={'root_dir': event_dir})

        # Crawl and download images for the given event name
        crawler.crawl(keyword=event_name, max_num=1)  # Download only 1 image
        try:
            os.rename("cardImages/000001.png", f"cardImages/{event_id}.png")
        except:
            try:
                os.rename("cardImages/000001.jpg", f"cardImages/{event_id}.jpg")
            except:
                os.rename("cardImages/000001.jpeg", f"cardImages/{event_id}.jpeg")
        event_id += 1


download_images_to_folders(events)
