# utils.py
def paginate_data(data, page, items_per_page):
    total_items = len(data)
    total_pages = (total_items + items_per_page - 1) // items_per_page
    start = (page - 1) * items_per_page
    end = start + items_per_page
    paginated_data = data[start:end]

    return paginated_data, total_pages


def filter_data(
    data, getLocale, search_query, title_key="title", description_key="description"
):
    """Filter data based on the search query."""
    if not search_query:
        return data

    # Convert search query to lowercase
    search_query = search_query.strip().lower()

    return [
        item
        for item in data
        if search_query in item[title_key][getLocale].lower()
        or search_query in item[description_key][getLocale].lower()
    ]