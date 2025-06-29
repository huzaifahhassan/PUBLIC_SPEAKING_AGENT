import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

def get_search_results_selenium(query, num_results=5):
    """
    Performs a Google search using Selenium to render JavaScript and returns the URLs of the top results.
    
    Args:
        query (str): The search term.
        num_results (int): The number of search result URLs to return.

    Returns:
        list: A list of URLs from the search results.
    """
    search_url = f"https://www.google.com/search?q={query}"
    
    print(f"Searching for '{query}' using Selenium...")

    # Set up the Selenium WebDriver
    # webdriver-manager will automatically download and manage the driver for you.
    options = webdriver.ChromeOptions()
    #options.add_argument('--headless')  # Run in headless mode (no browser window opens)
    options.add_argument('--log-level=3') # Suppress console logs
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Go to the Google search page
        driver.get(search_url)

        # Let the page load. You might need to increase this if results aren't loading.
        time.sleep(40) 

        # Now that the JavaScript has run, get the page source
        page_source = driver.page_source
        
        # Parse the HTML content
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # This selector is more robust for finding search result links in the rendered HTML.
        # It targets the `<a>` tag within an `<h3>` which is a common pattern for result titles.
        link_elements = soup.select('div.g h3 > a') 
        
        urls = [link.get('href') for link in link_elements[:num_results]]
                
        if not urls:
            print("Could not find any search results. Google's page structure may have changed, or the request was blocked.")

        return urls

    except Exception as e:
        print(f"An error occurred while fetching search results with Selenium: {e}")
        return []
    finally:
        # Important: always close the driver
        driver.quit()

def get_content_from_url(url):
    """
    Fetches and extracts the main text content from a given URL using requests.
    This function remains the same as individual pages are often less protected.

    Args:
        url (str): The URL to fetch content from.

    Returns:
        str: The extracted text content, or an error message.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
            
        # Get text from all paragraphs as a simple extraction method
        paragraphs = soup.find_all('p')
        content = ' '.join(p.get_text(strip=True) for p in paragraphs)
        
        return content if content else "No paragraph content found."

    except requests.exceptions.RequestException as e:
        return f"Error fetching content: {e}"

# --- Main Execution ---

if __name__ == "__main__":
    search_query = input("Enter what you want to search on Google: ")
    if search_query:
        # Get the top 5 search result URLs using the new Selenium function
        result_urls = get_search_results_selenium(search_query, num_results=5)
        
        if result_urls:
            print(f"\n--- Found {len(result_urls)} URLs ---")
            for i, url in enumerate(result_urls):
                print(f"{i+1}. {url}")
            
            print("\n--- Fetching Content ---")
            for i, url in enumerate(result_urls):
                print(f"\n\n--- Content from link #{i+1} ---\nURL: {url}")
                content = get_content_from_url(url)
                # Print a snippet of the content
                print(f"Snippet: {content[:500]}...")
    else:
        print("No search term entered. Exiting.")
