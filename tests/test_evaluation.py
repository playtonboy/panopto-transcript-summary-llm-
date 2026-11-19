from evaluation.consistency import overlap
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

def test_overlap_counts_matching_bullets():
    run_a = ["Unit tests check one function.", "Integration tests check parts together."]
    run_b = ["Unit tests check a single function.", "Something completely different."]
    assert overlap(run_a, run_a) == 1.0
    assert overlap(run_a, run_b) == 0.5
    assert overlap([], run_b) == 0.0


def test_report_table_has_one_row_per_lecture_and_level_and_totals(tmp_path):
    from evaluation.report import read_scores, table

    after = tmp_path / "after.csv"
    after.write_text(
        "lecture,detail_level,bullet_no,bullet,score\n"
        "l01,Short,1,A,1\nl01,Short,2,B,-1\nl01,Medium,1,C,1\nl01,Medium,2,D,\nl02,Short,1,E,0\n",
        encoding="utf-8",
    )
    before = tmp_path / "before.csv"
    before.write_text("lecture,detail_level,bullet_no,bullet,score\nl01,Short,1,A,-1\n", encoding="utf-8")

    text = table(read_scores(after), read_scores(before))
    assert "| l01 | Short | +0.00 | 1 of 2 | -1.00 |" in text
    assert "| l01 | Medium | +1.00 | 0 of 1 | - |" in text
    assert "| **All lectures** | Short | **+0.00** | 1 of 3 | -1.00 |" in text
    assert text.index("| l01 | Short") < text.index("| l01 | Medium")
