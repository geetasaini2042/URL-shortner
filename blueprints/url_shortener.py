from flask import (
    Blueprint,
    request,
    jsonify,
    render_template,
    redirect,
    url_for,
)
from utils.url_utils import (
    get_client_ip,
    validate_password,
    validate_url,
    validate_alias,
    validate_emoji_alias,
    generate_short_code,
    generate_emoji_alias,
)
from utils.mongo_utils import (
    load_url,
    insert_url,
    load_emoji_url,
    insert_emoji_url,
    check_if_slug_exists,
    check_if_emoji_alias_exists,
    validate_blocked_url,
    urls_collection,
    get_url_v2_by_alias,
)
from utils.general import is_positive_integer, humanize_number
from .limiter import limiter
from cache import dual_cache

from datetime import datetime
from urllib.parse import unquote
import tldextract
from crawlerdetect import CrawlerDetect

url_shortener = Blueprint("url_shortener", __name__)

crawler_detect = CrawlerDetect()
tld_no_cache_extract = tldextract.TLDExtract(cache_dir=None)


@url_shortener.route("/", methods=["GET"])
@limiter.exempt
def index():
    return render_template("index.html", host_url=request.host_url)


@url_shortener.route("/", methods=["POST"])
def shorten_url():
    url = request.values.get("url")
    password = request.values.get("password")
    max_clicks = request.values.get("max-clicks")
    alias = request.values.get("alias")
    block_bots = request.values.get("block-bots")

    if not url:
        if request.headers.get("Accept") == "application/json":
            return jsonify({"UrlError": "URL is required"}), 400
        else:
            return (
                render_template(
                    "index.html",
                    error="URL is required",
                    host_url=request.host_url,
                ),
                400,
            )

    if url and not validate_url(url):
        return (
            jsonify(
                {
                    "UrlError": "Invalid URL, URL must have a valid protocol and must follow rfc_1034 & rfc_2728 patterns"
                }
            ),
            400,
        )

    if url and not validate_blocked_url(url):
        return jsonify({"BlockedUrlError": "Blocked URL ⛔"}), 403

    if alias and not validate_alias(alias):
        if request.headers.get("Accept") == "application/json":
            return jsonify({"AliasError": "Invalid Alias", "alias": f"{alias}"}), 400
        else:
            return (
                render_template(
                    "index.html",
                    error="Invalid Alias",
                    url=url,
                    host_url=request.host_url,
                ),
                400,
            )

    elif alias:
        short_code = alias[:16]

    if alias and check_if_slug_exists(alias[:16]):
        if request.headers.get("Accept") == "application/json":
            return (
                jsonify(
                    {"AliasError": "Alias already exists", "alias": f"{alias[:16]}"}
                ),
                400,
            )
        else:
            return (
                render_template(
                    "index.html",
                    error=f"Alias {alias[:16]} already exists",
                    url=url,
                    host_url=request.host_url,
                ),
                400,
            )
    elif alias:
        short_code = alias[:16]
    else:
        while True:
            short_code = generate_short_code()

            if not check_if_slug_exists(short_code):
                break

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
        if not validate_password(password):
            return (
                jsonify(
                    {
                        "PasswordError": "Invalid password, password must be atleast 8 characters long, must contain a letter and a number and a special character either '@' or '.' and cannot be consecutive"
                    }
                ),
                400,
            )
        data["password"] = password

    if max_clicks:
        if not is_positive_integer(max_clicks):
            return (
                jsonify({"MaxClicksError": "max-clicks must be an positive integer"}),
                400,
            )
        else:
            max_clicks = str(abs(int(str(max_clicks))))
        data["max-clicks"] = max_clicks

    if block_bots:
        data["block-bots"] = True

    insert_url(short_code, data)

    response_data = {
        "short_url": f"{request.host_url}{short_code}",
        "domain": request.host,
        "original_url": url,
    }

    response = jsonify(response_data)

    if request.headers.get("Accept") == "application/json":
        return response
    else:
        return redirect(url_for("url_shortener.result", short_code=short_code))


@url_shortener.route("/emoji", methods=["GET", "POST"])
def emoji():
    emojies = request.values.get("emojies", None)
    url = request.values.get("url")
    password = request.values.get("password")
    max_clicks = request.values.get("max-clicks")
    block_bots = request.values.get("block-bots")

    if not url:
        return jsonify({"UrlError": "URL is required"}), 400

    if emojies:
        # emojies = unquote(emojies)
        if not validate_emoji_alias(emojies):
            return jsonify({"EmojiError": "Invalid emoji"}), 400

        if check_if_emoji_alias_exists(emojies):
            return jsonify({"EmojiError": "Emoji already exists"}), 400
    else:
        while True:
            emojies = generate_emoji_alias()

            if not check_if_emoji_alias_exists(emojies):
                break

    if url and not validate_url(url):
        return (
            jsonify(
                {
                    "UrlError": "Invalid URL, URL must have a valid protocol and must follow rfc_1034 & rfc_2728 patterns"
                }
            ),
            400,
        )

    if url and not validate_blocked_url(url):
        return jsonify({"UrlError": "Blocked URL ⛔"}), 403

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
        if not validate_password(password):
            return (
                jsonify(
                    {
                        "PasswordError": "Invalid password, password must be atleast 8 characters long, must contain a letter and a number and a special character either '@' or '.' and cannot be consecutive"
                    }
                ),
                400,
            )
        data["password"] = password

    if max_clicks:
        if not is_positive_integer(max_clicks):
            return (
                jsonify({"MaxClicksError": "max-clicks must be an positive integer"}),
                400,
            )
        else:
            max_clicks = str(abs(int(str(max_clicks))))
        data["max-clicks"] = max_clicks

    if block_bots:
        data["block-bots"] = True

    insert_emoji_url(emojies, data)

    response_data = {
        "short_url": f"{request.host_url}{emojies}",
        "domain": request.host,
        "original_url": url,
    }

    response = jsonify(response_data)

    if request.headers.get("Accept") == "application/json":
        return response

    return redirect(url_for("url_shortener.result", short_code=emojies))


@url_shortener.route("/result/<short_code>", methods=["GET"])
@limiter.exempt
def result(short_code):
    short_code = unquote(short_code)
    v2 = False
    if validate_emoji_alias(short_code):
        url_data = load_emoji_url(short_code)
    else:
        # Try new V2 schema first (aliases >=7 by default but custom may be shorter)
        url_data = get_url_v2_by_alias(short_code)
        v2 = True
        if not url_data:
            url_data = load_url(short_code)

    if url_data:
        if v2:
            short_code = url_data["alias"]
        else:
            short_code = url_data["_id"]
        short_url = f"{request.host_url}{short_code}"
        return render_template(
            "result.html",
            short_url=short_url,
            short_code=short_code,
            host_url=request.host_url,
        )
    else:
        return (
            render_template(
                "error.html",
                error_code="404",
                error_message="URL NOT FOUND",
                host_url=request.host_url,
            ),
            404,
        )


METRIC_PIPELINE = [
    {
        "$group": {
            "_id": None,
            "total-shortlinks": {"$sum": 1},
            "total-clicks": {"$sum": "$total-clicks"},
        }
    }
]


@url_shortener.route("/metric")
@limiter.exempt
def metric():
    def query():
        result = urls_collection.aggregate(METRIC_PIPELINE).next()
        del result["_id"]
        result["total-clicks-raw"] = result["total-clicks"]
        result["total-shortlinks-raw"] = result["total-shortlinks"]
        result["total-clicks"] = humanize_number(result["total-clicks"])
        result["total-shortlinks"] = humanize_number(result["total-shortlinks"])
        return result

    return jsonify(dual_cache.get_or_set("metrics", query))
