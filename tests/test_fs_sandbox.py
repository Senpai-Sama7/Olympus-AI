import os
import pytest


def _set_root(tmpdir):
    os.environ["OLYMPUS_SANDBOX_ROOT"] = str(tmpdir)
    # Lazy import after setting env
    from packages.tools.olympus_tools import fs

    return fs


def test_path_escape_rejected(tmp_path):
    fs = _set_root(tmp_path)
    with pytest.raises(fs.PathError):
        fs.write_file(
            "../outside.txt", "nope", overwrite=True, token=fs.ConsentToken("t", ["*"])
        )


def test_symlink_rejected(tmp_path):
    fs = _set_root(tmp_path)
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    # Create a symlink within sandbox pointing outside
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported on this platform")
    with pytest.raises(fs.PathError):
        fs.read_file("link.txt", token=fs.ConsentToken("t", ["*"]))
