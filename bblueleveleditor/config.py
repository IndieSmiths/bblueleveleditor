
### standard library import
from pathlib import Path



_HERE = Path(__file__).parent

_DATA_DIR = _HERE / 'data'

FONTS_DIR = _DATA_DIR / 'fonts'

_ASSETS_DIR = _DATA_DIR / 'assets'
COLORKEY_ASSETS_DIR = _ASSETS_DIR / 'colorkey'
NO_COLORKEY_ASSETS_DIR = _ASSETS_DIR / 'no_colorkey'

LEVELS_DIR = _HERE / 'levels'


if not LEVELS_DIR.exists():
    LEVELS_DIR.mkdir()

elif LEVELS_DIR.is_file():
    raise RuntimeError("{LEVELS_DIR} must either be a folder or not exist.")
