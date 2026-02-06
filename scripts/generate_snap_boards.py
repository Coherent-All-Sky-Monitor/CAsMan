#!/usr/bin/env python3
"""
Generate dummy SNAP board configuration CSV.

Creates a CSV file mapping each SNAP board (identified by chassis and slot)
to its serial number, MAC address, IP address, and F-engine ID.

SNAP Configuration:
- 4 chassis (1-4)
- 11 slots per chassis (A-K)
- Total: 44 SNAP boards
- Each port's packet_index = feng_id * 12 + port_number

For initial setup, generates:
- Serial numbers: SN01 to SN44
- MAC addresses: Dummy format 00:11:22:33:XX:YY
- IP addresses: 192.168.1.1 to 192.168.1.44
- F-engine IDs: 0 to 43
"""

import csv
from datetime import datetime
from pathlib import Path


def generate_snap_boards():
    """Generate SNAP board configuration and write to CSV."""
    
    # Output path
    output_path = Path(__file__).parent.parent / "database" / "snap_boards.csv"
    
    # Generate timestamp
    update_date = datetime.now().strftime("%Y-%m-%d")
    
    # Configuration
    chassis_list = [1, 2, 3, 4]
    slot_list = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K']
    
    boards = []
    board_num = 1
    feng_id = 0  # F-engine ID starts at 0
    
    for chassis in chassis_list:
        for slot in slot_list:
            # Generate serial number
            sn = f"SN{board_num:02d}"
            
            # Generate dummy MAC address
            # Format: 00:11:22:33:XX:YY where XX is chassis, YY is slot index
            slot_idx = ord(slot) - ord('A')
            mac = f"00:11:22:33:{chassis:02X}:{slot_idx:02X}"
            
            # Generate IP address
            # Using 192.168.1.0/24 subnet
            ip = f"192.168.1.{board_num}"
            
            boards.append({
                'chassis': chassis,
                'slot': slot,
                'sn': sn,
                'mac': mac,
                'ip': ip,
                'feng_id': feng_id
            })
            
            board_num += 1
            feng_id += 1
    
    # Write to CSV
    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = ['chassis', 'slot', 'sn', 'mac', 'ip', 'feng_id', 'notes']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for board in boards:
            writer.writerow({
                'chassis': board['chassis'],
                'slot': board['slot'],
                'sn': board['sn'],
                'mac': board['mac'],
                'ip': board['ip'],
                'feng_id': board['feng_id'],
                'notes': f'Generated on {update_date}'
            })
    
    print(f"[OK] Generated SNAP board configuration: {output_path}")
    print(f"  Total boards: {len(boards)}")
    print("\nSample entries:")
    print(f"  Chassis 1, Slot A: SN={boards[0]['sn']}, FENG_ID={boards[0]['feng_id']}, MAC={boards[0]['mac']}, IP={boards[0]['ip']}")
    print(f"  Chassis 2, Slot A: SN={boards[11]['sn']}, FENG_ID={boards[11]['feng_id']}, MAC={boards[11]['mac']}, IP={boards[11]['ip']}")
    print(f"  Chassis 4, Slot K: SN={boards[43]['sn']}, FENG_ID={boards[43]['feng_id']}, MAC={boards[43]['mac']}, IP={boards[43]['ip']}")
    print(f"\nPacket index calculation: packet_index = feng_id * 12 + port_number")
    print(f"  Example: SNAP1A (feng_id=0) port 5 → packet_index = 0*12+5 = 5")
    print(f"  Example: SNAP2A (feng_id=11) port 5 → packet_index = 11*12+5 = 137")
    
    return boards


if __name__ == "__main__":
    generate_snap_boards()
