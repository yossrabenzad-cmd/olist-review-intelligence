import numpy as np

from src.themes import find_themes, themes_to_markdown


def fake_embed(texts):
    """Refund complaints point one way, delivery complaints another."""
    rng = np.random.default_rng(0)
    vecs = []
    for t in texts:
        base = np.array([1.0, 0.0]) if "refund" in t else np.array([0.0, 1.0])
        v = base + rng.normal(0, 0.05, 2)
        vecs.append(v / np.linalg.norm(v))
    return np.array(vecs)


REFUNDS = [f"still waiting for my refund after {i} weeks" for i in range(12)]
DELIVERY = [f"delivery was late by {i} days" for i in range(18)]


def test_too_few_complaints_gives_no_themes():
    assert find_themes(REFUNDS[:5], fake_embed) == []
    assert "too few" in themes_to_markdown([])


def test_two_clear_groups_are_found_largest_first():
    themes = find_themes(REFUNDS + DELIVERY, fake_embed, max_themes=2)
    assert [t["size"] for t in themes] == [18, 12]
    assert "delivery" in " ".join(themes[0]["words"])
    assert "refund" in " ".join(themes[1]["words"])
    assert abs(sum(t["share"] for t in themes) - 100) < 0.2


def test_markdown_lists_each_theme():
    md = themes_to_markdown(find_themes(REFUNDS + DELIVERY, fake_embed, max_themes=2))
    assert "Theme 1: 18 complaints (60%)" in md and "Theme 2: 12 complaints (40%)" in md
