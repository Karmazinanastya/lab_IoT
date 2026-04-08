from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Optional

import config
from domain.accelerometer import Accelerometer
from domain.aggregated_data import AggregatedData
from domain.gps import Gps
from domain.parking import Parking


class FileDatasource:
    def __init__(self, accelerometer_filename: str, gps_filename: str, parking_filename: str) -> None:
        self.accelerometer_filename = accelerometer_filename
        self.gps_filename = gps_filename
        self.parking_filename = parking_filename
        self.accelerometer_file = None
        self.gps_file = None
        self.parking_file = None
        self.accelerometer_reader: Optional[csv.DictReader] = None
        self.gps_reader: Optional[csv.DictReader] = None
        self.parking_reader: Optional[csv.DictReader] = None

    def startReading(self, *args, **kwargs):
        self.stopReading()
        self.accelerometer_file = open(self.accelerometer_filename, 'r', encoding='utf-8', newline='')
        self.gps_file = open(self.gps_filename, 'r', encoding='utf-8', newline='')
        self.parking_file = open(self.parking_filename, 'r', encoding='utf-8', newline='')
        self.accelerometer_reader = csv.DictReader(self.accelerometer_file, skipinitialspace=True)
        self.gps_reader = csv.DictReader(self.gps_file, skipinitialspace=True)
        self.parking_reader = csv.DictReader(self.parking_file, skipinitialspace=True)

    def read(self) -> AggregatedData:
        acc_row = self._next_row('acc')
        gps_row = self._next_row('gps')
        parking_row = self._next_row('parking')

        accelerometer = Accelerometer(
            x=self._read_number(acc_row, ('x',)) / config.ACCELEROMETER_DIVISOR,
            y=self._read_number(acc_row, ('y',)) / config.ACCELEROMETER_DIVISOR,
            z=self._read_number(acc_row, ('z',)) / config.ACCELEROMETER_DIVISOR,
        )
        gps = self._read_gps(gps_row)
        parking = Parking(
            empty_count=int(self._read_number(parking_row, ('empty_count', 'count'))),
            gps=self._read_gps(parking_row),
        )

        return AggregatedData(
            accelerometer=accelerometer,
            gps=gps,
            parking=parking,
            time=datetime.utcnow(),
            user_id=config.USER_ID,
        )

    def stopReading(self, *args, **kwargs):
        for file_obj in (self.accelerometer_file, self.gps_file, self.parking_file):
            try:
                if file_obj:
                    file_obj.close()
            except Exception:
                pass
        self.accelerometer_file = None
        self.gps_file = None
        self.parking_file = None
        self.accelerometer_reader = None
        self.gps_reader = None
        self.parking_reader = None

    def _next_row(self, source: str) -> dict[str, str]:
        reader = self._get_reader(source)
        while True:
            row = next(reader, None)
            if row is None:
                self._rewind(source)
                reader = self._get_reader(source)
                continue
            normalized = {str(key).strip().lower(): value for key, value in row.items() if key is not None}
            if any(str(value).strip() for value in normalized.values()):
                return normalized

    def _get_reader(self, source: str):
        mapping = {
            'acc': self.accelerometer_reader,
            'gps': self.gps_reader,
            'parking': self.parking_reader,
        }
        reader = mapping[source]
        if reader is None:
            raise RuntimeError('Datasource is not started. Call startReading() before read().')
        return reader

    def _rewind(self, source: str):
        if source == 'acc' and self.accelerometer_file is not None:
            self.accelerometer_file.seek(0)
            self.accelerometer_reader = csv.DictReader(self.accelerometer_file, skipinitialspace=True)
        elif source == 'gps' and self.gps_file is not None:
            self.gps_file.seek(0)
            self.gps_reader = csv.DictReader(self.gps_file, skipinitialspace=True)
        elif source == 'parking' and self.parking_file is not None:
            self.parking_file.seek(0)
            self.parking_reader = csv.DictReader(self.parking_file, skipinitialspace=True)

    @staticmethod
    def _read_number(row: dict[str, str], keys: tuple[str, ...]) -> float:
        for key in keys:
            if key in row and str(row[key]).strip() != '':
                return float(row[key])
        raise KeyError(f'Missing required column: {keys}')

    def _read_gps(self, row: dict[str, str]) -> Gps:
        if 'longitude' in row and 'latitude' in row:
            lon = float(row['longitude'])
            lat = float(row['latitude'])
        elif 'lat' in row and 'lon' in row:
            lat = float(row['lat'])
            lon = float(row['lon'])
        else:
            raise KeyError('GPS row must contain longitude and latitude columns.')

        # Protect against accidentally swapped columns in sample files.
        if abs(lat) <= 40 and abs(lon) > 40:
            lat, lon = lon, lat

        return Gps(longitude=lon, latitude=lat)
