# test_mercari_lib.py
from mercari import search, MercariSort, MercariOrder, MercariSearchStatus

keyword = "iPhone15 Pro 256GB"
# Problematic keywords
exclude = "11 12 13 14 16 ジャンク max".split()

try:
    print(f"Testing search with keyword='{keyword}', exclude_keywords={exclude}")
    results = search(
        keyword,
        sort=MercariSort.SORT_PRICE,
        order=MercariOrder.ORDER_ASC,
        status=MercariSearchStatus.ON_SALE,
        exclude_keywords=exclude # Pass the list directly
    )
    print(f"Success! Found {len(results)} items.")
except Exception as e:
    print(f"Error calling mercari.search directly: {e}")