# Core settings
DEFAULT_CATEGORY = ""
DISPLAY_CATEGORIES_ON_MENU = False
DELETE_OUTPUT_DIRECTORY = True
# MARKDOWN
MARKDOWN = {
    "extension_configs": {
        "markdown.extensions.codehilite": {"css_class": "highlight"},
        "markdown.extensions.extra": {},
        "markdown.extensions.meta": {},
        "markdown.extensions.smarty": {},
        "plugins.mermaid": {},
    },
    "output_format": "html5",
}
PATH = "content"
ARTICLE_PATHS = ["posts"]
SITENAME = "Below the ABI"
STATIC_PATHS = ["static"]
SUMMARY_MAX_LENGTH = None
SUMMARY_MAX_PARAGRAPHS = 1
ARTICLE_URL = "posts/{slug}/"
ARTICLE_SAVE_AS = "posts/{slug}/index.html"
DRAFT_URL = "drafts/posts/{slug}/"
DRAFT_ARTICLE_SAVE_AS = "drafts/posts/{slug}/index.html"
AUTHOR_URL = ""
AUTHOR_SAVE_AS = ""
CATEGORY_URL = ""
CATEGORY_SAVE_AS = ""
AUTHORS_SAVE_AS = ""
CATEGORIES_SAVE_AS = ""
SLUGIFY_SOURCE = "basename"
TIMEZONE = "Europe/Warsaw"
LOCALE = "C"
TEMPLATE_PAGES = {
    "sitemap.xml": "sitemap.xml",
    "404.html": "404.html",
    "robots.txt": "robots.txt",
}
DIRECT_TEMPLATES = ["index", "tags", "archives"]  # 'categories', 'authors'
AUTHOR = "Viktor Ostashevskyi"
EXTRA_PATH_METADATA = {
    "static/apple-touch-icon.png": {"path": "apple-touch-icon.png"},
    "static/favicon.ico": {"path": "favicon.ico"},
    "static/favicon.svg": {"path": "favicon.svg"},
    "static/.nojekyll": {"path": ".nojekyll"},
}
FEED_ATOM = None
FEED_ATOM_URL = None
FEED_RSS = "feeds/rss.xml"
FEED_RSS_URL = None
FEED_ALL_ATOM = None
FEED_ALL_ATOM_URL = None
FEED_ALL_RSS = None
FEED_ALL_RSS_URL = None
CATEGORY_FEED_ATOM = None
CATEGORY_FEED_ATOM_URL = None
CATEGORY_FEED_RSS = None
CATEGORY_FEED_RSS_URL = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_ATOM_URL = None
AUTHOR_FEED_RSS = None
AUTHOR_FEED_RSS_URL = None
TAG_FEED_ATOM = None
TAG_FEED_ATOM_URL = None
TAG_FEED_RSS = None
FEED_MAX_ITEMS = None
RSS_FEED_SUMMARY_ONLY = True
FEED_APPEND_REF = True
DEFAULT_PAGINATION = 10
DEFAULT_LANG = "en"
TRANSLATION_FEED_ATOM = None
THEME = "theme"
SITESUBTITLE = "where compilers stop"
# MENUITEMS [(title, url)]
# LINKS  [(title, url)]
SOCIAL = [("GitHub", "https://github.com/ostash")]
SOCIAL_WIDGET_NAME = None

# Theme specific settings
DEFAULT_COPYRIGHT_YEAR = 2026
DEFAULT_LICENSE = "CC-BY-4.0"
GISCUS = {
    "repo": "ostash/ostash.github.io",
    "repo-id": "R_kgDORnAUMA",
    "category": "Announcements",
    "category-id": "DIC_kwDORnAUMM4C4bu-",
    "mapping": "pathname",
    "strict": "1",
    "reactions-enabled": "1",
    "emit-metadata": "0",
    "input-position": "top",
    "theme": "dark",
}
SITE_DESCRIPTION = "A learning journal about building an LLVM backend for the 8086, documenting every step from scratch."

# Things which differs for publish
SITEURL = ""
RELATIVE_URLS = True
ANALYTICS = None
