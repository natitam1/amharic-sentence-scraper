# Mixed Source Collection

The pipeline supports natural Amharic from authorized podcast, interview, radio, story, lecture, drama, educational, and community transcripts.

## Prepare inputs

Place UTF-8 files into the matching folder under `input/`:

```text
input/podcasts/
input/interviews/
input/radio/
input/stories/
input/lectures/
input/drama/
input/educational/
input/community/
```

Supported formats are TXT, JSONL, SRT, and VTT. JSONL uses the `text` field by default. SRT and VTT timestamps, cue numbers, markup, duplicate caption lines, and optional speaker labels are removed before the shared sentence pipeline runs.

Only collect material you have permission to process. Keep original source URLs and licensing records outside the public repository.

## Run a category

```bash
python main.py --sources local_podcast_transcripts --sample 20
```

Run several natural-speech categories:

```bash
python main.py --content-types podcast interview radio story --sample 20
```

Disabled local sources can be selected explicitly with `--sources`. Set `enabled: true` only when you want them included in every normal run.

## Balance the corpus

Limit every content type to the same total size:

```bash
python main.py --max-sentences-per-type 5000
```

Existing records without `content_type` are counted as `news` for backward compatibility. Every new record includes its category.

## Export selected categories

```bash
python examples/export_text.py data/amharic_sentences.jsonl data/natural.txt --content-types podcast interview radio story --limit 10000
```

You may also filter with `--sources`, `--min-words`, and `--max-words`.
