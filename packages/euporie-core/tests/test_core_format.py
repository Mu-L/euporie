"""Test module for euporie.core.format."""

from __future__ import annotations

from unittest.mock import Mock, patch

from euporie.core.format import CliFormatter, Formatter, LspFormatter


class _EchoFormatter(Formatter):
    """A concrete formatter that appends a marker."""

    def format(self, text: str) -> str:
        """Return the text with a marker appended."""
        return f"{text}!"


def test_formatter_no_languages_formats_all() -> None:
    """With no languages set, any language is formatted."""
    formatter = _EchoFormatter()
    assert formatter._format("x", "python") == "x!"
    assert formatter._format("x", "rust") == "x!"


def test_formatter_matching_language() -> None:
    """A matching language is formatted."""
    formatter = _EchoFormatter(languages={"python"})
    assert formatter._format("x", "python") == "x!"


def test_formatter_non_matching_language_passthrough() -> None:
    """A non-matching language is returned unchanged."""
    formatter = _EchoFormatter(languages={"python"})
    assert formatter._format("x", "rust") == "x"


def test_cli_formatter_repr() -> None:
    """The CLI formatter repr uses the command name."""
    formatter = CliFormatter(["black", "-"])
    assert repr(formatter) == "BlackFormatter()"


def test_cli_formatter_skips_when_command_missing() -> None:
    """A missing command results in the text being passed through."""
    formatter = CliFormatter(["definitely-not-a-real-command", "-"])
    assert formatter._format("code", "python") == "code"


def test_cli_formatter_format_returns_output() -> None:
    """Successful command output is returned with trailing newlines stripped."""
    formatter = CliFormatter(["fmt"])
    proc = Mock()
    proc.communicate.return_value = ("formatted\n", "")
    with patch("subprocess.Popen", return_value=proc):
        assert formatter.format("unformatted") == "formatted"


def test_cli_formatter_format_returns_input_on_error_output() -> None:
    """When the command emits an error, the input is returned unchanged."""
    formatter = CliFormatter(["fmt"])
    proc = Mock()
    proc.communicate.return_value = ("", "boom")
    with patch("subprocess.Popen", return_value=proc):
        assert formatter.format("unformatted") == "unformatted"


def test_cli_formatter_format_handles_popen_failure() -> None:
    """A failure to spawn the process returns the input unchanged."""
    formatter = CliFormatter(["fmt"])
    with patch("subprocess.Popen", side_effect=OSError):
        assert formatter.format("unformatted") == "unformatted"


def test_lsp_formatter_repr() -> None:
    """The LSP formatter repr uses the client name."""
    lsp = Mock()
    lsp.name = "python-lsp-server"
    formatter = LspFormatter(lsp, Mock())
    assert repr(formatter) == "PythonlspserverLspFormatter()"


def test_lsp_formatter_applies_changes() -> None:
    """The LSP formatter applies text edits returned by the client."""
    lsp = Mock()
    lsp.format.return_value = [
        {
            "newText": "formatted",
            "range": {
                "start": {"line": 0, "character": 0},
                "end": {"line": 0, "character": 11},
            },
        }
    ]
    formatter = LspFormatter(lsp, Mock())
    assert formatter.format("unformatted") == "formatted"


def test_lsp_formatter_handles_exception() -> None:
    """An exception during formatting returns the input unchanged."""
    lsp = Mock()
    lsp.format.side_effect = RuntimeError
    formatter = LspFormatter(lsp, Mock())
    assert formatter.format("unformatted") == "unformatted"


def test_lsp_formatter_no_changes() -> None:
    """When no changes are returned the text is only stripped."""
    lsp = Mock()
    lsp.format.return_value = []
    formatter = LspFormatter(lsp, Mock())
    assert formatter.format("code\n") == "code"
