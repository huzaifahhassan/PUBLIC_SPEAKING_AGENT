import webbrowser
import urllib.parse

def google_search(query):
    """
    Performs a Google search by opening a new tab in the default web browser.

    Args:
        query (str): The search term you want to look up on Google.
    """
    # URL encode the query to handle spaces and special characters
    encoded_query = urllib.parse.quote_plus(query)
    
    # Construct the Google search URL
    search_url = f"https://www.google.com/search?q={encoded_query}"
    
    print(f"Searching for '{query}'...")
    print(f"Opening URL: {search_url}")
    
    # Open the URL in a new tab of the default browser
    webbrowser.open_new_tab(search_url)

# --- Example Usage ---

# 1. Simple search with a predefined query
# search_term = "how to learn python"
# google_search(search_term)


# 2. Interactive search (uncomment the lines below to use)
search_input = input("Enter what you want to search on Google: ")
if search_input:
    google_search(search_input)
else:
    print("No search term entered. Exiting.")