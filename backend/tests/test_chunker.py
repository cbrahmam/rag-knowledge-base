from services.chunker import adaptive_params, chunk_document, chunk_text


def test_adaptive_params_per_type():
    assert adaptive_params("md") == (800, 100)
    assert adaptive_params("txt") == (500, 50)
    # Unknown type falls back to the default.
    assert adaptive_params("rtf") == (500, 50)


def test_chunk_text_empty_returns_no_chunks():
    assert chunk_text("", "empty.txt") == []
    assert chunk_text("   \n  ", "blank.txt") == []


def test_chunk_document_produces_unique_ordered_indices():
    text = "Sentence one. Sentence two. " * 60
    chunks = chunk_document(text, "t.txt", "txt")
    assert len(chunks) > 1
    indices = [c.chunk_index for c in chunks]
    assert indices == list(range(len(chunks)))  # 0..n-1, unique + ordered


def test_chunk_document_markdown_splits_on_headings():
    md = "# Intro\nHello.\n\n## Details\nMore text here.\n\n## More\nEven more."
    chunks = chunk_document(md, "d.md", "md")
    # Each heading section becomes at least one chunk, re-indexed uniquely.
    assert len(chunks) >= 3
    assert len({c.chunk_index for c in chunks}) == len(chunks)


def test_chunk_document_respects_custom_size():
    # Sentences give the chunker boundaries to split on.
    text = "Word here. " * 400
    small = chunk_document(text, "t.txt", "txt", chunk_size=200, overlap=0)
    large = chunk_document(text, "t.txt", "txt", chunk_size=1000, overlap=0)
    assert len(small) > len(large)
