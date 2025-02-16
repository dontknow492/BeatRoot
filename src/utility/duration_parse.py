def duration_to_seconds(duration: str) -> int:
        """
        Converts a duration string in MM:SS or HH:MM:SS format to total seconds.
        """
        parts = list(map(int, duration.split(':')))
        if len(parts) == 2:  # MM:SS
            minutes, seconds = parts
            return minutes * 60 + seconds
        elif len(parts) == 3:  # HH:MM:SS
            hours, minutes, seconds = parts
            return hours * 3600 + minutes * 60 + seconds
        return 0  # Default to 0 if format is invalid
    
    

def seconds_to_duration(seconds: int) -> str:
    """
    Converts seconds to a duration string in HH:MM:SS or MM:SS format.
    If the total duration is less than 1 hour, it uses MM:SS format.
    Otherwise, it uses HH:MM:SS format.
    """
    if seconds < 3600:  # Less than an hour
        return f"{seconds // 60:02d}:{seconds % 60:02d}"
    else:  # One hour or more
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
def milliseconds_to_duration(milliseconds: int) -> str:
    """
    Converts milliseconds to a duration string in HH:MM:SS or MM:SS format.
    If the total duration is less than 1 hour, it uses MM:SS format.
    Otherwise, it uses HH:MM:SS format.
    """
    seconds = milliseconds // 1000
    return seconds_to_duration(seconds)

def duration_to_milliseconds(duration: str) -> int:
    """
    Converts a duration string in HH:MM:SS or MM:SS format to total milliseconds.
    """
    return duration_to_seconds(duration) * 1000

def get_duration_percent(current, total)-> float:
    if isinstance(current, str):
        current = duration_to_seconds(current)
    if isinstance(total, str):
        total = duration_to_seconds(total)
    return (current / total) * 100


def get_percent_duration(percentage: float, total)-> str:
    if isinstance(total, str):
        total = duration_to_seconds(total)
    return seconds_to_duration(int((percentage / 100) * total))

def get_seconds_percentage(sec: int, total)-> float:
    if isinstance(total, str):
        total = duration_to_seconds(total)
    return (sec / total) * 100
    
    

if(__name__ == "__main__"):
    print(duration_to_seconds("03:00"))
    print(duration_to_seconds("00:03:00"))
    print(seconds_to_duration(313))
    print(get_duration_percent("01:00", "10:03:00"))
    print(get_percent_duration(1.0, "10:03:00"))