import re
import json
import os
import scrapy
from datetime import datetime 

class TranscriptSpider(scrapy.Spider):
    name = "friends_transcripts"
    start_urls = ['https://subslikescript.com/series/Friends-108778']

    def __init_(self, *args, **kwargs):
        super(TranscriptSpider, self).__init__(*args, **kwargs)
        # Creating an Time stamp
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Creating the path/directory to store the data, if it doesn;t exist (current directory + 'data/transcripts')
        self.data_dir = os.path.join(os.getcwd(), 'data', 'transcripts')  
        os.makedirs(self.data_dir, exist_ok=True)

    # Method to extract all the season links
    def extract_seasons(self, response):
        # Extracting the links from website
        season_links = response.CSS('article.season a::attr(href)').getall()

        for season in season_links:
            url = response.urljoin(season) #converts relative urls to absolute urls
            yield scrapy.Request(url, callback = self.extract_season_number) # It schedules an new request eavery time when we call this 

    # This Method extract all the season number from the above season links 
    def extract_season_number(self, response):
        title = response.CSS('h1::text').get()
        season_num = re.search(r'Season (\d+)', title).group(1) # uses regex to find the season number in the title

        # Creating an directory for each season number
        season_dir = os.path.join(self.data_dir, f'season_{season_num}')
        os.makedirs(season_dir, exist_ok=True)

        # Extract links to each episodes
        episode_links = response.css('article.episode a::attr(href)').getall() #Finds all episode links in the season page

        for link in episode_links:
            episode_url = response.urljoin(link)
            yield scrapy.Request(
                episode_url,
                callback = self.extract_episodes,
                meta = {'season_number': season_num, 'season_directory':season_dir}  # it passes additional data to the callback function
            )

    #Function to extract only the episodes using episode links or Processes each episode page
    def extract_episodes(self, response):
        # Extract season info from season_num and season_dir
        season_num = response.meta['season_number']
        season_dir = response.meta['season_directory']

        # Extract the episode title and number
        title_txt = response.css('h1::text').get()
        match_episode_title = re.search(r'Epiosde (\d+) - (.*)', title_txt)

        if not match_episode_title:
            return 
        
        episode_number = match_episode_title.group(1)
        episode_title = match_episode_title.group(2).strip()

        # Extracting full transcript
        transcript_div = response.css('div.full-script')
        transcript_text = transcript_div.css('::text').getall() # Extract all the text notes with in the transcript_div
        transcript_text = ''.join(transcript_text).strip()

        lines = transcript_text.split('\n')
        dialogues = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

        # Checking if line start with an character name or not (all caps followed by column)
        char_match = re.match(r'([A-Z][A-Z\s]+):\s(.*)', line)
        if char_match:
            character = char_match.group(1).strip()
            dialogue = char_match.group(2).strip()
            dialogues.append({
                'character' : character,
                'dialogue': dialogue
            })
        else:

            # Else we append the previous dialogue  it is a continuation
            if dialogues:
                dialogues[-1]['dialogue'] += ' ' + line

        # Now creating the episode data structure
        episode_data = {
            'season': int(season_num),
            'episode': int(episode_number),
            'title': episode_title,
            'url' : response.url,
            'dialogues': dialogues,
            'full_transcript': transcript_text
        }

        # Add to local storage in the directory
        self.all_episodes.append(episode_data)

        # Saving the indivisual episode file to JSON structure
        episode_file = os.path.json(season_dir, f'episode_{episode_number}.json')
        with open(episode_file, 'w', encoding = 'utf-8') as f:
            json.dump(episode_data, f, ensure_ascii=False, indent= 2) #ensure_ascii=False(prevents non-ASCII characters), indent= 2(prints the json with indentation)

        # Save the file with Log Progress
        self.logger.info(f"Scraped S{season_num}E{episode_number}: {episode_title}")

    # Function to close when spider finishes crawling
    def closed_spider(self, reason):
        all_episodes_file = os.path.join(self.data_dir, f'all_episodes_{self.timestamp}.json')
        with open(all_episodes_file, 'w', encoding='utf-8') as f:
            json.dump({'episodes': self.all_episodes}, f, ensure_ascii=False, indent=2)

        self.logger.info(f"Saved all Episodes to {all_episodes_file}")






        

