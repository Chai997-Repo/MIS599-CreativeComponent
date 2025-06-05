import scrapy
import re
import json
import os
from datetime import datetime

class CharacterSpider(scrapy.Spider):
    name = "friends_characters"
    start_urls = ['https://www.imdb.com/title/tt0108778/fullcredits']

    def __init__(self, name = None, **kwargs):
        super(CharacterSpider, self).__init__(name, **kwargs)

        # Create the time stamp for versioning the data 
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Creating the data directory if doesn't exist in the project structure
        self.data_dir = os.path.join(os.getcwd(), 'data', 'character_directory')
        os.makedirs(self.data_dir, exist_ok=True)


        # Creating individual directory for characters
        self.individual_dir = os.path.join(self.data_dir, "individual_directory")
        os.makedirs(self.individual_dir, exist_ok=True)

        def parse_cast(self, response):
            # Extract the Main Cast information

            table_cast = response.css('table.cast_list')
            rows_cast = response.css('tr.odd, tr.even')

            characters_ = []

            for row in rows_cast:
                name_ = row.css('td:nth-child(2) a::text').get()
                if name_:
                    actor_name = name_.strip()

                    # Extract the character name
                    characters_group = row.css('td.character')
                    character_name = characters_group.css('a::text').get()

                    if not character_name:
                        character_name = characters_group.css('a::text').get()

                    if character_name:
                        character_name = re.sub(r'\s+', ' ', character_name).strip()
                        character_name = re.sub(r'\s*/\s*.*', '', character_name)

                        # Now Extracting the actor URL for more information
                        url = row.css('td:nth-child(2) a::attr(href)').get()
                        if url:
                            actor_url = response.urljoin(url)

                        characters_.append({
                            'actor_name': actor_name,
                            'character_name':character_name,
                            'actor_url':actor_url

                        })

                        if actor_url:
                            yield scrapy.Request(
                                actor_url,
                                callback=self.parse_actor,
                                meta={'character_data':characters_[-1]}
                            )

            file = os.path.join(self.data_dir, f'basic_characters_{self.timestamp}.json')
            with open(file, 'w', encoding='utf-8') as f:
                json.dump({'character': characters_}, f, ensure_ascii=False, indent=2)

        def parse_actor(self, response):
            char_data = response.meta['character_data']

            # Extract the actor bio
            actor_bio = response.css('div.name-overview-bio::text').get()
            if actor_bio:
                char_data['actor_bio'] = actor_bio.strip()

            # Extrac the image URL
            image_url = response.css('img.name-poster::attr(src)').get()
            if image_url:
                char_data['image_url'] = image_url

            # Saving the individual character data 
            actor_data = char_data['actor_name'].lower().replace(' ', '_')
            character_file_ = os.path.join(self.individual_dir, f'{actor_data}.json')
            with open(character_file_, 'w', encoding='utf-8') as f:
                json.dump(char_data, f, ensure_ascii=False, indent=2)
                