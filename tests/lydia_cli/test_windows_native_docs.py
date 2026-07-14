from pathlib import Path


def test_windows_native_install_path_docs_match_installer() -> None:
    doc = Path("website/docs/user-guide/windows-native.md").read_text()
    install = Path("scripts/install.ps1").read_text()

    assert "%LOCALAPPDATA%\\lydia\\lydia-agent\\venv\\Scripts" in doc
    assert "Get-Command lydia        # should print C:\\Users\\<you>\\AppData\\Local\\lydia\\lydia-agent\\venv\\Scripts\\lydia.exe" in doc
    assert '$lydiaBin = "$InstallDir\\venv\\Scripts"' in install
