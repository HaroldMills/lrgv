"""
Script that generates the `devices` and `station_devices` sections of
a monitoring network's metadata YAML file.
"""


STATION_NAMES = (
    'BBBO',
    'Barker',
    'Golden Hill',
    'Hamlin Beach',
    'Hilton',
    'Kendall',
    'Lakeside',
    'Lyndonville',
    'Newfane',
    'Station 1',
    'Station 5',
    'Wilson',
)

YEAR = 2026

DEVICE_TEMPLATE = '''

    # {station_name}

    - name: 21c {station_num} Vesper
      model: 21c
      serial_number: {station_num} Vesper
      description: Microphone and Vesper Recorder at {station_name} station.

    - name: 21c {station_num} Tseep-r
      model: 21c
      serial_number: {station_num} Tseep-r
      description: Microphone and Tseep-r at {station_name} station.

    - name: Vesper Recorder {station_num}
      model: Vesper Recorder
      serial_number: {station_num}
      description: Vesper Recorder at {station_name} station.

    - name: Tseep-r {station_num}
      model: Tseep-r
      serial_number: {station_num}
      description: Tseep-r at {station_name} station.'''

STATION_DEVICE_TEMPLATE = '''
    - station: {station_name}
      start_time: {start_year}-01-01
      end_time: {end_year}-01-01
      devices:
          - 21c {station_num} Vesper
          - 21c {station_num} Tseep-r
          - Vesper Recorder {station_num}
          - Tseep-r {station_num}
      connections:
          - output: 21c {station_num} Vesper Output
            input: Vesper Recorder {station_num} Input
          - output: 21c {station_num} Tseep-r Output
            input: Tseep-r {station_num} Input'''


def main():

    create_devices_section()

    print()
    print()

    create_station_devices_section()


def create_devices_section():

    print('devices:')

    for station_num, station_name in enumerate(STATION_NAMES):
        params = {
            'station_num': station_num,
            'station_name': station_name
        }
        print(DEVICE_TEMPLATE.format_map(params))


def create_station_devices_section():

    print('station_devices:')

    for station_num, station_name in enumerate(STATION_NAMES):
        params = {
            'station_num': station_num,
            'station_name': station_name,
            'start_year': YEAR,
            'end_year': YEAR + 1
        }
        print(STATION_DEVICE_TEMPLATE.format_map(params))


if __name__ == '__main__':
    main()
