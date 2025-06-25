import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from Holefilling import Multiple_Pass

def plot_mesh(vertices, faces, title):
    """
    Plots the 3D mesh using the vertices and faces.
    """
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    for f in faces:
        face_vertices = vertices[f]
        poly = Poly3DCollection([face_vertices], alpha=0.7, edgecolor='k',facecolor = 'yellow')
        ax.add_collection3d(poly)

    ax.set_xlim(vertices[:, 0].min(), vertices[:, 0].max())
    ax.set_ylim(vertices[:, 1].min(), vertices[:, 1].max())
    ax.set_zlim(vertices[:, 2].min(), vertices[:, 2].max())
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title(title)
    plt.show()


def triangles_to_numpy(triangles):
    """
    Converts BPA triangle output to a consistent NumPy array of vertices and faces.
    """
    vertices = []
    faces = []
    v2index = {}
    index_counter = 0

    for triangle_tuple in triangles:
        face_indices = []
        for vertex in triangle_tuple:
            if vertex not in v2index:
                v2index[vertex] = index_counter
                vertices.append(vertex)
                index_counter += 1
            face_indices.append(v2index[vertex])
        faces.append(face_indices)

    vertices = np.array(vertices)
    faces = np.array(faces)
    return vertices, faces


#radii = [0.01,0.009,0.008,0.007,0.0009,0.0005] # sphere
#radii = np.arange(0.0001, 0.004, 0.0001).tolist()# bunny
radii = [0.005]
path='sphere_point_cloud_with_500_even_normals.txt'

final_triangle = Multiple_Pass(radii,path,2250) #this works for single radius as well but the radius should be in a list

vertices,faces = triangles_to_numpy(final_triangle)

# Plot the final combined mesh
plot_mesh(vertices, faces, "Final 3D Mesh")
