class Edge:
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        self.num_triangles_this_edge_is_in = 0 # To avoid cases where algorithm tries to expand edges that are already
        # part of 2 different triangles.
        
class Triangle:
	def __init__(self, v1, v2, v3):
		self.v1 = v1
		self.v2 = v2
		self.v3 = v3
		self.vertices = [v1, v2, v3]

	def __eq__(self, other):
		vertices = [self.v1, self.v2, self.v3]
		return other.v1 in vertices and other.v2 in vertices and other.v3 in vertices