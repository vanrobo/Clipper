import socket
import threading
import time
import pyperclip

def get_local_ip():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    return local_ip

# --- Configuration ---
SERVER_HOST = '0.0.0.0'
# SERVER_PORT: The port this node will listen on for incoming connections.
# Choose a non-privileged port (above 1023).
SERVER_PORT = 65432

# TARGET_HOST/PORT: Default values for the client to attempt connecting to.
# These can be overridden by user input.
DEFAULT_TARGET_HOST = '127.0.0.1'
DEFAULT_TARGET_PORT = 65432


def get_local_ip_test():
    s = None # Initialize s to None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip_address = s.getsockname()[0]
        return local_ip_address
    except socket.error as e:
        print(f"Error getting local IP address: {e}")
        print("Please check your network connection.")
        return None
    finally:
        if s: 
            s.close()

# --- Server Component Function ---
def server_thread_function():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((SERVER_HOST, SERVER_PORT))
        server_socket.listen(5)
        print(f"[SERVER] Node server started, listening on {SERVER_HOST}:{SERVER_PORT}")

        try:
            while True:
                # Accept a new connection. This call blocks until a client connects.
                conn, addr = server_socket.accept()
                with conn: # Use 'with' statement to ensure the connection is closed automatically
                    print(f"[SERVER] Accepted connection from {addr}")
                    while True:
                        # Receive data from the client.
                        # 1024 is the buffer size (maximum number of bytes to receive at once).
                        data = conn.recv(1024)
                        if not data:
                            # If no data is received, the client has likely closed its connection.
                            print(f"[SERVER] Client {addr} disconnected.")
                            break
                        # Decode the received bytes into a UTF-8 string.
                        decoded_data = data.decode('utf-8')
                        print(f"[SERVER] Received from {addr}: {decoded_data}")
                        pyperclip.copy(decoded_data)
                        # Prepare a response message and encode it back to bytes before sending.
                        response_message = f"Echo from Node {SERVER_PORT}: '{decoded_data}'"
                        conn.sendall(response_message.encode('utf-8'))
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully to shut down the server.
            print("\n[SERVER] Server shutting down.")
        except Exception as e:
            print(f"[SERVER ERROR] An unexpected error occurred: {e}")
        finally:
            # Ensure the server socket is closed when the function exits.
            server_socket.close()



# --- Client Component Function ---
def client_thread_function():
    while True:
        # Prompt user for the target IP address to connect to.
        target_ip = input("\n[CLIENT] Enter target IP to connect to (or 'quit' to exit client): ")
        if target_ip.lower() == 'quit':
            print("[CLIENT] Client quitting.")
            break

        # Prompt user for the target port, using a default if none is provided.
        target_port_str = input(f"[CLIENT] Enter target port (default {DEFAULT_TARGET_PORT}): ")
        target_port = int(target_port_str) if target_port_str.isdigit() else DEFAULT_TARGET_PORT

        try:
            # Create a TCP/IP socket for the client.
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                # Connect to the specified target host and port.
                client_socket.connect((target_ip, target_port))
                print(f"[CLIENT] Connected to {target_ip}:{target_port}")

                while True:
                    message = pyperclip.paste()  # Get the current clipboard content.
                    if message:
                        print(f"[CLIENT] Sending message to {target_ip}:{target_port}: {message}")
                        client_socket.sendall(message.encode('utf-8'))

                    # Receive data back from the server.
                        data = client_socket.recv(1024)
                        if not data:
                            # If no data is received, the server has closed its connection.
                            print(f"[CLIENT] Server {target_ip}:{target_port} disconnected.")
                            break
                        # Decode the received bytes into a UTF-8 string.
                        print(f"[CLIENT] Received from {target_ip}:{target_port}: {data.decode('utf-8')}")
                    else:
                        print("[CLIENT] No message to send. Waiting for new clipboard content...")

                    time.sleep(0.25)  # Sleep for a second before checking the clipboard again

        except ConnectionRefusedError:
            print(f"[CLIENT ERROR] Connection refused. Is the target server running and accessible at {target_ip}:{target_port}?")
        except socket.gaierror:
            print(f"[CLIENT ERROR] Hostname '{target_ip}' could not be resolved. Check the IP address.")
        except Exception as e:
            print(f"[CLIENT ERROR] An unexpected error occurred during client operation: {e}")

        print(f"[CLIENT] Disconnected from {target_ip}:{target_port}")


# --- Main Execution Block ---
if __name__ == "__main__":
    # Create a thread for the server component.
    # The 'target' argument specifies the function to be run in the new thread.
    print(f"[MAIN] Local IP address: {get_local_ip()}")
    server_thread = threading.Thread(target=server_thread_function)
    server_thread.daemon = True
    # Start the server thread.
    server_thread.start()

    # Give the server thread a moment to initialize and start listening.
    time.sleep(1)

    # Run the client component in the main thread.
    client_thread_function()

    print("Program finished.")
