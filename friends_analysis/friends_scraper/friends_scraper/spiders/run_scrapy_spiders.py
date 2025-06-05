import os
import subprocess
import time
from datetime import datetime


def run_scrappers():
    start_time = datetime.now()
    print(f"Starting the data collection{start_time}")

    # Creating a log directory
    log_dir = os.path.join(os.getcwd(), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # Define all the spiders to run
    spiders = [
        'friends_transcripts',
        'friends_characters',
        'friends_episode_Summaries'
    ]

    # Run each spider and capture its output
    for spider in spiders:
        print(f"\n{'='*50}")
        print(f"Running {spider} spider...")
        print(f"{'='*50}\n")

        log_file = os.path.join(log_dir, f"{spider}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

        # Running the spider
        with open(log_file, 'w') as f:
            process = subprocess.Popen(
            ['scrapy', 'crawl', spider],
            stdout= subprocess.PIPE,
            stderr= subprocess.STDOUT,
            universal_newlines= True
        )

            for line in process.stdout:
                print(line, end='')
                f.write(line)

            # Wait for the process to complete
            process.wait()

        print(f"\nFinished {spider} spider. Log save to {log_file}")

    end_time = datetime.now()
    duration = end_time - start_time
    print(f"\nSPiders Completed at {end_time} ")
    print(f"\nTotal Duration {duration}")


if __name__ == "__main__":
    run_scrappers()


