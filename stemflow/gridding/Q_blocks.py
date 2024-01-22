"""I call this Q_blocks because they are essential blocks for QTree methods"""

from typing import List, Tuple, Union

from ..utils.sphere.coordinate_transform import lonlat_spherical_transformer
from ..utils.sphere.distance import spherical_distance_from_coordinates


class QPoint:
    """A Point class for recording data points"""

    def __init__(self, index, x, y):
        self.x = x
        self.y = y
        self.index = index


class QNode:
    """A tree-like division node class"""

    def __init__(
        self,
        x0: Union[float, int],
        y0: Union[float, int],
        w: Union[float, int],
        h: Union[float, int],
        points: List[QPoint],
    ):
        self.x0 = x0
        self.y0 = y0
        self.width = w
        self.height = h
        self.points = points
        self.children = []

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def get_points(self):
        return self.points


class QGrid:
    """Grid class for STEM (fixed gird size)"""

    def __init__(self, x_index, y_index, x_range, y_range):
        self.x_index = x_index
        self.y_index = y_index
        self.x_range = x_range
        self.y_range = y_range
        self.points = []


class Sphere_Point:
    """A Point class for recording data points"""

    def __init__(self, index, inclination, azimuth):
        self.inclination = inclination
        self.azimuth = azimuth
        self.index = index


class Sphere_Face:
    """A tree-like division triangle node class for Sphere Quadtree"""

    def __init__(
        self,
        x0: Union[float, int],
        y0: Union[float, int],
        azimuth1: Union[float, int],
        inclination1: Union[float, int],
        azimuth2: Union[float, int],
        inclination2: Union[float, int],
        azimuth3: Union[float, int],
        inclination3: Union[float, int],
        points: list[Sphere_Point],
    ):
        self.x0 = x0
        self.y0 = y0

        self.distance = spherical_distance_from_coordinates(
            inclination1, azimuth1, inclination2, azimuth2, radius=6371.0
        )
        self.points = points
        self.children = []

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def get_points(self):
        return self.points
