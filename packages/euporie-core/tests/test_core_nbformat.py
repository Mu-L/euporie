"""Test module for euporie.core.nbformat."""

from __future__ import annotations

import io
from unittest.mock import Mock, patch

import pytest

from euporie.core.nbformat import (
    NotebookNode,
    _rejoin_lines,
    _rejoin_mimebundle,
    _strip_transient,
    new_code_cell,
    new_notebook,
    output_from_msg,
    read,
)


def test_notebook_node_attribute_access() -> None:
    """Items are accessible as attributes."""
    node = NotebookNode()
    node.foo = 1
    assert node.foo == 1
    assert node["foo"] == 1


def test_notebook_node_missing_attribute_raises() -> None:
    """Accessing a missing attribute raises AttributeError."""
    node = NotebookNode()
    with pytest.raises(AttributeError):
        _ = node.missing


def test_notebook_node_nested_dict_coerced() -> None:
    """Nested dicts are coerced to NotebookNodes."""
    node = NotebookNode()
    node["child"] = {"a": 1}
    assert isinstance(node.child, NotebookNode)
    assert node.child.a == 1


def test_notebook_node_update_mapping() -> None:
    """Update accepts a mapping."""
    node = NotebookNode()
    node.update({"a": 1, "b": 2})
    assert node == {"a": 1, "b": 2}


def test_notebook_node_update_iterable() -> None:
    """Update accepts an iterable of pairs."""
    node = NotebookNode()
    node.update([("a", 1), ("b", 2)])
    assert node == {"a": 1, "b": 2}


def test_notebook_node_update_kwargs() -> None:
    """Update accepts keyword arguments."""
    node = NotebookNode()
    node.update(a=1, b=2)
    assert node == {"a": 1, "b": 2}


def test_notebook_node_update_too_many_args() -> None:
    """Update raises when given more than one positional argument."""
    node = NotebookNode()
    with pytest.raises(TypeError):
        node.update({}, {})


def test_notebook_node_from_dict_recursive() -> None:
    """_from_dict recurses through dicts and lists."""
    result = NotebookNode._from_dict({"a": [{"b": 1}], "c": 2})
    assert isinstance(result, NotebookNode)
    assert isinstance(result.a[0], NotebookNode)
    assert result.a[0].b == 1
    assert result.c == 2


def test_new_notebook_defaults() -> None:
    """A new notebook has the expected default structure."""
    nb = new_notebook()
    assert nb.nbformat == 4
    assert nb.nbformat_minor == 5
    assert nb.cells == []
    assert isinstance(nb.metadata, NotebookNode)


def test_new_notebook_kwargs_override() -> None:
    """Keyword arguments override the notebook defaults."""
    nb = new_notebook(metadata={"kernelspec": {"name": "python3"}})
    assert nb.metadata.kernelspec.name == "python3"


def test_new_code_cell_defaults() -> None:
    """A new code cell has the expected default structure."""
    cell = new_code_cell()
    assert cell.cell_type == "code"
    assert cell.source == ""
    assert cell.outputs == []
    assert cell.execution_count is None
    assert len(cell.id) == 8


def test_new_code_cell_with_source() -> None:
    """A code cell keeps its provided source and extra kwargs."""
    cell = new_code_cell("print(1)", execution_count=3)
    assert cell.source == "print(1)"
    assert cell.execution_count == 3


def test_rejoin_mimebundle_joins_text() -> None:
    """Multi-line text values are joined into a string."""
    data = {"text/plain": ["a", "b", "c"]}
    assert _rejoin_mimebundle(data) == {"text/plain": "abc"}


def test_rejoin_mimebundle_leaves_json() -> None:
    """JSON mime types are left untouched."""
    data = {"application/json": [1, 2], "application/vnd.x+json": [3, 4]}
    result = _rejoin_mimebundle(data)
    assert result["application/json"] == [1, 2]
    assert result["application/vnd.x+json"] == [3, 4]


def test_rejoin_lines() -> None:
    """Cell source and output text lists are joined."""
    nb = NotebookNode._from_dict(
        {
            "cells": [
                {
                    "cell_type": "code",
                    "source": ["line1\n", "line2"],
                    "outputs": [
                        {"output_type": "stream", "text": ["out1\n", "out2"]},
                        {
                            "output_type": "execute_result",
                            "data": {"text/plain": ["a", "b"]},
                        },
                    ],
                }
            ]
        }
    )
    _rejoin_lines(nb)
    cell = nb.cells[0]
    assert cell.source == "line1\nline2"
    assert cell.outputs[0].text == "out1\nout2"
    assert cell.outputs[1].data["text/plain"] == "ab"


def test_strip_transient() -> None:
    """Transient metadata and trusted flags are removed."""
    nb = NotebookNode._from_dict(
        {
            "metadata": {
                "orig_nbformat": 4,
                "orig_nbformat_minor": 2,
                "signature": "abc",
                "keep": 1,
            },
            "cells": [{"metadata": {"trusted": True, "keep": 2}}],
        }
    )
    _strip_transient(nb)
    assert "orig_nbformat" not in nb.metadata
    assert "orig_nbformat_minor" not in nb.metadata
    assert "signature" not in nb.metadata
    assert nb.metadata.keep == 1
    assert "trusted" not in nb.cells[0].metadata
    assert nb.cells[0].metadata.keep == 2


def test_read_v4_json() -> None:
    """A v4 JSON notebook is read via the fast path."""
    fp = io.StringIO(
        '{"nbformat": 4, "nbformat_minor": 5, "metadata": {}, '
        '"cells": [{"cell_type": "code", "source": ["a\\n", "b"], '
        '"metadata": {}, "outputs": []}]}'
    )
    nb = read(fp, as_version=4)
    assert isinstance(nb, NotebookNode)
    assert nb.nbformat == 4
    assert nb.cells[0].source == "a\nb"


def test_read_non_v4_falls_back() -> None:
    """A non-v4 notebook falls back to an external reader."""
    fp = io.StringIO('{"nbformat": 3, "cells": []}')
    fake_reader = Mock(return_value=NotebookNode(nbformat=3))
    with patch.dict("sys.modules", {"jupytext": Mock(read=fake_reader)}):
        result = read(fp, as_version=4)
    fake_reader.assert_called_once()
    assert result.nbformat == 3


def test_output_from_msg_rewrites_update_display() -> None:
    """update_display_data messages are rewritten to display_data."""
    captured = {}

    def fake_output_from_msg(msg: dict) -> NotebookNode:
        captured["msg"] = msg
        return NotebookNode(output_type="display_data")

    msg = {
        "header": {"msg_type": "update_display_data"},
        "content": {"transient": {"display_id": "xyz"}},
    }
    with patch.dict(
        "sys.modules",
        {"nbformat.v4": Mock(output_from_msg=fake_output_from_msg)},
    ):
        output = output_from_msg(msg)
    assert captured["msg"]["header"]["msg_type"] == "display_data"
    assert output.transient["display_id"] == "xyz"
