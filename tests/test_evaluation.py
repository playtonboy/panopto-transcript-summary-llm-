from evaluation.consistency import CHECK_PAIRS, check_matcher, overlap
from evaluation.key_points import recall, summary_text
from evaluation.matching import parse_yes_no
from evaluation.judge import parse_scores, summary_bullets

BODY = "## Main topics\n- Testing\n\n## Summary\n- Point one.\n- Point two.\n\n## Action items\n- Hand in Task 5"


def test_summary_bullets_takes_only_the_summary_section():
    assert summary_bullets(BODY) == ["Point one.", "Point two."]


def test_parse_scores_reads_one_line_per_bullet():
    assert parse_scores("1: 1\n2: -1\n3: 0", 3) == [1, -1, 0]
    assert parse_scores("1. -1\n2) 1", 2) == [-1, 1]


def test_parse_scores_handles_messy_answers():
    assert parse_scores("1: 5\n3: -1", 3) == [1, None, -1]  # out of range is clamped, skipped bullet is None
    assert parse_scores("1 -1 0", 3) == [1, -1, 0]  # plain numbers in order
    assert parse_scores("no idea", 2) == [None, None]  # unreadable: not scored


def test_overlap_counts_points_the_matcher_calls_the_same():
    run_a = ["Unit tests check one function.", "Integration tests check parts together."]
    run_b = ["Unit tests check a single function.", "Something completely different."]

    def same(a, b):
        return [point.startswith("Unit") for point in a]

    assert overlap(run_a, run_b, same) == 0.5
    assert overlap([], run_b, same) == 0.0
    assert overlap(run_a, run_b, lambda a, b: [None, None]) == 0.0  # no answer is not a match


def test_matcher_check_uses_the_feedback_pairs():
    assert len(CHECK_PAIRS) == 3
    assert check_matcher(lambda a, b: [a[0].endswith("noon.") and "12:00" in b[0]]) == 3
    assert check_matcher(lambda a, b: [True]) == 1  # a matcher that always says "same" fails two of them


def test_parse_yes_no_reads_one_answer_per_point():
    assert parse_yes_no("1: yes\n2: No\n3. yes", 3) == [True, False, True]
    assert parse_yes_no("1: yes\nI am not sure about 2", 2) == [True, None]


def test_key_point_recall_counts_missing_answers_as_not_found():
    assert recall([True, False, None, True]) == 0.5
    assert recall([]) == 0.0


def test_key_points_use_the_whole_summary_when_it_was_saved():
    assert summary_text({"body": "## Action items\n- Hand in Task 5", "bullets": ["x"]}).endswith("Task 5")
    assert summary_text({"bullets": ["One.", "Two."]}) == "- One.\n- Two."


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
