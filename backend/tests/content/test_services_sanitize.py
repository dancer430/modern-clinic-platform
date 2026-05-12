from __future__ import annotations

from content.services import sanitize_html


def test_strips_script_tags():
    out = sanitize_html("<p>hi</p><script>alert(1)</script>")
    assert "<script>" not in out
    assert "alert(1)" not in out
    assert "<p>hi</p>" in out


def test_strips_event_handlers():
    out = sanitize_html('<a href="https://x" onclick="bad()">link</a>')
    assert "onclick" not in out
    assert 'href="https://x"' in out


def test_strips_inline_styles():
    out = sanitize_html('<p style="color:red">x</p>')
    assert "style" not in out


def test_keeps_allowed_tags():
    src = (
        "<h1>T</h1><h2>S</h2><h3>U</h3>"
        "<p><strong>b</strong><em>i</em><u>u</u></p>"
        "<ul><li>a</li></ul><ol><li>1</li></ol>"
        "<blockquote>q</blockquote><br>"
    )
    out = sanitize_html(src)
    for tag in (
        "<h1>",
        "<h2>",
        "<h3>",
        "<strong>",
        "<em>",
        "<u>",
        "<ul>",
        "<ol>",
        "<li>",
        "<blockquote>",
        "<br",
    ):
        assert tag in out


def test_blocks_external_image_sources():
    out = sanitize_html(
        '<p>x</p><img src="https://evil.example.com/x.png">',
        allowed_image_prefix="http://localhost:9000/",
    )
    assert "<img" not in out


def test_keeps_platform_image_sources():
    out = sanitize_html(
        '<img src="http://localhost:9000/clinic-media/media/inline/a.png" alt="a">',
        allowed_image_prefix="http://localhost:9000/",
    )
    assert "<img" in out
    assert 'src="http://localhost:9000/clinic-media/media/inline/a.png"' in out


def test_keeps_relative_media_paths():
    out = sanitize_html(
        '<img src="/media/inline/a.png">',
        allowed_image_prefix="http://localhost:9000/",
    )
    assert "<img" in out


def test_blocks_external_images_without_configured_prefix():
    """When no allowed_image_prefix is supplied, external images must still be blocked."""
    out = sanitize_html('<img src="https://evil.com/x.png">', allowed_image_prefix="")
    assert "<img" not in out
