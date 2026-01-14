from unittest.mock import MagicMock, patch

import pytest

from transcriptor.main import main


@patch("transcriptor.main.cli_main")
@patch("transcriptor.main.tui_main")
@patch("transcriptor.main.argparse.ArgumentParser.parse_args")
def test_main_cli_default(mock_parse_args, mock_tui_main, mock_cli_main):
    # Case 1: No arguments provided -> run CLI (default)
    mock_args = MagicMock()
    mock_args.command = None
    del mock_args.func  # Ensure func attribute is missing
    mock_parse_args.return_value = mock_args

    main()
    mock_cli_main.assert_called_once()
    mock_tui_main.assert_not_called()


@patch("transcriptor.main.cli_main")
@patch("transcriptor.main.tui_main")
@patch("transcriptor.main.argparse.ArgumentParser.parse_args")
def test_main_cli_explicit(mock_parse_args, mock_tui_main, mock_cli_main):
    # Case 2: 'cli' command provided -> run CLI
    mock_args = MagicMock()
    mock_args.command = "cli"
    mock_args.func = mock_cli_main  # argparse sets the default func
    mock_args.cli_args = ["some", "args"]
    mock_parse_args.return_value = mock_args

    main()
    mock_cli_main.assert_called_with(argv=["some", "args"])
    mock_tui_main.assert_not_called()


@patch("transcriptor.main.cli_main")
@patch("transcriptor.main.tui_main")
@patch("transcriptor.main.argparse.ArgumentParser.parse_args")
def test_main_tui(mock_parse_args, mock_tui_main, mock_cli_main):
    # Case 3: 'tui' command provided -> run TUI
    mock_args = MagicMock()
    mock_args.command = "tui"
    mock_args.func = mock_tui_main
    mock_parse_args.return_value = mock_args

    main()
    mock_tui_main.assert_called_once()
    mock_cli_main.assert_not_called()


@patch("transcriptor.main.exit")
@patch("transcriptor.main.argparse.ArgumentParser")
def test_main_invalid_command(mock_argparser, mock_exit):
    # Case 4: Invalid command handling (usually handled by argparse itself,
    # but the else block handles cases where func is missing and command is not None)

    # Mock parse_args return value
    mock_args = MagicMock()
    mock_args.command = "invalid"
    # Ensure 'func' is NOT present
    del mock_args.func

    mock_parser_instance = mock_argparser.return_value
    mock_parser_instance.parse_args.return_value = mock_args

    main()

    mock_parser_instance.print_help.assert_called_once()
    mock_exit.assert_called_once_with(1)
