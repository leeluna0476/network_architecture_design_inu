import socket
import struct
import threading

HOST = "0.0.0.0"
PORT = 4242

CLIENT_TIMEOUT = 30.0
MAX_MESSAGE_SIZE = 1024 * 1024  # 1 MB

HEADER_SIZE = 4


def recv_exact(sock: socket.socket, size: int) -> bytes | None:
    """
    Receive exactly 'size' bytes.

    Returns None if the peer closes the connection normally
    before a new message begins.

    Raises ConnectionError if the connection is closed
    in the middle of a message.
    """
    data = bytearray()

    while len(data) < size:
        chunk = sock.recv(size - len(data))

        # recv() returns b'' when the peer performs an orderly shutdown.
        if not chunk:
            # EOF before receiving any part of this field is treated
            # as a normal connection termination.
            if len(data) == 0:
                return None

            # EOF after receiving only part of the expected data means
            # that the protocol message was incomplete.
            raise ConnectionError(
                "Connection closed in the middle of a message"
            )

        data.extend(chunk)

    return bytes(data)


def send_message(sock: socket.socket, payload: bytes) -> None:
    """
    Send one message using a 4-byte length-prefixed protocol.

    Message format:
        [4-byte payload length][payload]
    """
    header = struct.pack("!I", len(payload))

    # sendall() handles partial sends internally.
    sock.sendall(header + payload)


def recv_message(sock: socket.socket) -> bytes | None:
    """
    Receive one length-prefixed message.

    Returns None when the peer closes the connection normally.
    """
    header = recv_exact(sock, HEADER_SIZE)

    if header is None:
        return None

    message_length = struct.unpack("!I", header)[0]

    if message_length > MAX_MESSAGE_SIZE:
        raise ValueError(
            f"Message too large: {message_length} bytes"
        )

    payload = recv_exact(sock, message_length)

    # At this point the header has already been received,
    # so EOF before the payload is complete is not a normal message boundary.
    if payload is None:
        raise ConnectionError(
            "Connection closed before the payload was received"
        )

    return payload


def handle_client(client_socket: socket.socket, address) -> None:
    """
    Handle one connected client.

    Each client runs in its own thread, so blocking socket I/O
    does not prevent other clients from being served.
    """
    print(f"[CONNECTED] {address}")

    client_socket.settimeout(CLIENT_TIMEOUT)

    try:
        while True:
            message = recv_message(client_socket)

            # None means recv() eventually returned b'' before
            # a new message started, which is a normal EOF.
            if message is None:
                print(f"[DISCONNECTED] {address} closed normally")
                break

            print(
                f"[RECEIVED] {address}: "
                f"{message.decode('utf-8', errors='replace')}"
            )

            # Echo the same message back to the client.
            send_message(client_socket, message)

    except socket.timeout:
        print(f"[TIMEOUT] {address}")

    except ConnectionResetError:
        print(f"[RESET] Connection reset by {address}")

    except BrokenPipeError:
        print(f"[BROKEN PIPE] {address}")

    except ConnectionError as e:
        print(f"[CONNECTION ERROR] {address}: {e}")

    except ValueError as e:
        print(f"[INVALID MESSAGE] {address}: {e}")

    except OSError as e:
        print(f"[SOCKET ERROR] {address}: {e}")

    finally:
        client_socket.close()
        print(f"[CLOSED] {address}")


def main() -> None:
    server_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    # Allow the server to restart without waiting for an old socket
    # address to become reusable.
#    server_socket.setsockopt(
#        socket.SOL_SOCKET,
#        socket.SO_REUSEADDR,
#        1
#    )

    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen()

        print(f"[LISTENING] {HOST}:{PORT}")

        while True:
            try:
                # accept() blocks until a new client connects.
                client_socket, address = server_socket.accept()

                # Create one thread for each connected client.
                thread = threading.Thread(
                    target=handle_client,
                    args=(client_socket, address),
                    daemon=True
                )

                thread.start()

                print(
                    f"[ACTIVE CONNECTIONS] "
                    f"{threading.active_count() - 1}"
                )

            except KeyboardInterrupt:
                print("\n[SERVER STOPPING]")
                break

            except OSError as e:
                print(f"[ACCEPT ERROR] {e}")

    finally:
        server_socket.close()
        print("[SERVER CLOSED]")


if __name__ == "__main__":
    main()
