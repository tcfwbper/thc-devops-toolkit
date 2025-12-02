from thc_devops_toolkit.documentation.highlight import highlight, unhighlight


def test_highlight_normal_text():
    text = "Hello World"
    result = highlight(text)
    assert result.startswith('<span style="color:red">**')
    assert result.endswith("**</span>")
    assert "Hello World" in result


def test_highlight_already_highlighted():
    text = '<span style="color:red">**Already Highlighted**</span>'
    result = highlight(text)
    assert result == text
    assert result.count('<span style="color:red">**') == 1


def test_unhighlight_highlighted_text():
    text = '<span style="color:red">**Hello World**</span>'
    result = unhighlight(text)
    assert result == "Hello World"
    assert '<span style="color:red">**' not in result
    assert "**</span>" not in result


def test_unhighlight_normal_text():
    text = "Hello World"
    result = unhighlight(text)
    assert result == "Hello World"


def test_highlight_empty_string():
    text = ""
    result = highlight(text)
    assert result == '<span style="color:red">****</span>'


def test_unhighlight_empty_string():
    text = ""
    result = unhighlight(text)
    assert result == ""


def test_highlight_unhighlight_roundtrip():
    original = "Test Text"
    highlighted = highlight(original)
    unhighlighted = unhighlight(highlighted)
    assert unhighlighted == original
