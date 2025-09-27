#!/usr/bin/env python3
"""
Send CAN frames at a fixed interval.
- Default bus: socketcan on vcan0 (change CHANNEL to 'can0' for real hardware)
- Tries hardware/driver periodic sending; falls back to a timed loop.
"""
import sys
import time
import can

BUSTYPE = "socketcan"
CHANNEL = "vcan0"  # change to 'can0' for real interface
INTERVAL_MS = 10


def send_one(bus: can.BusABC) -> None:
    """Send one extended-id message (example)."""
    msg = can.Message(
        arbitration_id=0xC0FFEE,
        data=[0, 25, 0, 1, 3, 1, 4, 1],
        is_extended_id=True,
    )
    try:
        bus.send(msg)
        print(f"Message sent on {bus.channel_info}")
    except can.CanError as e:
        print(f"Message NOT sent: {e}")


def main() -> None:
    # For socketcan, bitrate is configured at the OS level, so we don't pass it here.
    try:
        bus = can.interface.Bus(channel=CHANNEL, bustype=BUSTYPE)
    except OSError as e:
        print(
            f"CAN bus not found or accessible on {BUSTYPE}:{CHANNEL}. "
            f"Ensure the interface exists and is up. Error: {e}"
        )
        sys.exit(1)

    # Example single send (optional): uncomment if you want to send this once up front.
    # send_one(bus)

    interval_s = INTERVAL_MS / 1000.0
    print(f"Starting CAN message loop on {bus.channel_info}, every {INTERVAL_MS} ms...")

    # The periodic message we'll send
    message = can.Message(
        arbitration_id=0x123,
        data=[0x01, 0x02, 0x03, 0x04],
        is_extended_id=False,
    )

    try:
        # Prefer driver/hardware periodic sending when supported
        try:
            sender = bus.send_periodic(message, interval_s)
            print("Using driver/hardware periodic sending (send_periodic). Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
        except (AttributeError, NotImplementedError):
            # Fallback: software-timed loop
            print("send_periodic not available; using software loop. Press Ctrl+C to stop.")
            while True:
                t0 = time.perf_counter()
                bus.send(message)
                print(
                    f"CAN message sent: ID=0x{message.arbitration_id:X}, "
                    f"Data={message.data.hex()}"
                )
                elapsed = time.perf_counter() - t0
                sleep_for = interval_s - elapsed
                if sleep_for > 0:
                    time.sleep(sleep_for)
                else:
                    print(
                        f"Warning: loop iteration took {elapsed * 1000:.2f} ms "
                        f"(> {INTERVAL_MS} ms)."
                    )
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        # Stop periodic sender if we started one
        try:
            sender.stop()  # type: ignore[name-defined]
        except Exception:
            pass
        bus.shutdown()
        print("CAN bus shut down.")


if __name__ == "__main__":
    main()
