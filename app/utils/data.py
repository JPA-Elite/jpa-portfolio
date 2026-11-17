import random


def paginate_data(data, page, items_per_page):
    total_items = len(data)
    total_pages = (total_items + items_per_page - 1) // items_per_page
    start = (page - 1) * items_per_page
    end = start + items_per_page
    paginated_data = data[start:end]

    return paginated_data, total_pages


def filter_data(
    data, getLocale, search_query, tags=None,
    title_key="title", description_key="description", tags_key="tags", id_key="id"
):
    """Filter data based on the search query and tags."""
    search_query = search_query.strip().lower() if search_query else ''
    tags = set(tags.split('.')) if tags else set()

    filtered_data = []
    seen_ids = set()

    if tags:
        for item in data:
            item_tags = set(item.get(tags_key, []))
            if item_tags & tags:
                item_id = item.get(id_key)
                if item_id not in seen_ids:
                    filtered_data.append(item)
                    seen_ids.add(item_id)

        if search_query:
            filtered_data = [
                item for item in filtered_data
                if search_query in item[title_key].get(getLocale, "").lower()
                or search_query in item[description_key].get(getLocale, "").lower()
            ]

        return filtered_data

    if search_query:
        return [
            item for item in data
            if search_query in item[title_key].get(getLocale, "").lower()
            or search_query in item[description_key].get(getLocale, "").lower()
        ]

    return data


def get_random_tags(data, tags_length=10):
    unique_tags = set()

    if not data:
        return []

    if isinstance(data[0], dict):
        for item in data:
            if "tags" in item and isinstance(item["tags"], list):
                unique_tags.update(item["tags"])
    elif isinstance(data[0], str):
        unique_tags.update(data)

    unique_tags = list(unique_tags)
    random.shuffle(unique_tags)

    return unique_tags[:tags_length]


def num_to_alpha_lower(num_str: str):
    result = ""
    for char in num_str:
        if char.isdigit():
            n = int(char)
            if n == 0:
                result += "z"
            else:
                result += chr(96 + n)
        else:
            result += char
    return result
