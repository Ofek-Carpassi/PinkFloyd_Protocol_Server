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

import select # Used to monitor multiple sockets
import socket # Used to create sockets
import errno # Used to handle socket errors

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

def main():
    # Create a socket to listen for incoming connections
    LISTENING_PORT = 1965
    listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Try to bind the socket to the listening port
    while True:
        try:
            listening_socket.bind(('', LISTENING_PORT))
            break
        # If the port is already in use, try the next port
        except socket.error as e:
            if e.errno == errno.EADDRINUSE:
                print(f"Port {LISTENING_PORT} is already in use.")
                # Try the next port
                LISTENING_PORT += 1
                print(f"Trying to bind to port {LISTENING_PORT} instead.")
            # If there is another error, raise it
            else:
                raise

    # Start listening for incoming connections
    listening_socket.listen(1)
    print("Server is listening on port", LISTENING_PORT)

    inputs = [listening_socket]  # Create a list of sockets to monitor for incoming data

    while True:
        # Wait for a socket to become readable
        readable, _, exceptional = select.select(inputs, [], inputs)

        # Iterate over the readable sockets
        for s in readable:
            if s is listening_socket:
                # If the socket is the listening socket, accept the connection
                client_socket, client_address = s.accept()
                print("Connection from", client_address)
                # Add the client socket to the list of sockets to monitor
                inputs.append(client_socket)
            else:
                # Try to receive data from the client
                try:
                    data = s.recv(BUFFER_SIZE).decode()
                except ConnectionResetError:
                    # If the client closes the connection, remove the socket
                    print("Connection closed by the client")
                    inputs.remove(s)
                    s.close()
                    continue

                # If the client sends an empty message, close the connection
                if data == "":
                    print("Connection closed by the client")
                    inputs.remove(s)
                    s.close()
                    continue

                print("Received data:", data)
                
                # Try to break the data into type and message
                try:
                    type, data = breakData(data)
                # Make sure the message is in the correct format
                except ValueError:
                    print("Invalid message received. Closing connection.")
                    inputs.remove(s)
                    s.close()
                    continue

                # Handle the message type and send a response
                response = handleType(type, data)
                s.send(response.encode())

                # If the client sends a message with type 0, close the connection
                if type == EXIT_TYPE:
                    print("Connection closed by the client")
                    inputs.remove(s)
                    s.close()

        # Iterate over the exceptional sockets
        for s in exceptional:
            # If there is an error with a socket, remove it
            inputs.remove(s)
            s.close()

def breakData(data):
    # Try to break the data into type and message
    try:
        # Get the type and message from the data
        type = int(data[TYPE_INDEX_START:TYPE_INDEX_END], 2)
        data = data[DATA_INDEX_START:]
        return type, data
    except ValueError:
        # Make sure the type is a valid number
        raise ValueError("Invalid message format.")

def handleType(type, data):
    # Handle the message type according to the type
    if type == EXIT_TYPE:
        return "EXIT"
    elif type == ALBUMS_LIST_TYPE:
        return getAlbumsList()
    elif type == SONGS_IN_ALBUM_TYPE:
        return getSongsInAlbum(data)
    elif type == LENGTH_OF_SONG_TYPE:
        return getLengthOfSong(data)
    elif type == LYRICS_OF_SONG_TYPE:
        return getLyricsOfSong(data)
    elif type == ALBUM_OF_SONG_TYPE:
        return getAlbumOfSong(data)
    elif type == SONGS_WITH_WORD_IN_TITLE_TYPE:
        return getSongsWithWordInTitle(data)
    elif type == SONGS_WITH_WORD_IN_LYRICS_TYPE:
        return getSongsWithWordInLyrics(data)
    else:
        return INVALID_OPTION_ERROR

def getAlbumsList():
    albums = []
    # Read the entire database file
    with open(DB_FILE, "r") as f:
        for line in f:
            # If the line starts with a #, it is an album
            if line[0] == "#":
                # Add the album's name to the list of albums and not the year of release
                albums.append(line[1:].split("::")[0])

    # If there are no albums in the list, return an error message (will never happen with the provided database file)
    if(albums == []):
        print(NO_ALBUMS_FOUND_ERROR)
        return NO_ALBUMS_FOUND_ERROR

    # If there are albums in the list, return them as a comma-separated string
    return ", ".join(albums)

def getSongsInAlbum(album):
    # Read the entire database file
    with open(DB_FILE, "r") as f:
        in_target_album = False
        songs = []

        for line in f:
            # If the line starts with a #, it is an album
            if line.startswith("#"):
                # Check if the album is the target album
                in_target_album = line[1:].split("::")[0].strip() == album
            # If the line starts with a * and we are in the target album, it is a song within the album
            elif in_target_album and line.startswith("*"):
                # Add the song's name to the list of songs
                song_name = line[1:].split("::")[0].strip()
                # Check if the song name is not empty
                if song_name:
                    songs.append(song_name)

        # If there are songs in the list, return them as a comma-separated string
        if songs:
            return ", ".join(songs)

    # If the album is not found, return an error message (will never happen with the provided database file)
    return SONG_NOT_FOUND_ERROR

def getLengthOfSong(song):
    # Read the entire database file
    with open(DB_FILE, "r") as f:
        for line in f:
            # If the line starts with a *, it is a song
            if line[0] == "*":
                # Check if the song is the target song
                if line[1:].split("::")[0] == song:
                    # Return the length of the song
                    return line[1:].split("::")[2]
                
    # If the song is not found, return an error message
    return SONG_NOT_FOUND_ERROR

def getLyricsOfSong(song):
    lyrics = []
    # Read the entire database file
    with open(DB_FILE, "r") as f:
        for line in f:
            # If the line starts with a *, it is a song
            if line[0] == "*":
                # Check if the song is the target song
                if line[1:].split("::")[0] == song:
                    # Add the lyrics to the list of lyrics
                    lyrics.append(line[1:].split("::")[3].rstrip('\n'))
                    for line in f:
                        # Make sure we haven't reached the next song or album
                        if line[0] == "*" or line[0] == "#":
                            break
                        # Add the lyrics to the list of lyrics
                        lyrics.append(line.rstrip('\n'))
                    # Return the lyrics as a string
                    return "\n".join(lyrics)
                
    # If the song is not found, return an error message
    return SONG_NOT_FOUND_ERROR

def getAlbumOfSong(song):
    # Run through all the albums and check if the song is in the album
    for album in getAlbumsList().split(", "):
        # If the song is in the album, return the album
        if song in getSongsInAlbum(album).split(", "):
            return album
        
    # If the song is not found, return an error message
    return SONG_NOT_FOUND_ERROR

def getSongsWithWordInTitle(word):
    songs = []
    # Run through all the albums and songs and check if the word is in the song title
    for album in getAlbumsList().split(", "):
        # Run through all the songs in the album
        for song in getSongsInAlbum(album).split(", "):
            # If the word is in the song title, add the song to the list of songs
            if word.lower() in song.lower().split():
                songs.append(song)
    # If there are no songs in the list, return an error message
    if(songs == []):
        print(NO_SONGS_FOUND_ERROR)
        return NO_SONGS_FOUND_ERROR
    # If there are songs in the list, return them as a comma-separated string
    return ", ".join(songs)

def getSongsWithWordInLyrics(word):
    songs = []
    # Run through all the albums and songs and check if the word is in the song lyrics
    for album in getAlbumsList().split(", "):
        # Run through all the songs in the album
        for song in getSongsInAlbum(album).split(", "):
            # If the word is in the song lyrics, add the song to the list of songs
            if word.lower() in getLyricsOfSong(song).lower().split():
                songs.append(song)
    # If there are no songs in the list, return an error message
    if(songs == []):
        print(NO_SONGS_FOUND_ERROR)
        return NO_SONGS_FOUND_ERROR
    # If there are songs in the list, return them as a comma-separated string
    return ", ".join(songs)

if __name__ == '__main__':
    main()