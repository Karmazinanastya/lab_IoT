import asyncio
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy_garden.mapview import MapMarker, MapView

from datasource import Datasource
from lineMapLayer import LineMapLayer


BASE_DIR = Path(__file__).resolve().parent
line_layer_colors = [
    [1, 0, 0, 1],
    [1, 0.5, 0, 1],
    [0, 1, 0, 1],
    [0, 1, 1, 1],
    [0, 0, 1, 1],
    [1, 0, 1, 1],
]


class MapViewApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mapview = None
        self.datasource = Datasource(user_id=1)
        self.line_layers = {}
        self.car_markers = {}
        self.bump_markers = []
        self.pothole_markers = []

    def on_start(self):
        self.update()
        Clock.schedule_interval(self.update, 1)

    def update(self, *args):
        new_points = self.datasource.get_new_points()
        if not new_points:
            return

        for point in new_points:
            lat, lon, road_state, user_id = point

            if user_id not in self.line_layers:
                self.line_layers[user_id] = LineMapLayer(color=line_layer_colors[user_id % len(line_layer_colors)])
                self.mapview.add_layer(self.line_layers[user_id])

            self.line_layers[user_id].add_point((lat, lon))
            self.update_car_marker(lat, lon, user_id)
            self.check_road_quality(point)

    def check_road_quality(self, point):
        lat, lon, road_state, _user_id = point
        if road_state == 'pothole':
            self.set_pothole_marker((lat, lon))
        elif road_state == 'bump':
            self.set_bump_marker((lat, lon))

    def update_car_marker(self, lat, lon, user_id):
        marker_source = str(BASE_DIR / 'images' / 'car.png')
        if user_id not in self.car_markers:
            self.car_markers[user_id] = MapMarker(lat=lat, lon=lon, source=marker_source)
            self.mapview.add_marker(self.car_markers[user_id])
        else:
            self.car_markers[user_id].lat = lat
            self.car_markers[user_id].lon = lon
        self.mapview.center_on(lat, lon)

    def set_pothole_marker(self, point):
        lat, lon = point
        marker = MapMarker(lat=lat, lon=lon, source=str(BASE_DIR / 'images' / 'pothole.png'))
        self.mapview.add_marker(marker)
        self.pothole_markers.append(marker)

    def set_bump_marker(self, point):
        lat, lon = point
        marker = MapMarker(lat=lat, lon=lon, source=str(BASE_DIR / 'images' / 'bump.png'))
        self.mapview.add_marker(marker)
        self.bump_markers.append(marker)

    def build(self):
        self.mapview = MapView(zoom=15, lat=50.4501, lon=30.5234)
        return self.mapview


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(MapViewApp().async_run(async_lib='asyncio'))
    loop.close()
