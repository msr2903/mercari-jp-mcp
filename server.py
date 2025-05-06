from typing import Any, Dict, List, Optional

from mercari import (MercariOrder, MercariSearchStatus, MercariSort, search)

from pydantic import Field

from fastmcp import FastMCP

mercari_mcp = FastMCP(name="MercariSearchComplete", dependencies=["mercari"])

@mercari_mcp.tool(name="search_mercari_jp", description="Search Mercari for items, excluding keywords and filtering by price.")
def search_mercari_items_filtered(
    keyword: str = Field(..., description="The main keyword to search for."),
    exclude_keywords: str = Field("", description="Space-separated keywords to exclude."),
    min_price: Optional[int] = Field(None, description="Minimum price in JPY.", ge=0),
    max_price: Optional[int] = Field(None, description="Maximum price in JPY.", ge=0),
    limit: int = Field(20, description="Maximum number of items to return.", ge=1)
) -> List[Dict[str, Any]]:
    """
    Performs a search on Mercari Japan using a keyword, excluding specified keywords,
    and filtering results by the provided price range.
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
        items_processed_count = 0
        
        for item in search_results:
            items_processed_count += 1
            try:
                price = float(item.price)
                min_check_passed = (min_price is None) or (price >= float(min_price))
                max_check_passed = (max_price is None) or (price <= float(max_price))
                
                if min_check_passed and max_check_passed:
                    items_found.append({
                        "name": getattr(item, 'productName', 'N/A'),
                        "url": getattr(item, 'productURL', 'N/A'),
                        "price": price,
                    })
                    
                    # Stop collecting items once we've reached the limit
                    if len(items_found) >= limit:
                        break
            except (ValueError, TypeError, AttributeError) as price_err:
                print(f"Warning: Skipping item during filtering due to invalid data: {price_err}")
                continue
                
        return items_found
    except Exception as e:
        print(f"Error: An error occurred during Mercari search: {e}")
        raise e

if __name__ == "__main__":
    mercari_mcp.run()
