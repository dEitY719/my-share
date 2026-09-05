"""changelog_toggle 자체 점검: 기존 섹션 이관 / 토글 / 멱등 / 대상 없음.

    python3 scripts/test_changelog_toggle.py
"""

from changelog_toggle import BEGIN, END, apply_state, read_state


def test_legacy_migration_keeps_neighbors():
    text = "# Repo\n\nintro\n\n## Changelog\n\n- old rule\n\n## Next\n\ntail\n"
    out = apply_state(text, "off")
    assert out is not None
    assert "- old rule" not in out
    assert BEGIN in out and END in out
    assert out.startswith("# Repo\n\nintro\n\n")
    assert out.endswith("## Next\n\ntail\n")
    assert read_state(out) == "off"


def test_legacy_at_eof_and_level_one_heading():
    text = "# AGENTS.md\n\n# 변경 기록 (changelog)\n\n- old\n"
    out = apply_state(text, "off")
    assert out is not None and out.endswith(END + "\n"), out
    assert read_state(out) == "off"


def test_toggle_is_idempotent_and_reversible():
    off = apply_state("## Changelog\n\n- old\n", "off")
    again = apply_state(off, "off")
    assert again == off
    on = apply_state(off, "on")
    assert read_state(on) == "on"
    assert read_state(apply_state(on, "off")) == "off"


def test_fragment_format_gets_its_own_on_text():
    off = apply_state("## Changelog\n\n- old\n", "off", "changelog.d")
    on = apply_state(off, "on", "changelog.d")
    assert "changelog.d/<YYYY-MM-DD>-<issue>.md" in on
    assert read_state(on, "changelog.d") == "on"
    # 포맷이 다르면 그 repo 기준으로는 정규 본문이 아니다 → custom
    assert read_state(on, "changelog.md") == "custom"


def test_no_section():
    assert apply_state("# Repo\n\nnothing here\n", "off") is None
    assert read_state("# Repo\n") == "none"


if __name__ == "__main__":
    test_legacy_migration_keeps_neighbors()
    test_legacy_at_eof_and_level_one_heading()
    test_toggle_is_idempotent_and_reversible()
    test_fragment_format_gets_its_own_on_text()
    test_no_section()
    print("OK")
