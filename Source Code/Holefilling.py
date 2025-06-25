from ball_pivoting_algo import BPA
import time
def triangle_to_tuple(triangle):
    """
    Converts a triangle object into a hashable tuple representation.
    """
    return tuple(sorted((vertex.x, vertex.y, vertex.z) for vertex in triangle.vertices))
def Multiple_Pass(radii,input_path,limit):
    combined_triangles = set()
    #In this section the hole filling algorithm is implemeted
    for i, radius in enumerate(radii):
        start = time.time()
        if not isinstance(input_path, str):
            raise TypeError(f"Invalid path type: expected str, got {type(input_path)}")
        bpa = BPA(path= input_path, radius=radius)
        new_triangles = bpa.generate_mesh(limit_iterations=limit)#16600
        end = time.time()

        print(f"Radius of pivoting ball (iteration {i+1}): {radius}")
        print(f"Running time: {end - start:.2f} seconds")
        
        # Insert unique triangles
        for triangle in new_triangles:
            triangle_tuple = triangle_to_tuple(triangle)
            if triangle_tuple not in combined_triangles:
                combined_triangles.add(triangle_tuple)
    return combined_triangles