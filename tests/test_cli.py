"""
Unit tests for CLI commands dispatching and main entry point.
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
from main import main


@patch("sys.argv", ["main.py", "stats"])
@patch("cli.commands.db_healthcheck")
@patch("cli.commands.get_db")
def test_cli_stats_command(mock_get_db, mock_healthcheck):
    mock_healthcheck.return_value = True
    mock_db = MagicMock()
    mock_col = MagicMock()
    mock_col.count_documents.return_value = 42
    mock_db.__getitem__.return_value = mock_col
    mock_get_db.return_value = mock_db

    with patch("rich.console.Console.print"):
        main()

    assert mock_healthcheck.called


@patch("sys.argv", ["main.py", "reset"])
@patch("cli.commands.db_healthcheck")
@patch("cli.commands.get_db")
@patch("cli.commands.create_all_indexes")
def test_cli_reset_command(mock_indexes, mock_get_db, mock_healthcheck):
    mock_healthcheck.return_value = True
    mock_db = MagicMock()
    mock_col = MagicMock()
    mock_db.__getitem__.return_value = mock_col
    mock_get_db.return_value = mock_db

    with patch("rich.console.Console.print"):
        main()

    assert mock_indexes.called
