import socket
import struct

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 4242

CONNECT_TIMEOUT = 5.0
IO_TIMEOUT = 30.0

MAX_MESSAGE_SIZE = 1024 * 1024  # 1 MB

HEADER_SIZE = 4


def recv_exact(sock: socket.socket, size: int) -> bytes | None:
    """
    Receive exactly 'size' bytes.

    Returns None if the server closes the connection normally
    before a new message begins.

    Raises ConnectionError if the connection is closed
    in the middle of a message.
    """
    data = bytearray()

    while len(data) < size:
        chunk = sock.recv(size - len(data))

        # recv() returns b'' when the peer performs an orderly shutdown.
        if not chunk:
            if len(data) == 0:
                return None

            raise ConnectionError(
                "Connection closed in the middle of a message"
            )

        data.extend(chunk)

    return bytes(data)


def send_message(sock: socket.socket, payload: bytes) -> None:
    """
    Send one length-prefixed message.

    Message format:
        [4-byte payload length][payload]
    """
    header = struct.pack("!I", len(payload))

    # sendall() repeatedly sends data until all bytes have been accepted
    # by the local socket or an error occurs.
    sock.sendall(header + payload)


def recv_message(sock: socket.socket) -> bytes | None:
    """
    Receive one complete length-prefixed message.

    Returns None if the server closes the connection normally.
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

    if payload is None:
        raise ConnectionError(
            "Connection closed before the payload was received"
        )

    return payload


def main() -> None:
    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    try:
        # Limit how long connect() may block.
        sock.settimeout(CONNECT_TIMEOUT)

        print(
            f"[CONNECTING] "
            f"{SERVER_HOST}:{SERVER_PORT}"
        )

        sock.connect((SERVER_HOST, SERVER_PORT))

        print("[CONNECTED]")

        # Use a separate timeout for send and receive operations.
        sock.settimeout(IO_TIMEOUT)

        while True:
            text = input("message> ")

            if text.lower() in {"quit", "exit"}:
                print("[DISCONNECTING]")
                break

            payload = text.encode("utf-8")

            if len(payload) > MAX_MESSAGE_SIZE:
                print("[ERROR] Message is too large")
                continue

            send_message(sock, payload)

            echoed = recv_message(sock)

            # None means the server performed an orderly shutdown.
            if echoed is None:
                print("[DISCONNECTED] Server closed the connection normally")
                break

            print(
                "echo> "
                + echoed.decode(
                    "utf-8",
                    errors="replace"
                )
            )

    except EOFError:
        # On Unix-like systems, Ctrl-D causes input() to raise EOFError.
        # Treat this as a normal request to terminate the client.
        print("\n[EOF] Input closed. Disconnecting normally.")

    except KeyboardInterrupt:
        # Ctrl-C is also handled gracefully instead of printing a traceback.
        print("\n[INTERRUPTED] Client stopping")

    except socket.timeout:
        print("[TIMEOUT] Socket operation timed out")

    except ConnectionRefusedError:
        print("[ERROR] Connection refused. Is the server running?")

    except ConnectionResetError:
        print("[ERROR] Connection reset by server")

    except BrokenPipeError:
        print("[ERROR] Broken pipe")

    except ConnectionError as e:
        print(f"[CONNECTION ERROR] {e}")

    except ValueError as e:
        print(f"[INVALID MESSAGE] {e}")

    except OSError as e:
        print(f"[SOCKET ERROR] {e}")

    finally:
        # Closing the TCP socket normally causes the OS to initiate
        # an orderly connection shutdown, typically by sending FIN.
        sock.close()
        print("[CLOSED]")


if __name__ == "__main__":
    main()
