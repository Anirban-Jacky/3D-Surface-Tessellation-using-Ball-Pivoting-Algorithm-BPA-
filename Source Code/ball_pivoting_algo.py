from typing import List
import numpy as np
from spatial_grid import Grid
from point import Point
import helper
from Tracker import Edge, Triangle


class BPA:
    def __init__(self, path, radius, num_workers=1):
        self.first_free_point_index = 0
        self.points = self.read_points(path)
        self.num_triangles_this_edge_is_in=0
        self.radius = radius
        self.grid = Grid(points=self.points, radius=radius)
        self.num_free_points = len(self.points)
        self.num_workers = num_workers

    def read_points(self, path: str) -> List:
        #Read the points from a text file.
        points = []
        f = open(path, "r")
        lines = f.read().splitlines()

        for i, line in enumerate(lines):
            coordinates = line.split()

            if len(coordinates) == 3:
                p = Point(float(coordinates[0]), float(coordinates[1]), float(coordinates[2]), id=i)
                points.append(p)

            elif len(coordinates) == 6:
                p = Point(float(coordinates[0]), float(coordinates[1]), float(coordinates[2]), id=i)
                normal = [float(coordinates[3]), float(coordinates[4]), float(coordinates[5])]
                p.normal = normal
                points.append(p)

            else:
                continue

        f.close()

        # Sorting the points can lead to better seed triangle picking
        sorted_points = sorted(points, key=lambda p: (p.x, p.y, p.z))

        for i, p in enumerate(sorted_points):
            p.id = i

        return sorted_points

    @staticmethod
    def dist_between_point_and_edge(points: List, p1: Point, p2: Point) -> list:
        
        dists_p1 = [round(helper.calc_distance_points(p1, p3), 2) for p3 in points]
        dists_p2 = [round(helper.calc_distance_points(p2, p3), 2) for p3 in points]
        dists = [round(dists_p1[i] + dists_p2[i], 2) for i in range(len(dists_p1))]
        return dists

    @staticmethod
    def get_third_point_of_triangle(triangle_edges: List, p1: Point, p2: Point) -> Point:
        """
        Given a triangle's edges, and 2 of the points of the triangle, find the thirds point.
        """
        triangle_points = []
        third_point = None

        for triangle_edge in triangle_edges:
            first_point, second_point = triangle_edge.p1, triangle_edge.p2
            triangle_points.append(first_point)
            triangle_points.append(second_point)

        triangle_points = set(triangle_points)

        for point in triangle_points:
            if point.id != p1.id and point.id != p2.id:
                third_point = point
                break

        return third_point

    @staticmethod
    def will_triangles_overlap(edge: Edge, p3: Point, p4: Point) -> bool:
        """
        Check if a triangle defined by the 2 points of "edge" and a point p3, will overlap  a triangle defined by
        2 points of "edge" and a point p4.

        :return: Boolean.
        """
        p1, p2 = edge.p1, edge.p2

        # The following section checks if p3 is the same side of the edge as the third point of the rectangle
        # we are expanding. If so - keep searching, so we won't have overlapping triangles in the mesh.
        # Calculate the normal of the triangle
        v1 = [p3.x - p1.x, p3.y - p1.y, p3.z - p1.z]
        v2 = [p2.x - p1.x, p2.y - p1.y, p2.z - p1.z]
        triangle_normal = np.cross(v1, v2)

        # Calculate the normal to the plane defined by v2 and the triangle_normal (the plane orthogonal to
        # the triangle).
        plane_normal = np.cross(v2, triangle_normal)

        # Check if p3 is in the same side of the plane as the third point.
        v3 = [p4.x - p1.x, p4.y - p1.y, p4.z - p1.z]

        return np.sign(np.dot(plane_normal, v1)) == np.sign(np.dot(plane_normal, v3))
    def find_triangles_by_edge(self, edge: Edge) -> List:
        """
        Find all triangles the edge is in them.
        """
        possible_triangles = []

        for triangle in self.grid.triangles:
            if edge.p1 in triangle and edge.p2 in triangle:
                third_point = [p for p in triangle if p.id != edge.p1.id and p.id != edge.p2.id]

                if len(third_point) > 0:
                    third_point = third_point[0]
                    possible_triangles.append([edge.p1, edge.p2, third_point])

        return possible_triangles

    def check_a_path_between_two_points(self, p1, p2, point_of_triangle_we_creating):
        """
        Check if there is a path between two gicen points.

        :param p1: First point we check.
        :param p2: Second point we check.
        :param point_of_triangle_we_creating: Third point of a triangle these 2 points are in.
        :return:
        """
        edges_first_point_int = []
        edges_second_point_int = []
        points_first_edges = []
        points_second_edges = []

        for e in self.grid.edges:
            if p1.id == e.p1.id or p1.id == e.p2.id:
                edges_first_point_int.append(e)

            if p2.id == e.p1.id or p2.id == e.p2.id:
                edges_second_point_int.append(e)

        for e in edges_first_point_int:
            points_first_edges.append(e.p1.id)
            points_first_edges.append(e.p2.id)

        for e in edges_second_point_int:
            points_second_edges.append(e.p1.id)
            points_second_edges.append(e.p2.id)

        points_first_edges = set(points_first_edges)

        if p1.id in points_first_edges:
            points_first_edges.remove(p1.id)

        points_second_edges = set(points_second_edges)

        if p2.id in points_second_edges:
            points_second_edges.remove(p2.id)

        intersection = set(points_first_edges & points_second_edges)
        if point_of_triangle_we_creating.id in intersection:
            intersection.remove(point_of_triangle_we_creating.id)

        return len(intersection) > 0


    def find_seed_triangle(self, first_point_index=0, num_recursion_calls=0) -> tuple[int, tuple]:
        """
        Find seed triangle.
        """
        #Produces an error to break the iteration loop so that it doesn't iterate inifinitly
        if num_recursion_calls > len(self.points):
            return -1, -1, -1 

        if first_point_index >= len(self.points) - 1:
            first_point_index = 0

        p1 = self.points[first_point_index] #get a point that is not used
        p1_neighbor_points = []

        # Find all points in 2r distance from the point that was initially chosen.
        for cell in p1.neighbor_nodes:
            p1_neighbor_points.extend(self.grid.get_cell_points(cell))

        p1_neighbor_points = set(p1_neighbor_points)

        # Sort points by distance from p1.
        dists = [helper.calc_distance_points(p1, p2) for p2 in p1_neighbor_points]
        p1_neighbor_points = [x for _, x in sorted(zip(dists, p1_neighbor_points))]
        #reduce the neighbour points to 6.
        point_limit = 6
        p1_neighbor_points = p1_neighbor_points[:point_limit]

        # For each other point, find all points that are in 2r distance from that other point.
        for p2 in p1_neighbor_points:
            if p2.is_used:
                pass
            if p2.x == p1.x and p2.y == p1.y and p2.z == p1.z:
                continue

            # Find all points that are on 2r distance from p1 and p2
            intersect_cells = list(set(p1.neighbor_nodes) & set(p2.neighbor_nodes))
            possible_points = []

            for cell in intersect_cells:
                possible_points.extend(self.grid.get_cell_points(cell))

            # Sort points by distance from second point p2.
            dists_p2 = [helper.calc_distance_points(p2, p3) for p3 in possible_points]
            dist_p1 = [helper.calc_distance_points(p1, p3) for p3 in possible_points]
            dists = [dist_p1[i] + dists_p2[i] for i in range(len(dist_p1))]
            possible_points = [x for _, x in sorted(zip(dists, possible_points))] # put the possible points in the list
            point_limit = 5 #limit the number of neighbour points to 5
            possible_points = possible_points[:point_limit]

            for _, p3 in enumerate(possible_points):
                if p3.is_used:
                    pass

                if (p3.x == p1.x and p3.y == p1.y and p3.z == p1.z) or (p2.x == p3.x and p2.y == p3.y and p2.z == p3.z):
                    continue

                #checks the ball fits the triangle
                if self.radius <= helper.calc_incircle_radius(p1, p2, p3):
                    # Calculate triangle's normal.
                    v1 = [p2.x - p1.x, p2.y - p1.y, p2.z - p1.z]
                    v2 = [p3.x - p1.x, p3.y - p1.y, p3.z - p1.z]
                    triangle_normal = np.cross(v1, v2)

                    # Check if the normal of the triangle is on the same direction with points normals.
                    if np.dot(triangle_normal, p1.normal) < 0:
                        continue

                    # Check if two of the points are already connected.
                    p1_p3_already_connected = [e for e in self.grid.edges if ((e.p1.id == p1.id) and (e.p2.id == p3.id)) or ((e.p1.id == p3.id) and (e.p2.id == p1.id))]
                    p1_p2_already_connected = [e for e in self.grid.edges if ((e.p1.id == p1.id) and (e.p2.id == p2.id)) or ((e.p1.id == p2.id) and (e.p2.id == p1.id))]
                    p2_p3_already_connected = [e for e in self.grid.edges if ((e.p1.id == p2.id) and (e.p2.id == p3.id)) or ((e.p1.id == p3.id) and (e.p2.id == p2.id))]
                    e1,e2,e3 = None,None,None
                    
                    if len(p1_p3_already_connected) > 0 or len(p1_p2_already_connected) > 0 or len(p2_p3_already_connected) > 0:
                        continue

                    # Check if one of the new edges might close another triangle in the mesh.
                    p1_p3_closing_another_triangle_in_the_mesh = self.check_a_path_between_two_points(p1, p3, point_of_triangle_we_creating=p2)
                    p2_p3_closing_another_triangle_in_the_mesh = self.check_a_path_between_two_points(p2, p3, point_of_triangle_we_creating=p1)
                    p1_p2_closing_another_triangle_in_the_mesh = self.check_a_path_between_two_points(p1, p2, point_of_triangle_we_creating=p3)

                    if e1 is None:
                        e1 = Edge(p1, p3)
                        e1.num_triangles_this_edge_is_in += 1

                        if p1_p3_closing_another_triangle_in_the_mesh:
                            e1.num_triangles_this_edge_is_in += 1

                    if e2 is None:
                        e2 = Edge(p1, p2)
                        e2.num_triangles_this_edge_is_in += 1

                        if p1_p2_closing_another_triangle_in_the_mesh:
                            e2.num_triangles_this_edge_is_in += 1

                    if e3 is None:
                        e3 = Edge(p2, p3)
                        e3.num_triangles_this_edge_is_in += 1

                        if p2_p3_closing_another_triangle_in_the_mesh:
                            e3.num_triangles_this_edge_is_in += 1

                    self.grid.edges.append(e1)
                    self.grid.edges.append(e2)
                    self.grid.edges.append(e3)

                    triangle = sorted(list({e1.p1, e1.p2, e2.p1, e2.p2, e3.p1, e3.p2}))
                    self.grid.triangles.append(triangle)

                    # Move the points to the end of the list.
                    self.first_free_point_index += 1
                    # update the status of the seed triangle points so that they won't be used for 
                    p1.is_used = True
                    p2.is_used = True
                    p3.is_used = True

                    return 1, (e1, e2, e3), first_point_index

        # Else, find another free point and start over.
        return self.find_seed_triangle(first_point_index=first_point_index+1, num_recursion_calls=num_recursion_calls+1)

    def expand_triangle(self, edge: Edge, triangle_edges: List[Edge]) -> tuple[Edge, Edge]:
        """
        Tuple of two edges of the new formed triangle.
        """
        if edge.num_triangles_this_edge_is_in < 2:
            # Avoid duplications.
            intersect_cells = list(set(edge.p1.neighbor_nodes) & set(edge.p2.neighbor_nodes))
            possible_points = []

            p1, p2 = edge.p1, edge.p2
            third_point_of_triangle_for_expantion = self.get_third_point_of_triangle(triangle_edges, p1, p2)

            for cell in intersect_cells:
                possible_points.extend(self.grid.get_cell_points(cell))

            # Sort points by distance from p1 and p2.
            dists = self.dist_between_point_and_edge(possible_points, p1, p2)
            sorted_possible_points = [x for _, x in sorted(zip(dists, possible_points))]
            point_limit = 5
            sorted_possible_points = sorted_possible_points[:point_limit]

            for _, p3 in enumerate(sorted_possible_points):
                if p3.id == p1.id or p3.id == p2.id or p3.id == third_point_of_triangle_for_expantion.id:
                    continue

                if self.will_triangles_overlap(edge, third_point_of_triangle_for_expantion, p3):
                    continue

                
                t = helper.calc_incircle_radius(p1, p2, p3)
                if self.radius <= t:
                    # Calculate new triangle's normal.
                    v1 = [p2.x - p1.x, p2.y - p1.y, p2.z - p1.z]
                    v2 = [p3.x - p1.x, p3.y - p1.y, p3.z - p1.z]
                    new_triangle_normal = np.cross(v1, v2)

                    # Check if the normal of the triangle is on the same direction with other points normals.
                    if np.dot(new_triangle_normal, p1.normal) < 0 and np.dot(new_triangle_normal, p2.normal) < 0:
                        pass

                    e1 = None
                    e2 = None

                    p1_and_p3_already_connected = [e for e in self.grid.edges if ((e.p1.id == p1.id) and (e.p2.id == p3.id)) or ((e.p1.id == p3.id) and (e.p2.id == p1.id))]
                    p2_and_p3_already_connected = [e for e in self.grid.edges if ((e.p1.id == p2.id) and (e.p2.id == p3.id)) or ((e.p1.id == p3.id) and (e.p2.id == p2.id))]

                    # These points are already part of a triangle!
                    if len(p1_and_p3_already_connected) and len(p2_and_p3_already_connected):
                        continue

                    if len(p1_and_p3_already_connected) > 0:
                        # Find the single edge they are connected with.
                        e1 = p1_and_p3_already_connected[0]

                        if e1.num_triangles_this_edge_is_in >= 2:
                            continue

                        # Make sure that if the edge they are already connected with is part of the triangle, the new
                        # triangle will not overlap
                        triangles = self.find_triangles_by_edge(e1)

                        if len(triangles) >= 2:
                            continue
                        else:
                            third_point_of_triangle = [p for p in triangles[0] if p.id != p1.id and p.id != p3.id][0]

                            if self.will_triangles_overlap(e1, third_point_of_triangle, p2):
                                continue

                        e1.num_triangles_this_edge_is_in += 1

                    if len(p2_and_p3_already_connected) > 0:
                        # Find the single edge they are connected with.
                        e2 = p2_and_p3_already_connected[0]

                        if e2.num_triangles_this_edge_is_in >= 2:
                            continue

                        # Make sure that if the edge they are already connected with is part of the triangle, the new
                        # triangle will not overlap
                        triangles = self.find_triangles_by_edge(e2)

                        if len(triangles) >= 2:
                            continue
                        else:
                            third_point_of_triangle = [p for p in triangles[0] if p.id != p1.id and p.id != p3.id][0]
                            if self.will_triangles_overlap(e2, third_point_of_triangle, p1):
                                continue

                        e2.num_triangles_this_edge_is_in += 1

                    # Check if one of the new edges might close another triangle in the mesh.
                    p1_p3_closing_another_triangle_in_the_mesh = False
                    p2_p3_closing_another_triangle_in_the_mesh = False

                    if p3.is_used:
                        p1_p3_closing_another_triangle_in_the_mesh = self.check_a_path_between_two_points(p1, p3, p2)
                        p2_p3_closing_another_triangle_in_the_mesh = self.check_a_path_between_two_points(p2, p3, p1)

                    # Update that the edge that is expanded is now part of the triangle.
                    edge.num_triangles_this_edge_is_in += 1

                    # If Update that 'point' is not free anymore, we update the point status to True .
                    p3.is_used = True

                    if e1 is None:
                        e1 = Edge(p1, p3)
                        e1.num_triangles_this_edge_is_in += 1

                        if p1_p3_closing_another_triangle_in_the_mesh:
                            e1.num_triangles_this_edge_is_in += 1

                    if e2 is None:
                        e2 = Edge(p2, p3)
                        e2.num_triangles_this_edge_is_in += 1

                        if p2_p3_closing_another_triangle_in_the_mesh:
                            e2.num_triangles_this_edge_is_in += 1

                    self.grid.add_edge(e1)
                    self.grid.add_edge(e2)

                    triangle = sorted(list({e1.p1, e1.p2, e2.p1, e2.p2,edge.p1, edge.p2}))

                    v1 = [p2.x - p1.x, p2.y - p1.y, p2.z - p1.z]
                    v2 = [p3.x - p1.x, p3.y - p1.y, p3.z - p1.z]
                    normal = np.cross(v1, v2)

                    if np.sign(np.dot(normal, p1.normal)) < 0:
                        triangle.reverse() #reverse the orientation

                    self.grid.triangles.append(triangle)
                    return e1, e2
            else:
                return None, None

        return None, None

    def generate_mesh(self, limit_iterations: int = np.inf,first_point_index: int = 0):
        expansion_counter = 0
        facets = []

        while 1 and expansion_counter < limit_iterations:
            # Find a seed triangle.
            _, edges, last_point_index = self.find_seed_triangle(first_point_index=first_point_index)
            first_point_index = last_point_index

            if edges == None or edges == -1:
                return facets


            expansion_counter += 1
            i = 0

            # Try to expand from each edge.
            while i < len(edges) and expansion_counter < limit_iterations:
                e1, e2 = self.expand_triangle(edges[i], edges)
                
                expansion_counter += 1

                if e1 != None and e2 != None:
                    edges = [e1, e2]
                    mesh_triangle=Triangle(e1.p1,e1.p2,e2.p1)
                    i = 0
                    
                    facets.append(mesh_triangle)

                else:
                    i += 1

        return facets

