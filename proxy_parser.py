import re
from datetime import datetime, timezone, timedelta
import requests

def get_spys_proxies(url="https://spys.me/proxy.txt"):
    """Retrieves and parses proxy addresses and update time from spys.me.

    Args:
        url: The URL of the spys.me proxy list (defaults to the standard URL).

    Returns:
        A tuple containing:
        - A list of proxy addresses (strings).
        - A datetime object representing the last update time.
        - Returns (None, None) if retrieval or parsing fails.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        text = response.text
        # with open("spys_proxy_20241123.txt") as f:
        #     text = f.read()
        proxies = []
        proxy_regex = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5})"
        for match in re.finditer(proxy_regex, text):
            proxies.append(match.group(1))

        update_regex = r"updated at (.*)"
        match = re.search(update_regex, text)
        if not match:
            update_regex = r"Proxy list .* updated at (.*)"
            match = re.search(update_regex, text)
            if not match:
                return None, None

        update_string = match.group(1)

        try:
            updated_at = datetime.strptime(update_string, "%a, %d %b %y %H:%M:%S %z")
        except ValueError:
            updated_at = datetime.strptime(update_string, "%a, %d %b %y %H:%M:%S")
            offset_match = re.search(r"([+-]\d{2}):?(\d{2})", text) 
            if offset_match:
                offset_hours = int(offset_match.group(1))
                offset_minutes = int(offset_match.group(2))
                updated_at = updated_at.replace(tzinfo=timezone(timedelta(hours=offset_hours, minutes=offset_minutes)))
            else:
                updated_at = updated_at.replace(tzinfo=timezone.utc) 

        return proxies, updated_at

    except requests.exceptions.RequestException as e:
        print(f"Error fetching proxy data: {e}")
        return None, None
    except Exception as e:
        print(f"Error parsing proxy data: {e}")
        return None, None