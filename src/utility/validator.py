from pathlib import Path
import re

def validate_path(path, type_: str = 'file'):
    # Convert the path to a Path object
    if isinstance(path, str):
        path_obj = Path(path)
    elif isinstance(path, Path):
        path_obj = path
    else:
        print("Invalid path type. Please use a string or Path object.")
        return False
    type_ = type_.lower()
    
    if type_.lower() == 'file':
        if path_obj.is_file():
            return True
        else:
            return False
    elif type_.lower() == 'folder':
        if path_obj.is_dir():
            return True
        else:
            return False
    else:
        print("Invalid type. Please use 'file' or 'folder'.")
        return False


def is_youtube_thumbnail_url(url):
    pattern = r'^https:\/\/i\.ytimg\.com\/vi\/[A-Za-z0-9_-]{11}\/maxresdefault\.jpg$'
    return bool(re.match(pattern, url))

# Example usage:
if(__name__ == "__main__"):
    path = r"D:\Program\Musify\src\ui\statsCard.py"
    type_ = 'file'

    result = validate_path(path, type_)
    print(result)
