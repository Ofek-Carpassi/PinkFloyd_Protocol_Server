"""
PINKFLOYD protocol server implementation
-=+=-=+=-=+=-=+=-=+=-=+=-=+=-=+=-=+=-=+=-
The PINKFLOYD protocol is a simple textual protocol.
The server will listen on a port for incoming connections.
The client will connect to the server and send a message.
The server will respond with a message based on the message type.
The server will close the connection if the client sends a message with type 0.

The PINKFLOYD protocol message format is as follows:
TYPE:<3-bit binary number>|DATA:<message data>
"""

import re  # Added for regular expressions
import select  # Used to monitor multiple sockets
import socket  # Used to create sockets
import errno  # Used to handle socket errors

# Constants
BUFFER_SIZE = 1024
TYPE_INDEX_START = 5
TYPE_INDEX_END = 8
DATA_INDEX_START = 14
EXIT_TYPE = 0
ALBUMS_LIST_TYPE = 1
SONGS_IN_ALBUM_TYPE = 2
LENGTH_OF_SONG_TYPE = 3
LYRICS_OF_SONG_TYPE = 4
ALBUM_OF_SONG_TYPE = 5
SONGS_WITH_WORD_IN_TITLE_TYPE = 6
SONGS_WITH_WORD_IN_LYRICS_TYPE = 7
INVALID_OPTION_ERROR = "Invalid option"
SONG_NOT_FOUND_ERROR = "Song not found"
NO_SONGS_FOUND_ERROR = "No songs found"
NO_ALBUMS_FOUND_ERROR = "No albums found"
DB_FILE = "Pink_Floyd_DB.txt"

# Data dictionary to store the information from the database file
data_dict = {
    # The keys in this dictionary are the different types of data that the server has.
    "albumsList": [],
    "songsInAlbum": {},
    "lengthOfSong": {},
    "lyricsOfSong": {},
    "albumOfSong": {},
    "songsWithWordInTitle": {},
    "songsWithWordInLyrics": {}
}

def main():
    # Initialize the data dictionary
    initialize_data_dict()

    # Set up the server socket
    listening_socket = setup_server_socket(1965)

    # Print the port the server is listening on
    print("Server is listening on port", listening_socket.getsockname()[1])
    
    # List of sockets to monitor for incoming data
    inputs = [listening_socket]

    while True:
        # Wait for a socket to be ready for reading or to raise an exception
        readable, _, exceptional = select.select(inputs, [], inputs)

        # Handle the sockets that are ready for reading
        for s in readable:
            # If the socket is the listening socket, accept a new connection
            if s is listening_socket:
                handle_new_connection(s, inputs)
            # If the socket is a client socket, handle the data
            else:
                handle_client_data(s, inputs)

        # Handle sockets that have raised an exception
        for s in exceptional:
            handle_socket_exception(s, inputs)

# Initialize the data dictionary
def initialize_data_dict():
    # Initialize the data dictionary with the data from the database file
    data_dict["albumsList"] = getAlbumsList()

    # Populate the data dictionary with additional information
    for album in data_dict["albumsList"]:
        # Initialize the songsInAlbum dictionary with an empty list for each album
        data_dict["songsInAlbum"][album] = getSongsInAlbum(album)

        # Populate the lengthOfSong, lyricsOfSong, and albumOfSong dictionaries
        for song in data_dict["songsInAlbum"][album]:
            # Add the length of the song to the lengthOfSong dictionary
            data_dict["lengthOfSong"][song] = getLengthOfSong(song)
            # Add the lyrics of the song to the lyricsOfSong dictionary
            data_dict["lyricsOfSong"][song] = getLyricsOfSong(song)
            # Add the album of the song to the albumOfSong dictionary
            data_dict["albumOfSong"][song] = getAlbumOfSong(song)

            # Populate the songsWithWordInTitle and songsWithWordInLyrics dictionaries
            for word in song.split():
                # If the word is not already in the dictionary, create a new list for it
                if word.lower() not in data_dict["songsWithWordInTitle"]:
                    data_dict["songsWithWordInTitle"][word.lower()] = []
                # Add the song to the list of songs with the word in the title
                data_dict["songsWithWordInTitle"][word.lower()].append(song)

            # Populate the songsWithWordInLyrics dictionary
            lyrics = '\n'.join(data_dict["lyricsOfSong"][song])

            # Use regular expressions to extract words from the lyrics
            word_list = re.findall(r'\w+', lyrics.lower())  

            # Add the song to the list of songs with each word in the lyrics
            for word in set(word_list):  
                if word not in data_dict["songsWithWordInLyrics"]:
                    data_dict["songsWithWordInLyrics"][word] = []
                data_dict["songsWithWordInLyrics"][word].append(song)

# Set up the server socket
def setup_server_socket(port):
    # Create a new socket
    listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Set the socket options to allow the port to be reused immediately after the socket is closed
    while True:
        try:
            # Bind the socket to the specified port and start listening for incoming connections
            listening_socket.bind(('', port))
            listening_socket.listen(1)
            return listening_socket
        # Handle the case where the port is already in use
        except socket.error as e:
            # Try the next port
            if e.errno == errno.EADDRINUSE:
                print(f"Port {port} is already in use.")
                port += 1
                print(f"Trying to bind to port {port} instead.")
            else:
                raise

# Handle a new connection
def handle_new_connection(listening_socket, inputs):
    # Accept the new connection
    client_socket, client_address = listening_socket.accept()
    print("Connection from", client_address)
    # Add the new client socket to the list of inputs to monitor
    inputs.append(client_socket)

def handle_client_data(client_socket, inputs):
    # Receive the data from the client
    try:
        data = client_socket.recv(BUFFER_SIZE).decode()
    except ConnectionResetError:
        # Handle the case where the client closes the connection unexpectedly
        close_connection(client_socket, inputs)
        return

    # Handle the case where the client closes the connection
    if not data:
        close_connection(client_socket, inputs)
        return

    print("Received data:", data)

    try:
        # Break the data into the message type and message data
        type, message_data = break_data(data)
    except ValueError:
        # Handle the case where the message format is invalid
        print("Invalid message received. Closing connection.")
        close_connection(client_socket, inputs)
        return

    # Handle the message based on the message type
    response = handle_type(type, message_data)
    try:
        # Send the response to the client
        client_socket.send(response.encode())
        print("Sent data:", response)
    except ConnectionResetError:
        # Handle the case where the client closes the connection unexpectedly
        close_connection(client_socket, inputs)
        return

    # Close the connection if the client requests it
    if type == EXIT_TYPE:
        close_connection(client_socket, inputs)

def handle_socket_exception(sock, inputs):
    print("Socket exception")
    inputs.remove(sock)
    sock.close()

def close_connection(sock, inputs):
    print("Connection closed by the client")
    inputs.remove(sock)
    sock.close()

def break_data(data):
    try:
        # Extract the message type and message data from the data
        type = int(data[TYPE_INDEX_START:TYPE_INDEX_END], 2)
        data = data[DATA_INDEX_START:]
        return type, data
    except ValueError:
        raise ValueError("Invalid message format.")

def handle_type(type, data):
    # Handle the message based on the message type
    if type == EXIT_TYPE:
        return "EXIT"
    elif type == ALBUMS_LIST_TYPE:
        return ", ".join(data_dict["albumsList"])
    elif type == SONGS_IN_ALBUM_TYPE:
        return ", ".join(data_dict["songsInAlbum"].get(data, [SONG_NOT_FOUND_ERROR]))
    elif type == LENGTH_OF_SONG_TYPE:
        return data_dict["lengthOfSong"].get(data, SONG_NOT_FOUND_ERROR)
    elif type == LYRICS_OF_SONG_TYPE:
        return "\n".join(data_dict["lyricsOfSong"].get(data, [SONG_NOT_FOUND_ERROR]))
    elif type == ALBUM_OF_SONG_TYPE:
        return data_dict["albumOfSong"].get(data, SONG_NOT_FOUND_ERROR)
    elif type == SONGS_WITH_WORD_IN_TITLE_TYPE:
        return ", ".join(data_dict["songsWithWordInTitle"].get(data.lower(), [NO_SONGS_FOUND_ERROR]))
    elif type == SONGS_WITH_WORD_IN_LYRICS_TYPE:
        return ", ".join(data_dict["songsWithWordInLyrics"].get(data.lower(), [NO_SONGS_FOUND_ERROR]))
    else:
        return INVALID_OPTION_ERROR

def getAlbumsList():
    albums = []
    with open(DB_FILE, "r") as f:
        for line in f:
            # Check if the line starts with a "#" to indicate an album
            if line.startswith("#"):
                # Extract the album name from the line and add it to the list of albums
                albums.append(line[1:].split("::")[0].strip())

    # If there was an error parsing the file, return an error message - not supposed to ever happen - only if the file is corrupted
    if not albums:
        return NO_ALBUMS_FOUND_ERROR
    return albums

def getSongsInAlbum(album):
    songs = []
    with open(DB_FILE, "r") as f:
        in_target_album = False
        for line in f:
            # Check if the line starts with a "#" to indicate an album
            if line.startswith("#"):
                # Check if the album name matches the target album
                in_target_album = line[1:].split("::")[0].strip() == album
            # Check if the line starts with a "*" to indicate a song
            elif in_target_album and line.startswith("*"):
                # Extract the song name from the line and add it to the list of songs
                song_name = line[1:].split("::")[0].strip()
                # add the song to the list of songs if it is not empty
                if song_name:
                    songs.append(song_name)
    if songs:
        return songs
    return SONG_NOT_FOUND_ERROR

def getLengthOfSong(song):
    with open(DB_FILE, "r") as f:
        for line in f:
            # Check if the line starts with a "*" to indicate a song
            if line.startswith("*"):
                # Check if the song name matches the target song
                if line[1:].split("::")[0] == song:
                    # Extract the length of the song from the line
                    return line[1:].split("::")[2].strip()
    return SONG_NOT_FOUND_ERROR

def getLyricsOfSong(song):
    lyrics = []
    with open(DB_FILE, "r") as f:
        for line in f:
            # Check if the line starts with a "*" to indicate a song
            if line.startswith("*"):
                # Check if the song name matches the target song
                if line[1:].split("::")[0] == song:
                    # Extract the lyrics of the song from the file
                    lyrics.append(line[1:].split("::")[3].rstrip('\n'))
                    # Read the rest of the lyrics until the next song or album
                    for line in f:
                        if line.startswith("*") or line.startswith("#"):
                            break
                        lyrics.append(line.rstrip('\n'))
                    return lyrics
    return SONG_NOT_FOUND_ERROR

def getAlbumOfSong(song):
    # Find the album that contains the song
    for album in data_dict["albumsList"]:
        # Check if the song is in the album
        if song in data_dict["songsInAlbum"][album]:
            return album
    return SONG_NOT_FOUND_ERROR

if __name__ == "__main__":
    main()