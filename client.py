import socket
import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog

# Server IP and port
SERVER_IP = 'localhost'
SERVER_PORT = 1965

def main():
    # Create the client's socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server
    server_address = (SERVER_IP, SERVER_PORT)
    client_socket.connect(server_address)
    print('Connected to the server')

    # Create a GUI window
    window = tk.Tk()
    window.title("Client")

    # Make the window fill the screen
    window.state('zoomed')

    # Create all the options
    options = [
        "Get the list of all Pink Floyd albums",
        "Get the list of all Pink Floyd songs in a specific album",
        "Get the length of a specific Pink Floyd song",
        "Get the lyrics of a specific Pink Floyd song",
        "In which albums does the song appear?",
        "Get all songs with a specific word in the title",
        "Get all songs with a specific word in the lyrics",
        "EXIT"
    ]

    # Define the font for the labels and buttons
    font = ('Helvetica', 14, 'bold')

    # Run the GUI
    for i, option in enumerate(options, start=1):
        # Create a label and a button for each option
        label = tk.Label(window, text=option, font=font)
        label.grid(row=i-1, column=0, sticky='nsew')

        # Create a button for each option that calls the handleOption function using the lambda function
        button = tk.Button(window, text="Select", command=lambda i=i: handleOption(i, client_socket, window), font=font)

        # Style the button
        button.configure(bg='#0078D7', fg='white', relief='flat')

        button.grid(row=i-1, column=1, sticky='nsew')

    # Configure the rows and columns to expand as the window size changes
    for i in range(len(options)):
        window.grid_rowconfigure(i, weight=1)
    window.grid_columnconfigure(0, weight=3)
    window.grid_columnconfigure(1, weight=1)

    # Start the GUI event loop
    window.mainloop()

    # Close the connection
    print("Connection closed")

def handleOption(option, client_socket, window):
    # Handle the selected option
    if(option == 1):
        type = 1
        data = ""
    # If the option is 2, 3, 4, or 5, ask the user for the song/album name
    elif(option in [2, 3, 4, 5]):
        # Set the type based on the option
        type = option
        # Ask the user for the song/album name using a dialob box (ask for a string)
        data = simpledialog.askstring("Input", "Enter the song/album name:")
    # If the option is 6 or 7, ask the user for the word
    elif(option in [6, 7]):
        # Set the type based on the option
        type = option
        # Ask the user for the word using a dialob box (ask for a string)
        data = simpledialog.askstring("Input", "Enter the word:")
    elif(option == 8):
        # Set the type to 0 to close the connection
        type = 0
        data = ""
        try:
            # Send the message to the server
            message = f"TYPE:{type:03b}|DATA:{data}"
            client_socket.sendall(message.encode())
            client_socket.close()
        # Handle any exceptions that may occur
        except Exception as e:
            messagebox.showerror("Error", f"Error: {e}")

        # Close the window and return
        window.quit()
        return
    # If the option is invalid, show an error message and return (which can't ever happen when using the GUI)
    else:
        messagebox.showerror("Error", "Invalid option")
        return

    # Send the message to the server and receive the response
    try:
        # Send the message to the server
        message = f"TYPE:{type:03b}|DATA:{data}"
        client_socket.sendall(message.encode())

        # Receive the response from the server
        received_data = client_socket.recv(1024)
    # Handle any exceptions that may occur
    except Exception as e:
        messagebox.showerror("Error", f"Error: {e}")
        return

    # Show the received data in a message box
    messagebox.showinfo("Received data", received_data.decode())

if(__name__ == '__main__'):
    main()