from chat_console.chat import SUMMARY_MAX_CHARS, _summarize, _word_chunks


def test_word_chunks_rejoins_to_original() -> None:
    text = "one two three four five six seven eight nine ten"
    assert "".join(_word_chunks(text, size=10)).strip() == text


def test_word_chunks_single_short_text_is_one_chunk() -> None:
    assert _word_chunks("hi there") == ["hi there"]


def test_word_chunks_empty_text() -> None:
    assert _word_chunks("") == [""]


def test_summarize_short_text_passthrough() -> None:
    assert _summarize("all good") == "all good"


def test_summarize_collapses_whitespace() -> None:
    assert _summarize("a\n\n  b   c") == "a b c"


def test_summarize_truncates_long_text() -> None:
    long_text = "x" * (SUMMARY_MAX_CHARS + 50)
    summary = _summarize(long_text)
    assert len(summary) == SUMMARY_MAX_CHARS
    assert summary.endswith("…")
