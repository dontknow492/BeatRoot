import socket

def is_connected_to_internet(host="8.8.8.8", port=53, timeout=3):
    """
    Checks if the device is connected to the internet by attempting to connect
    to a public DNS server.

    Args:
        host (str): The host to connect to (default is Google's public DNS server).
        port (int): The port to use for the connection (default is 53 for DNS).
        timeout (int): The timeout in seconds for the connection attempt.

    Returns:
        bool: True if connected to the internet, False otherwise.
    """
    try:
        # Attempt to create a socket connection
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except OSError:
        return False
    
if(__name__ == "__main__"):
    print(is_connected_to_internet())