# nodes/utils/fonts.py

import sys
import os
import subprocess
from pathlib import Path
from PIL import ImageFont

# Optional: try to import bidi support
try:
    from bidi.algorithm import get_display

    BIDI_AVAILABLE = True
except ImportError:
    BIDI_AVAILABLE = False


def get_system_font_names():
    """Get list of available system fonts."""
    fonts = set()

    try:
        if sys.platform == "win32":
            font_dirs = [
                Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts",
                Path.home() / "AppData/Local/Microsoft/Windows/Fonts",
            ]
            for font_dir in font_dirs:
                if font_dir.exists():
                    for ext in ["*.ttf", "*.otf", "*.TTF", "*.OTF"]:
                        fonts.update(font_dir.rglob(ext))
        else:
            try:
                result = subprocess.run(
                    ["fc-list", "--format=%{file}\\n"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        line = line.strip()
                        if line and Path(line).exists():
                            fonts.add(line)
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                pass

            if not fonts:
                font_dirs = []
                if sys.platform == "darwin":
                    font_dirs = [
                        Path("/System/Library/Fonts"),
                        Path("/Library/Fonts"),
                        Path.home() / "Library/Fonts",
                    ]
                else:
                    font_dirs = [
                        Path("/usr/share/fonts"),
                        Path("/usr/local/share/fonts"),
                        Path.home() / ".fonts",
                        Path.home() / ".local/share/fonts",
                    ]

                for font_dir in font_dirs:
                    if font_dir.exists():
                        for ext in ["*.ttf", "*.otf", "*.TTF", "*.OTF"]:
                            fonts.update(font_dir.rglob(ext))

    except Exception as e:
        print(f"⚠️ Font detection error: {e}")

    working_fonts = set()
    test_text = "A"

    for font_path in fonts:
        path = Path(font_path)
        if path.exists() and path.suffix.lower() in ['.ttf', '.otf']:
            try:
                font = ImageFont.truetype(str(path), 12)
                bbox = font.getbbox(test_text)
                if bbox[2] > bbox[0]:
                    name = path.stem.replace('-', ' ').replace('_', ' ')
                    working_fonts.add(name)
            except Exception:
                pass

    fallbacks = {"Arial", "DejaVuSans", "LiberationSans", "NotoSans"}
    working_fonts.update(fallbacks)

    return sorted(working_fonts) if working_fonts else ["Arial", "DejaVuSans"]


def find_font_path(font_name):
    """Find the file path for a given font name."""
    font_path = None

    try:
        if sys.platform == "win32":
            base_dirs = [Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts"]
        else:
            try:
                result = subprocess.run(
                    ["fc-list", f":family={font_name}", "--format=%{file}\\n"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    font_path = result.stdout.strip().split('\n')[0]
            except:
                pass

        if not font_path:
            search_dirs = []
            if sys.platform == "win32":
                search_dirs = [Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts"]
            elif sys.platform == "darwin":
                search_dirs = [
                    Path("/System/Library/Fonts"),
                    Path("/Library/Fonts"),
                    Path.home() / "Library/Fonts",
                ]
            else:
                search_dirs = [
                    Path("/usr/share/fonts"),
                    Path("/usr/local/share/fonts"),
                    Path.home() / ".fonts",
                    Path.home() / ".local/share/fonts",
                ]

            for search_dir in search_dirs:
                if search_dir.exists():
                    candidates = [
                        search_dir / f"{font_name}.ttf",
                        search_dir / f"{font_name}.otf",
                        search_dir / f"{font_name.replace(' ', '')}.ttf",
                        search_dir / f"{font_name.replace(' ', '')}.otf",
                    ]
                    for candidate in candidates:
                        if candidate.exists():
                            font_path = str(candidate)
                            break
                    if font_path:
                        break

    except Exception as e:
        print(f"Font search error: {e}")

    return font_path


def load_font(font_name, font_size):
    """Load a font by name with automatic fallback."""
    font = None
    font_path = find_font_path(font_name)

    if font_path and Path(font_path).exists():
        try:
            font = ImageFont.truetype(font_path, font_size)
            return font
        except Exception as e:
            print(f"Failed to load font {font_path}: {e}")

    fallback_fonts = [
        "DejaVuSans.ttf",
        "Arial.ttf",
        "LiberationSans-Regular.ttf",
        "NotoSans-Regular.ttf"
    ]

    for fallback in fallback_fonts:
        try:
            font = ImageFont.truetype(fallback, font_size)
            return font
        except:
            continue

    return ImageFont.load_default()