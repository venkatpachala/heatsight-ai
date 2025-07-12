import pandas as pd
import numpy as np
import os

SCHEDULE_PATH = os.path.join('insights', 'staff_schedule.csv')


def generate_staff_schedule():
    """Create a simple weekly staff schedule across store zones."""
    zones = [f"{chr(65+r)}{c}" for r in range(10) for c in range(1, 11)]
    shifts = ['Morning', 'Afternoon', 'Evening']
    schedule = []
    for day in range(1, 8):  # 7-day schedule
        for shift in shifts:
            zone = np.random.choice(zones)
            staff_count = np.random.randint(3, 7)
            schedule.append({'Day': day, 'Shift': shift, 'Zone': zone, 'Staff_Count': staff_count})

    pd.DataFrame(schedule).to_csv(SCHEDULE_PATH, index=False)
    print(f'Staff schedule saved to {SCHEDULE_PATH}')


if __name__ == '__main__':
    generate_staff_schedule()
