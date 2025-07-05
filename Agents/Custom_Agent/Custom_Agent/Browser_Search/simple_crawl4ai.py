import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from bs4 import BeautifulSoup
import re

#==================================================================================================
# RUNNING ASYNC CRAWLER
#==================================================================================================
async def crawler(url):
    browser_conf = BrowserConfig(headless = False , 
                                 browser_mode = "dedicated" ,
                                 text_mode = False )  # or False to see the browser
    run_conf = CrawlerRunConfig(
        #css_selector="[class^='byrV5b']",  # Target specific content on the page
        cache_mode=CacheMode.BYPASS,
        verbose= False
    )

    async with AsyncWebCrawler(config=browser_conf) as crawler:
        result = await crawler.arun(
            url = url,
            config=run_conf
        )
        #print(result)
        return result

#==================================================================================================
# TOP URL EXTRACTOR
#==================================================================================================
async def extract_top_5_urls(query) -> list[str]:

    root_url = "https://www.google.com/search?q=" + query
    print("root url:" , root_url)
    http_result = await crawler(root_url)
    html_string = http_result[0].html

    soup = BeautifulSoup(html_string, 'html.parser')
    urls = []
    seen_urls = set()

    for cite_tag in soup.find_all('cite'):
        if len(urls) >= 3:
            break

        # Extract text which often looks like: "https://example.com › path › to › page"
        raw_url_text = cite_tag.get_text()
        # Reconstruct the URL by replacing separators and cleaning up
        # Replace breadcrumb separator ' › ' with a URL slash '/'
        # Remove ellipsis '...' which indicates a truncated URL
        # Strip any leading/trailing whitespace
        full_url = raw_url_text.replace(' › ', '/').replace('...', '').strip()

        # Ensure we only add unique URLs
        if full_url not in seen_urls:
            urls.append(full_url)
            seen_urls.add(full_url)
    return urls

#==================================================================================================
# EXTRACTING MEANINGFUL TEXT FROM STRING
#==================================================================================================
def extract_meaningful_text(markdown_text):
    """
    Cleans a markdown string scraped from a webpage to extract only the
    meaningful article text.

    Args:
        markdown_text (str): The raw markdown content scraped from a page.

    Returns:
        str: A clean string containing only the article's text.
    """
    # --- 1. Isolate the main article content ---
    # Find the start of the comments or FAQ section and cut off everything after it.
    stop_phrases = [
        "## Frequently Asked Questions",
        "#### Comments",
        "### Leave a Comment",
        "Test your Knowledge on Global Warming"
    ]
    stop_index = -1
    for phrase in stop_phrases:
        found_index = markdown_text.find(phrase)
        if found_index != -1:
            if stop_index == -1 or found_index < stop_index:
                stop_index = found_index
    
    if stop_index != -1:
        text = markdown_text[:stop_index]
    else:
        text = markdown_text

    # --- 2. Remove major markdown elements and noise with regex ---
    
    # Remove image links like ![](...)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    
    # Remove table of contents and other specific links, but keep the text
    # e.g., '[What is Global Warming?](...)' -> 'What is Global Warming?'
    text = re.sub(r'\[(.*?)\]\(https?://[^\)]+\)', r'\1', text)
    
    # Remove standalone numbers that are likely view counts
    text = re.sub(r'^\d{1,3}(,\d{3})*$', '', text, flags=re.MULTILINE)

    # --- 3. Clean up formatting and combine lines ---
    cleaned_lines = []
    for line in text.split('\n'):
        # Strip markdown headers, blockquotes, and extra whitespace
        line = re.sub(r'^[#>\s]+', '', line)
        line = line.replace('_', '').replace('*', '').strip()

        # Add the line if it's not empty
        if line:
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)

#==================================================================================================
# EXTRACTING FROM TOP URL
#==================================================================================================
async def url_content_extracter(urls):
    content = []
    for i in range (len(urls)):
        url = urls[i]
        http_result = await crawler(url)
        markdown_result = http_result.markdown
        clean_markdown = extract_meaningful_text(markdown_result)
        content.append(clean_markdown)
    return content

#==================================================================================================
# CRAWLER RUNNER
#==================================================================================================
async def url_runner(query):
    urls = extract_top_5_urls(query = query)
    urls = await urls
    print("No. of URLs: " , len(urls))
    print("URLs: " , urls)
    final_content = url_content_extracter(urls=urls)
    final_content = await final_content
    return final_content

# query = "global warming"
# content = runner(query)
# print("Content: " , content)


# if __name__ == "__crawler__":
#     asyncio.run(crawler())

# Learn to Extract Web Pages from The Results
