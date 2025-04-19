import re

from apify_client import ApifyClient

# Initialize Apify client with your API token
client = ApifyClient("apify_api_365MlxHyMWaX9JRG22msK3gHtN6hYs3hhGvW")

def get_meta_ads(niche: str):
    ads_run = client.actor("apify/facebook-ads-scraper").call(run_input={
        "startUrls": [{
            "url": f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=DZ&is_targeted_country=false&media_type=video&q={niche}&search_type=keyword_unordered"
        }],
        "resultsLimit": 10,
    })

    return list(client.dataset(ads_run["defaultDatasetId"]).iterate_items())