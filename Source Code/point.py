import numpy as np
import helper
from typing import List

class Point:
    def __init__(self, x, y, z, id, normal=None):
        self.z = np.float32(z)
        self.y = np.float32(y)
        self.x = np.float32(x)
        self.cell_code = None
        self.normal = normal
        self.id = id
        self.is_used = False

    def __lt__(self, other):
        return self.z <= other.z

    @property
    def neighbor_nodes(self) -> List:
        neighbor_nodes = [self.cell_code]

        # Find the point's cell.
        x, y, z = helper.decode_cell(self.cell_code)
        for i in range(-1, 2):
            for j in range(-1, 2):
                for k in range(-1, 2):
                    corner_of_cell = x + i, y + j, z + k

                    if corner_of_cell [0] < 0 or corner_of_cell [1] < 0 or corner_of_cell[2] < 0:
                        continue

                    cell_code = helper.encode_cell(corner_of_cell [0], corner_of_cell [1], corner_of_cell[2])
                    neighbor_nodes.append(cell_code)

        return neighbor_nodes




