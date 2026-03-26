from csv import reader
from datetime import datetime
from domain.aggregated_data import AggregatedData
from domain.accelerometer import Accelerometer
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
        self.accelerometer_reader = None
        self.gps_reader = None
        self.parking_reader = None

    def startReading(self, *args, **kwargs):
        self.accelerometer_file = open(self.accelerometer_filename, "r", encoding="utf-8")
        self.gps_file = open(self.gps_filename, "r", encoding="utf-8")
        self.parking_file = open(self.parking_filename, "r", encoding="utf-8")
        self.accelerometer_reader = reader(self.accelerometer_file)
        self.gps_reader = reader(self.gps_file)
        self.parking_reader = reader(self.parking_file)
        next(self.accelerometer_reader, None)
        next(self.gps_reader, None)
        next(self.parking_reader, None)

    def read(self) -> AggregatedData:
        try:
            acc_row = next(self.accelerometer_reader)
            gps_row = next(self.gps_reader)
            parking_row = next(self.parking_reader)
        except StopIteration:
            self.stopReading()
            self.startReading()
            acc_row = next(self.accelerometer_reader)
            gps_row = next(self.gps_reader)
            parking_row = next(self.parking_reader)

        accelerometer = Accelerometer(
            x=int(acc_row[0]),
            y=int(acc_row[1]),
            z=int(acc_row[2])
        )
        gps = Gps(
            longitude=float(gps_row[0]),
            latitude=float(gps_row[1])
        )
        parking = Parking(
            empty_count=int(parking_row[0]),
            gps=Gps(
                longitude=float(parking_row[1]),
                latitude=float(parking_row[2])
            )
        )
        return AggregatedData(
            accelerometer=accelerometer,
            gps=gps,
            parking=parking,
            time=datetime.now()
        )

    def stopReading(self, *args, **kwargs):
        if self.accelerometer_file:
            self.accelerometer_file.close()
        if self.gps_file:
            self.gps_file.close()
        if self.parking_file:
            self.parking_file.close()