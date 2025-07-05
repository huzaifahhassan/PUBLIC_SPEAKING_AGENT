import requests
from bs4 import BeautifulSoup
import webbrowser
import urllib.parse

def get_search_results(query, num_results=5):
    """
    Performs a Google search and returns the URLs of the top results.
    
    Args:
        query (str): The search term.
        num_results (int): The number of search result URLs to return.

    Returns:
        list: A list of URLs from the search results.
    """
    # URL encode the query
    encoded_query = urllib.parse.quote_plus(query)
    search_url = f"https://www.google.com.pk/search?q={encoded_query}"
    
    # Set headers to mimic a real browser visit
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    print(f"Searching for '{query}'...")
    
    try:
        # Fetch the search results page
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        print("Raw Extracted Results:" , soup)
        
        # Find all the search result links. Google often puts these in <h3> tags.
        # This is fragile and may break if Google changes its page structure.
        link_elements = soup.select('div.g a') # A more reliable selector
        
        urls = []
        for link in link_elements:
            href = link.get('href')
            if href and href.startswith('/url?q='):
                # Clean up the URL
                clean_url = href.split('/url?q=')[1].split('&sa=U')[0]
                if clean_url not in urls:
                    urls.append(clean_url)
            if len(urls) >= num_results:
                break
                
        if not urls:
            print("Could not find any search results. Google might have blocked the request.")
            print("You can try opening the search URL directly in your browser:")
            print(search_url)
            webbrowser.open_new_tab(search_url)

        return urls

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching search results: {e}")
        return []

def get_content_from_url(url):
    """
    Fetches and extracts the main text content from a given URL.

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
        # Get the top 5 search result URLs
        result_urls = get_search_results(search_query, num_results=5)
        
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
