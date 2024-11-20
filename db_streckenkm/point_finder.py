from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsPointXY, QgsWkbTypes
from qgis.core import QgsFeature, QgsGeometry, QgsProject, QgsVectorLayer

from . import string_to_real

NEIGHBOR_SAMPLE_SIZE = 100


class NearestPointFinder:
    NO_POINTS_FOUND = 1
    START_POS_NOT_FOUND = 2
    VALUE_FORMAT_WRONG = 3

    def __init__(self, search_layer: QgsVectorLayer, spatial_index, start_pos_field_name, ignore_empty=True,
                 field_is_real=False):
        self.search_layer = search_layer
        self.spatial_index = spatial_index
        self.start_pos_field_name = start_pos_field_name
        self.ignore_empty = ignore_empty
        self.field_is_real = field_is_real

    def find_nearest_feature(self, point: QgsPointXY, point_crs: QgsCoordinateReferenceSystem) -> QgsFeature | None:

        if point_crs != self.search_layer.crs():
            point = self.transform_to_layer_crs(point, point_crs)
        nearest_ids = self.spatial_index.nearestNeighbor(QgsPointXY(point), NEIGHBOR_SAMPLE_SIZE)
        nearest_feature = None
        nearest_dist = float('inf')
        if not nearest_ids:
            return None
        for fid in nearest_ids:
            feature = self.search_layer.getFeature(fid)
            val = feature[self.start_pos_field_name]
            if not val and self.ignore_empty:
                continue
            geom = feature.geometry()
            distance = geom.distance(QgsGeometry.fromPointXY(point))
            if distance < nearest_dist:
                nearest_feature = feature
                nearest_dist = distance
        return nearest_feature

    def get_partial_line_length(self, line: QgsGeometry, index: int, closest_point: QgsPointXY):
        """
        calculates Length from Start of LineSegement to Closest Point
        """
        line_strings = line.asMultiPolyline()
        cumulative_length = 0
        current_segment = 0
        last_point = [line_strings[0][0]]
        for line in line_strings:
            vertices = line  # Vertices of the current LineString
            last_point = vertices[0]
            num_segments = len(vertices) - 1  # Number of segments in the current LineString

            # Check if the target segment index is within this LineString
            if current_segment + num_segments > index:
                # Calculate the partial length in this LineString
                target_index = index - current_segment  # Segment index within this LineString
                last_point = vertices[target_index]
                partial_vertices = vertices[:target_index + 1]  # Include points up to the target segment
                partial_line = QgsGeometry.fromPolylineXY(partial_vertices)
                cumulative_length += partial_line.length()
                break
            else:
                # Add the full length of this LineString
                full_line = QgsGeometry.fromPolylineXY(vertices)
                cumulative_length += full_line.length()
                current_segment += num_segments
        partial_line = QgsGeometry.fromPolylineXY([last_point, closest_point])
        cumulative_length += partial_line.length()
        return cumulative_length

    def transform_to_project_crs(self, point: QgsPointXY):
        source_crs = self.search_layer.crs()
        target_crs = QgsProject.instance().crs()
        transform_context = QgsProject.instance().transformContext()
        # Create the coordinate transformer
        transformer = QgsCoordinateTransform(source_crs, target_crs, transform_context)
        return transformer.transform(point)

    def transform_to_layer_crs(self, point: QgsPointXY, source_crs: QgsCoordinateReferenceSystem):
        return self.transform_from_to(point, source_crs, self.search_layer.crs())

    def transform_from_to(self, point: QgsPointXY, source_crs: QgsCoordinateReferenceSystem,
                          target_crs: QgsCoordinateReferenceSystem):
        transform_context = QgsProject.instance().transformContext()
        # Create the coordinate transformer
        transformer = QgsCoordinateTransform(source_crs, target_crs, transform_context)
        return transformer.transform(point)

    def get_feature_value(self, feature, feature_name) -> str | None:
        return feature[feature_name] if feature_name in feature.fields().names() else None

    def find_closest_point(self, point: QgsPointXY, source_crs: QgsCoordinateReferenceSystem) -> tuple[
        QgsFeature | None, QgsPointXY | None, float | None]:
        if source_crs != self.search_layer.crs():
            point = self.transform_to_layer_crs(point, source_crs)

        local_crs = self.search_layer.crs()
        nearest_feature = self.find_nearest_feature(point, local_crs)

        if not nearest_feature:
            return self.NO_POINTS_FOUND, None, None

        if QgsWkbTypes.geometryType(self.search_layer.wkbType()) == QgsWkbTypes.LineGeometry:
            # Search for closest Point
            ortho_dist, nearest_point, next_index, is_left = nearest_feature.geometry().closestSegmentWithContext(point)
            dist = self.get_partial_line_length(nearest_feature.geometry(), next_index - 1, nearest_point)
        else:
            nearest_point = nearest_feature.geometry().asPoint()
            dist = 0

        nearest_point = self.transform_from_to(nearest_point, local_crs, source_crs)

        start_pos = self.get_feature_value(nearest_feature, self.start_pos_field_name)
        if start_pos is None:
            return nearest_feature, nearest_point, self.START_POS_NOT_FOUND
        try:
            if self.field_is_real:
                position = start_pos + dist / 1000
            else:
                position = string_to_real(start_pos) + dist / 1000
        except TypeError:
            return nearest_feature, nearest_point, self.VALUE_FORMAT_WRONG

        return nearest_feature, nearest_point, position
