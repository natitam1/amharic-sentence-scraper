# YouTube Playlist Collection

The `youtube_playlist` adapter enumerates videos with `yt-dlp`, requests Amharic subtitle tracks, and never downloads video or audio. Manual captions are preferred and automatic captions are used only as fallback.

The requested documentary playlist is configured as `ethiopian_documentary_playlist` and is disabled by default.

## Inspect and test

```bash
python main.py --list-sources
python main.py --sources ethiopian_documentary_playlist --max-articles 1 --sample 20 --verbose
```

## Collect the playlist

```bash
python main.py --sources ethiopian_documentary_playlist --max-articles 50 --sample 20
```

Re-running is idempotent. Videos with no configured Amharic VTT captions are reported as failures and may be retried later.

New JSONL records contain `content_type: documentary`, `video_id`, `title`, `channel`, `duration_seconds`, `transcript_language`, and `automatic_captions`.

If YouTube requires authentication for content you are permitted to access, set `cookie_file` in the source configuration to a local Netscape-format cookie file. Never commit that file. Review the playlist owner's terms and obtain permission before using transcripts for training or redistribution.

## Meri Podcast starter corpus

The channel source is configured as `meri_podcast_videos`:

```bash
python main.py --sources meri_podcast_videos --max-articles 1 --sample 20
```

Create a podcast-only text export with a 1,000-word ceiling while preserving complete sentences:

```bash
python examples/export_text.py data/amharic_sentences.jsonl data/meri_podcast_1000_words.txt --sources meri_podcast_videos --content-types podcast --max-total-words 1000
```

The exporter may finish slightly below the ceiling when the next complete sentence would exceed it. It never truncates a sentence to force an exact word total.
