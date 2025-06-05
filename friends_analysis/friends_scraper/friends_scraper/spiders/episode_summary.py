import scrapy
import re
import json
import os
from datetime import datetime

class EpisodeSummary(scrapy.Spider):
    name = "friends_episode_Summaries"
    start_urls = ['https://www.imdb.com/title/tt0108778/episodes']

    def __init__(self, name = None, **kwargs):
        super(EpisodeSummary, self).__init__(name, **kwargs)

        # Create timestamp 
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create data directory 
        self.data_dir = os.path.join(os.getcwd(), 'data', 'episode_summaries')
        os.makedirs(self.data_dir, exist_ok=True)

        # Store all episode summaries
        self.all_summaries = []

        def parse(self, response):
            seasons = response.css('select#bySeason option::attr(value)').getall()

            for season in seasons:
                if season:
                    # Create the dir to store the seasons
                    season_dir_ = os.path.join(self.data_dir, f'season_{season}')
                    os.makedirs(season_dir_, exist_ok=True)

                    url_ = f'https://www.imdb.com/title/tt0108778/episodes?season={season}'
                    yield scrapy.Request(
                        url_,
                        callback=self.parse_season,
                        meta={'season_num': season, 'season_dir':season_dir_}
                    )

    def parse_season(self, response):
        seas_num = response.meta['season_num']
        season_dir_ = response.meta['season_dir_']

        # Extract the episodes list
        episodes_ = response.css('div.list_item')

        for episode in episodes_:
            # Extrac the episode number
            episode_num = episode.css('div.image div.hover-over-image div::text').get()
            episode_num_match = re.search(r'S\d+, Ep(\d+)', episode_num)
            if episode_num_match:
                episode_num_ = episode_num_match.group(1)

                # Extract episode title
                episode_title = episode.css('div.info strong a::text').get().strip()

                # Extract air date
                air_date = episode.css('div.info div.airdate::text').get()
                if air_date:
                    airdate = air_date.strip()

                # Extract the ratings
                episode_rating = episode.css('div.info div.ip-rating-star span.ipl-rating-star__rating::text').get()

                # Extract Summary
                episode_summ = episode.css('div.info div.item_description::text').get()
                if episode_summ:
                    summary = episode_summ.strip()

                # Extract episode URLS for more information
                episode_url = episode.css('div.info strong a::attr(href)').get()
                if episode_url:
                    episode_url = response.urljoin(episode_url)

                episode_data = {
                    'season': int(seas_num),
                    'episode': int(episode_num),
                    'title': episode_title,
                    'airdate':airdate,
                    'rating': episode_rating,
                    'summary': summary,
                    'url':episode_url
                }

                self.all_summaries.append(episode_data)

                # Saving Individual episode summary
                episode_ind_Summ_ = os.path.join(season_dir_, f'Individual_episode_{episode_num_}.json')
                with open(episode_ind_Summ_, 'w', encoding='utf-8') as f:
                    json.dump(episode_data, f, ensure_ascii=False, indent=2)

                # Following the episode url to get more details
                if episode_url:
                    yield scrapy.Request(
                        episode_url,
                        callback= self.parse_episode_details,
                        meta={
                            'episode_data': episode_data,
                            'episode_file': episode_ind_Summ_
                        }
                    )

    def parse_episode_details(self, response):
        episode_data = response.meta['episode_data']
        episode_file = response.meta['episode_file']

        # Extract the full plot
        plot = response.css('div.plot_summary div.summary_text::text').get()
        if plot:
            episode_data['full_plot'] = plot.strip()

        # Extract the keywords
        keywords = response.css('div.see-more.inline.canwrap[itemprop="keywords"] a::text').get()
        if keywords:
            episode_data['keywords'] = [keyword.strip() for keyword in keywords]

        # Updating the episode data in directory
        with open(episode_file, 'w', encoding='utf-8') as f:
            json.dump(episode_data, f, ensure_ascii=False, indent=2)

    def close(self, response):
        all_summaries_ = os.path.join(self.data_dir, f'all_episode_summaries{self.timestamp}.json')
        with open(all_summaries_, 'w', encoding='utf-8') as f:
            json.dump({'episodes': self.all_summaries()}, f, ensure_ascii=False, indent=2)

        self.logger.info(f"Saved all smmaries files to {all_summaries_}")

