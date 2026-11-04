from evaluation.judge import parse_scores, summary_bullets

BODY = "## Main topics\n- Testing\n\n## Summary\n- Point one.\n- Point two.\n\n## Action items\n- Hand in Task 5"


def test_summary_bullets_takes_only_the_summary_section():
    assert summary_bullets(BODY) == ["Point one.", "Point two."]


def test_parse_scores_reads_one_line_per_bullet():
    assert parse_scores("1: 1\n2: -1\n3: 0", 3) == [1, -1, 0]
    assert parse_scores("1. -1\n2) 1", 2) == [-1, 1]


def test_parse_scores_handles_messy_answers():
    assert parse_scores("1: 5\n3: -1", 3) == [1, None, -1]  # out of range is clamped, skipped bullet is None
    assert parse_scores("1 -1 0", 3) == [1, -1, 0]        # plain numbers in order
    assert parse_scores("no idea", 2) == [None, None]      # unreadable: not scored