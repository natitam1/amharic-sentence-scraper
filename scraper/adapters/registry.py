from scraper.adapters.generic_news import GenericNewsAdapter

ADAPTERS = {"generic_news": GenericNewsAdapter}


def build_adapter(source_id: str, config: dict, fetcher):
    adapter_name = config["adapter"]
    try:
        adapter_class = ADAPTERS[adapter_name]
    except KeyError as exc:
        raise ValueError(f"Unknown adapter {adapter_name!r} for {source_id}") from exc
    return adapter_class(source_id, config, fetcher)

