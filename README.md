# Pink Floyd Protocol Server

This project implements a simple textual protocol server that provides information about Pink Floyd albums and songs.

## Project Structure

- `client.py`: Contains the client-side implementation of the Pink Floyd protocol.
- `server.py`: Contains the server-side implementation of the Pink Floyd protocol.
- `Pink_Floyd_DB.txt`: A text file database containing information about Pink Floyd albums and songs.

## How to Run

1. Start the server by running `server.py`.
2. Start the client by running `client.py`.

## Client Options

The client provides the following options:

1. Get the list of all Pink Floyd albums.
2. Get the list of all Pink Floyd songs in a specific album.
3. Get the length of a specific Pink Floyd song.
4. Get the lyrics of a specific Pink Floyd song.
5. In which albums does the song appear?
6. Get all songs with a specific word in the title.
7. Get all songs with a specific word in the lyrics.
8. EXIT

## Protocol

The Pink Floyd protocol message format is as follows:

`TYPE:<3-bit binary number>|DATA:<message data>`

## Error Messages

The server can respond with the following error messages:

- `INVALID_OPTION_ERROR`: The client sent an invalid option.
- `SONG_NOT_FOUND_ERROR`: The requested song was not found.
- `NO_SONGS_FOUND_ERROR`: No songs were found for the given criteria.
- `NO_ALBUMS_FOUND_ERROR`: No albums were found for the given criteria.

## Dependencies

- Python 3
- tkinter
- socket
- select
- errno