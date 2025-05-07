from typing import Any, Dict, List, Optional

from mercari import (MercariOrder, MercariSearchStatus, MercariSort, search)

from pydantic import Field

from fastmcp import FastMCP

mercari_mcp = FastMCP(name="MercariSearchComplete", dependencies=["mercari"])

@mercari_mcp.tool(name="search_mercari_jp", 
                description="""Search Mercari for items, excluding keywords and filtering by price and specific model name.
                Args:
                    keyword (str): The main keyword to search for (e.g., 'iPhone15 Pro 256GB'). Optimize this to ensure the product name is correct, sometimes it has to be in Japanese.
                    exclude_keywords (str): Space-separated keywords to exclude. Think about exclude keywords that can make the search more precise. Generate this in japanese. For example, 'ジャンク', 'max', 'plus', '11', '12', '13', '14', '16', 'ケース', 'カバー', 'フィルム' when searching for iPhone15 Pro 256GB. Don't forget to separate them with space.
                    min_price (int, optional): Minimum price in JPY. Think about the minimum price that you are willing to pay for the item. For example, if you are looking for a new iPhone15 Pro 256GB, you might want to set a minimum price of 100000 JPY.
                    max_price (int, optional): Maximum price in JPY. Think about the maximum price that you are willing to pay for the item. For example, if you are looking for a new iPhone15 Pro 256GB, you might want to set a maximum price of 200000 JPY.
                    limit (int): Maximum number of items to return.""")
def search_mercari_items_filtered(
    keyword: str = Field(..., description="The main keyword to search for (e.g., 'iPhone15 Pro 256GB')."),
    exclude_keywords: str = Field("", description="Space-separated keywords to exclude (e.g., 'ジャンク max')."),
    min_price: Optional[int] = Field(None, description="Minimum price in JPY.", ge=0),
    max_price: Optional[int] = Field(None, description="Maximum price in JPY.", ge=0),
    limit: int = Field(20, description="Maximum number of items to return.", ge=1)
) -> List[Dict[str, Any]]:
    """
    Performs a search on Mercari Japan using a keyword, excluding specified keywords,
    and filtering results by the provided price range.
    Additionally filters results based on keywords derived from the input keyword
    and exclude_keywords to ensure the product name closely matches the desired model.
    Uses default sorting (price ascending) and only shows items on sale.

    Returns:
        A list of dictionaries for items matching all criteria, limited to the specified number.
        Returns an empty list if no items are found or an error occurs.
    """
    try:
        # Use mercari.search with the provided keyword and exclusion list as a first pass.
        # The mercari.search function handles the initial exclusion based on the provided string.
        # We still pass the original exclude_keywords string here for the initial broad filtering.
        search_results = search(
            keyword,
            sort=MercariSort.SORT_SCORE, # Keep initial sort/order for broad results
            order=MercariOrder.ORDER_DESC,
            status=MercariSearchStatus.ON_SALE,
            exclude_keywords=exclude_keywords # Pass the exclusion keywords string for the initial search
        )

        items_found: List[Dict[str, Any]] = []

        # --- Dynamic Filtering Setup ---
        # Split the input keyword into required terms (convert to lowercase)
        required_terms = [term.lower() for term in keyword.split()]

        # Define base unwanted terms and add terms from exclude_keywords (convert to lowercase)
        # We keep some base unwanted terms that might not be in the exclude_keywords input
        # but are generally undesirable for a specific model search (like older models).
        base_unwanted_terms = ["max", "plus", "11", "12", "13", "14", "16", "ジャンク"]
        unwanted_terms_from_input = [term.lower() for term in exclude_keywords.split()]
        # Combine both lists and remove duplicates
        all_unwanted_terms = list(set(base_unwanted_terms + unwanted_terms_from_input))

        # Remove any required terms from the unwanted terms list
        # This is important if a required term (like "pro") is also in the unwanted list
        # due to variations like "pro max". We want to prioritize the required term.
        all_unwanted_terms = [term for term in all_unwanted_terms if term not in required_terms]

        # Print the terms being used for filtering (optional, for debugging)
        # print(f"Required terms: {required_terms}")
        # print(f"Unwanted terms: {all_unwanted_terms}")
        # --- End Dynamic Filtering Setup ---


        for item in search_results:
            try:
                # Get product name and price, skip if not available
                product_name = getattr(item, 'productName', None)
                if product_name is None:
                    # print(f"Warning: Skipping item due to missing product name.") # Uncomment for debugging
                    continue # Skip this item

                price = getattr(item, 'price', None)
                # Check if price is valid and convert to float, skip if not
                if price is None:
                    # print(f"Warning: Skipping item '{product_name}' due to missing price.") # Uncomment for debugging
                    continue # Skip this item
                try:
                    price = float(price)
                except (ValueError, TypeError):
                    # print(f"Warning: Skipping item '{product_name}' due to invalid price format: {price}") # Uncomment for debugging
                    continue # Skip this item if price conversion fails


                # --- Additional Filtering Logic ---
                # Convert product name to lowercase for case-insensitive comparison
                lower_product_name = product_name.lower()

                # Check if the product name contains ALL the required terms
                # We check if all required terms are present in the lower_product_name string
                name_contains_desired_keywords = all(
                    term in lower_product_name for term in required_terms
                )

                # Check if the product name contains ANY of the unwanted terms
                # We check if any unwanted term is present in the lower_product_name string
                name_contains_unwanted_terms = any(
                    term in lower_product_name for term in all_unwanted_terms
                )

                # Only proceed if the name contains ALL desired keywords and does NOT contain ANY unwanted terms
                if name_contains_desired_keywords and not name_contains_unwanted_terms:
                    # Check if the item's price is within the specified range
                    min_check_passed = (min_price is None) or (price >= min_price)
                    max_check_passed = (max_price is None) or (price <= max_price)

                    # If both price checks pass, add the item to the results
                    if min_check_passed and max_check_passed:
                        items_found.append({
                            "name": product_name,
                            "url": getattr(item, 'productURL', 'N/A'), # Get product URL, default to 'N/A'
                            "price": price,
                        })

                        # Stop collecting items once we've reached the limit
                        if len(items_found) >= limit:
                            break # Exit the loop early


            # Catch errors during attribute access or string operations within the loop
            except (AttributeError) as filter_err:
                print(f"Warning: Skipping item during post-filtering due to data access error: {filter_err}")
                continue # Move to the next item
            except Exception as unexpected_err:
                print(f"Warning: Skipping item due to unexpected error during filtering: {unexpected_err}")
                continue # Catch any other unexpected errors during processing a single item


        return items_found # Return the list of found items

    except Exception as e:
        # Catch any other exceptions during the initial search process
        print(f"Error: An error occurred during Mercari search: {e}")
        # Re-raise the exception to be handled by the caller if necessary,
        # or return an empty list to indicate failure gracefully.
        # Raising allows the caller (FastMCP client) to know an error occurred.
        raise e

if __name__ == "__main__":
    # This block runs the FastMCP server when the script is executed directly
    mercari_mcp.run()
