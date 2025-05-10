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
        search_results = search(
            keyword,
            sort=MercariSort.SORT_SCORE,
            order=MercariOrder.ORDER_DESC,
            status=MercariSearchStatus.ON_SALE,
            exclude_keywords=exclude_keywords
        )

        items_found: List[Dict[str, Any]] = []
        required_terms = [term.lower() for term in keyword.split()]
        unwanted_terms_from_input = [term.lower() for term in exclude_keywords.split()]
        all_unwanted_terms = list(set(unwanted_terms_from_input))
        all_unwanted_terms = [term for term in all_unwanted_terms if term not in required_terms]


        for item in search_results:
            try:
                product_name = getattr(item, 'productName', None)
                if product_name is None:
                    continue

                price = getattr(item, 'price', None)
                if price is None:
                    continue
                try:
                    price = float(price)
                except (ValueError, TypeError):
                    continue

                lower_product_name = product_name.lower()
                name_contains_desired_keywords = all(
                    term in lower_product_name for term in required_terms
                )
                name_contains_unwanted_terms = any(
                    term in lower_product_name for term in all_unwanted_terms
                )

                if name_contains_desired_keywords and not name_contains_unwanted_terms:
                    min_check_passed = (min_price is None) or (price >= min_price)
                    max_check_passed = (max_price is None) or (price <= max_price)

                    if min_check_passed and max_check_passed:
                        items_found.append({
                            "name": product_name,
                            "url": getattr(item, 'productURL', 'N/A'),
                            "price": price,
                        })

                        if len(items_found) >= limit:
                            break

            except (AttributeError) as filter_err:
                print(f"Warning: Skipping item during post-filtering due to data access error: {filter_err}")
                continue
            except Exception as unexpected_err:
                print(f"Warning: Skipping item due to unexpected error during filtering: {unexpected_err}")
                continue
        return items_found

    except Exception as e:
        print(f"Error: An error occurred during Mercari search: {e}")
        raise e

if __name__ == "__main__":
    mercari_mcp.run()
