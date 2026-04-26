"""Unit tests: `_compute_token_stats` field summation across cache categories.

Seed: #3 § 3.7 item 4. Regression target: README §B (cache fields must sum).
"""

import json
from pathlib import Path

from claude_busy_monitor._sessions import TokenStats, _compute_token_stats


def _write_transcript(path: Path, entries: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(e) for e in entries))


def test_token_stats_sums_input_plus_cache_creation_plus_cache_read(tmp_path):
    transcript = tmp_path / "session.jsonl"
    _write_transcript(
        transcript,
        [
            {
                "type": "assistant",
                "message": {
                    "usage": {
                        "input_tokens": 100,
                        "cache_creation_input_tokens": 200,
                        "cache_read_input_tokens": 300,
                        "output_tokens": 50,
                    }
                },
            }
        ],
    )
    assert _compute_token_stats(transcript) == TokenStats(output=50, input=600)


def test_token_stats_aggregates_across_assistant_entries(tmp_path):
    transcript = tmp_path / "session.jsonl"
    _write_transcript(
        transcript,
        [
            {
                "type": "assistant",
                "message": {"usage": {"input_tokens": 10, "output_tokens": 5}},
            },
            {
                "type": "user",
                "message": {"usage": {"input_tokens": 999, "output_tokens": 999}},
            },
            {
                "type": "assistant",
                "message": {"usage": {"input_tokens": 20, "output_tokens": 10}},
            },
        ],
    )
    assert _compute_token_stats(transcript) == TokenStats(output=15, input=30)


def test_token_stats_returns_none_when_path_is_none():
    assert _compute_token_stats(None) is None


def test_token_stats_skips_invalid_lines(tmp_path):
    transcript = tmp_path / "session.jsonl"
    transcript.write_text(
        "garbage{not-json\n"
        + json.dumps(
            {
                "type": "assistant",
                "message": {"usage": {"input_tokens": 5, "output_tokens": 3}},
            }
        )
        + "\n\n"
    )
    assert _compute_token_stats(transcript) == TokenStats(output=3, input=5)


def test_token_stats_handles_missing_usage_field(tmp_path):
    transcript = tmp_path / "session.jsonl"
    _write_transcript(
        transcript,
        [
            {"type": "assistant", "message": {}},
            {
                "type": "assistant",
                "message": {"usage": {"input_tokens": 7, "output_tokens": 4}},
            },
        ],
    )
    assert _compute_token_stats(transcript) == TokenStats(output=4, input=7)
