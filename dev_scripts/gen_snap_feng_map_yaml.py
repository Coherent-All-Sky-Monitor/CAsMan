"""
Generate snap_feng_map.yaml for 43 SNAPs, each with 12 ADCs.
Output format: SNAP<3 digit number>_ADC<2 digit number>: FENG_<crate num><snap letter><adc number>
"""

import os

LETTERS = [chr(ord('A') + i) for i in range(22)]
db_dir = os.path.join(os.path.dirname(__file__), '../database')
os.makedirs(db_dir, exist_ok=True)
yaml_path = os.path.join(db_dir, 'snap_feng_map.yaml')
with open(yaml_path, 'w', encoding='utf-8') as f:
    f.write('# SNAP to FENG mapping for 43 SNAPs, each with 12 ADCs\n')
    f.write(
        '# Format: SNAP<3 digit number>_ADC<2 digit number>: \
        FENG_<crate num><snap letter><adc number>\n\n'
        )
    for crate in [1, 2]:
        SNAP_START = 1 if crate == 1 else 23
        SNAP_END = 22 if crate == 1 else 43
        for snap_num in range(SNAP_START, SNAP_END + 1):
            snap_letter = LETTERS[(snap_num - 1) % 22]
            for adc in range(12):
                snap_key = f'SNAP{snap_num:03d}_ADC{adc:02d}'
                feng_val = f'FENG_{crate}{snap_letter}{adc:02d}'
                f.write(f'{snap_key}: {feng_val}\n')
