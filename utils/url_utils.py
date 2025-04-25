import re
import string
import random
from datetime import datetime, timedelta, timezone
from emojies import EMOJIES
from urllib.parse import unquote
import emoji
import validators
import geoip2.errors
import geoip2.database
from flask import request

# Load the bot user agents from a file
with open("bot_user_agents.txt", "r") as file:
    BOT_USER_AGENTS = file.read()
    BOT_USER_AGENTS = [
        i.strip() for i in BOT_USER_AGENTS.split("\n") if i.strip() != ""
    ]


def get_country(ip_address):
    """Parses the client's IP address and returns the country name."""
    reader = geoip2.database.Reader("misc/GeoLite2-Country.mmdb")
    try:
        response = reader.country(ip_address)
        country = response.country.name
        return country
    except geoip2.errors.AddressNotFoundError:
        return "Unknown"
    finally:
        reader.close()


def get_client_ip() -> str:
    """Gets the client IP address from the request headers."""
    # Check for common proxy headers first
    headers_to_check: list[str] = [
        "CF-Connecting-IP",  # Cloudflare
        "True-Client-IP",  # Akamai & others
        "X-Forwarded-For",  # Standard proxy header (can contain multiple IPs)
        "X-Real-IP",  # Nginx or other proxies
        "X-Client-IP",  # Less common
    ]

    for header in headers_to_check:
        ip_value: str | None = request.headers.get(header)
        if ip_value:
            client_ip: str = ip_value.split(",")[0].strip()
            if client_ip:
                return client_ip

    # Fall back to remote address if no proxy headers found
    return request.remote_addr or ""


def validate_password(password) -> bool:
    # Check if the password is at least 8 characters long
    if len(password) < 8:
        return False

    # Check if the password contains a letter, a number, and the allowed special characters
    if not re.search(r"[a-zA-Z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[@.]", password):
        return False

    # Check if there are consecutive special characters
    if re.search(r"[@.]{2}", password):
        return False

    return True


def validate_url(url):
    return validators.url(
        url, skip_ipv4_addr=True, skip_ipv6_addr=True
    ) and not re.match(r"^https?://(?:www\.)?spoo\.me.*$", url, re.IGNORECASE)


# custom expiration time is currently really buggy and not ready for production
def validate_expiration_time(expiration_time):
    try:
        expiration_time = datetime.fromisoformat(expiration_time)
        # Check if it's timezone aware
        if expiration_time.tzinfo is None:
            print("timezone not aware")
            return False
        else:
            print("timezone aware")
            print("Expiration Time in GMT: ", expiration_time.astimezone(timezone.utc))
            print(expiration_time.tzinfo)
            # Convert to GMT if it's timezone aware
            expiration_time = expiration_time.astimezone(timezone.utc)
        if expiration_time < datetime.now(timezone.utc) + timedelta(minutes=3):
            print(expiration_time, datetime.now(timezone.utc) + timedelta(minutes=3))
            print("EXPIRATION TIME IN GMT: ", expiration_time)
            print("CURRENT TIME IN GMT: ", datetime.now(timezone.utc))
            print(
                "CURRENT TIME IN GMT + 5: ",
                datetime.now(timezone.utc) + timedelta(minutes=4.5),
            )
            print("less than 5 minutes")
            return False
        return True
    except Exception as e:
        print(e)
        return False


def convert_to_gmt(expiration_time):
    expiration_time = datetime.fromisoformat(expiration_time)
    # Check if it's timezone aware
    if expiration_time.tzinfo is None:
        return None
    else:
        # Convert to GMT if it's timezone aware
        expiration_time = expiration_time.astimezone(timezone.utc)
    return expiration_time


def generate_short_code() -> str:
    """Generates a random 6 character alphanumeric string."""
    letters = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return "".join(random.choice(letters) for i in range(6))


def validate_alias(string) -> bool:
    pattern = r"^[a-zA-Z0-9_-]*$"
    return bool(re.search(pattern, string))


def generate_emoji_alias() -> str:
    """Generates a random 3 character emoji string."""
    return "".join(random.choice(EMOJIES) for _ in range(3))


def validate_emoji_alias(alias) -> bool:
    unqoted_alias: str = unquote(alias)
    emoji_list = emoji.emoji_list(unqoted_alias)
    extracted_emojis: str = "".join([data["emoji"] for data in emoji_list])

    return len(extracted_emojis) == len(unqoted_alias) and len(emoji_list) <= 15


def generate_unique_code(generate_func, exists_check_func):
    """Generates a unique unique code by checking against the provided function."""
    short_code = generate_func()
    while exists_check_func(short_code):
        short_code = generate_func()
    return short_code


def build_url_data(
    url,
    password: str | None = None,
    max_clicks: int | None = None,
    block_bots: bool | None = None,
):
    """Generates the standard Short URL schema"""
    data = {
        "url": url,
        "counter": {},
        "total-clicks": 0,
        "ips": [],
        "creation-date": datetime.now().strftime("%Y-%m-%d"),
        "creation-time": datetime.now().strftime("%H:%M:%S"),
        "creation-ip-address": get_client_ip(),
    }

    if password:
        data["password"] = password
    if max_clicks:
        data["max-clicks"] = str(abs(int(str(max_clicks))))
    if block_bots:
        data["block-bots"] = True

    return data
