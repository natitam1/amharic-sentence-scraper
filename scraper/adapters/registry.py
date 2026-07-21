from scraper.adapters.generic_news import GenericNewsAdapter
from scraper.adapters.local_transcript import LocalTranscriptAdapter
from scraper.adapters.youtube_playlist import YouTubePlaylistAdapter

ADAPTERS = {
    "generic_news": GenericNewsAdapter,
    "generic_web": GenericNewsAdapter,
    "local_transcript": LocalTranscriptAdapter,
    "youtube_playlist": YouTubePlaylistAdapter,
}


def build_adapter(source_id: str, config: dict, fetcher):
    adapter_name = config["adapter"]
    try:
        adapter_class = ADAPTERS[adapter_name]
    except KeyError as exc:
        raise ValueError(f"Unknown adapter {adapter_name!r} for {source_id}") from exc
    return adapter_class(source_id, config, fetcher)
