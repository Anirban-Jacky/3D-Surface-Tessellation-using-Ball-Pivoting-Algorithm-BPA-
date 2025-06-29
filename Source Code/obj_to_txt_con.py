import numpy as np
from point import Point

"""
Models are taken from here: https://github.com/alecjacobson/common-3d-test-models
"""

if __name__ == "__main__":
    f = open("fandisk.obj")
    lines = f.readlines()
    f.close()

    points = []
    points_and_normals = {}
    facets = []
    normals = []

    for line in lines:
        splitted = line.strip().split(" ")
        if len(splitted) >= 4:
            if splitted[0] == 'v':  # Parse vertex lines
                p = Point(x=float(splitted[1]), y=float(splitted[2]), z=float(splitted[3]), id=1)
                points.append(p)
            elif splitted[0] == 'f':  # Parse facet lines
                try:
                    # Extract only vertex indices before the '/' character
                    vertex_indices = [int(part.split('/')[0]) for part in splitted[1:4]]
                    p = Point(x=vertex_indices[0], y=vertex_indices[1], z=vertex_indices[2], id=1)
                    facets.append(p)
                except ValueError:
                    print(f"Malformed facet line: {line}")

    for facet in facets:
        p1 = points[int(facet.x)-1]
        p2 = points[int(facet.y)-1]
        p3 = points[int(facet.z)-1]

        v1 = [p2.x - p1.x, p2.y - p1.y, p2.z - p1.z]
        v2 = [p3.x - p1.x, p3.y - p1.y, p3.z - p1.z]
        normal = np.cross(v1, v2)
        normal = normal / np.linalg.norm(normal)

        if p1 not in points_and_normals.keys():
            points_and_normals[p1] = normal
        if p2 not in points_and_normals.keys():
            points_and_normals[p2] = normal
        if p3 not in points_and_normals.keys():
            points_and_normals[p3] = normal

    f = open("fandisk.txt", 'w')

    for k, v in points_and_normals.items():
        f.write(str(k.x) + " " + str(k.y) + " " + str(k.z) + " " + str(v[0]) + " " + str(v[1]) + " " + str(v[2]) + "\n")

    f.close()