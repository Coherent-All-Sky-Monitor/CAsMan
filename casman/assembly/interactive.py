"""
Interactive assembly operations for CAsMan.

This module provides interactive command-line interfaces for scanning
and assembling parts.
"""

import logging

logger = logging.getLogger(__name__)


def scan_and_assemble_interactive() -> None:
    """
    Interactive scanning and assembly function.

    Provides a command-line interface for scanning parts and recording
    their connections. Continues until the user types 'quit'.

    Returns
    -------
    None

    Examples
    --------
    >>> scan_and_assemble_interactive()  # doctest: +SKIP
    Interactive Assembly Scanner
    ============================
    Type 'quit' to exit.

    Scan first part: ANTP1-00001
    Scan connected part: LNA-P1-00001
    Connection recorded: ANTP1-00001 -> LNA-P1-00001

    Scan first part: quit
    Goodbye!
    """
    print("Interactive Assembly Scanner")
    print("=" * 30)
    print("Type 'quit' to exit.")
    print()

    while True:
        try:
            # Get first part
            first_part = input("Scan first part: ").strip()
            if first_part.lower() == 'quit':
                print("Goodbye!")
                break

            if not first_part:
                print("Please enter a part number.")
                continue

            # Get connected part
            connected_part = input("Scan connected part: ").strip()
            if connected_part.lower() == 'quit':
                print("Goodbye!")
                break

            if not connected_part:
                print("Please enter a connected part number.")
                continue

            # For now, just print the connection
            # In a real implementation, this would record to database
            print(f"Connection recorded: {first_part} -> {connected_part}")
            print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except (OSError, IOError) as e:
            logger.error("Error in interactive scanning: %s", e)
            print(f"Error: {e}")
            print("Please try again.")
