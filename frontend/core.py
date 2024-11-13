import numpy as np
from scipy.spatial import KDTree


class PointSystem:
    def __init__(self, points: np.ndarray, r1: float, r2: float):
        self.__points = points.copy()
        self.states = np.zeros(len(points), dtype=int)  # Initial states set to 0
        self.r1 = r1
        self.r2 = r2
        self.tree = KDTree(self.__points)  # Use KDTree for efficient neighbor search

    def update_states(self):
        # For each point, check neighbors within distance r1 and r2
        for i, point in enumerate(self.__points):
            neighbors_r1 = self.tree.query_ball_point(point, self.r1)
            neighbors_r2 = self.tree.query_ball_point(point, self.r2)

            # Update state to 1 if within r1 distance
            for neighbor in neighbors_r1:
                if neighbor != i:
                    self.states[neighbor] = 1

            # Probabilistic update to state 3 if within r2 distance
            for neighbor in neighbors_r2:
                if neighbor != i and np.random.rand() < 1 / (self.r2**2):
                    self.states[neighbor] = 3

    def apply_deltas(self, deltas: np.ndarray):
        # Update positions and rebuild KDTree for efficient lookup
        self.__points += deltas  # Apply deltas to each point
        self.tree = KDTree(self.__points)  # Rebuild KDTree for updated positions
        self.update_states()  # Update states after movement

    @property
    def points(self):
        return self.__points

    @points.setter
    def points(self, value: np.ndarray):
        self.__points = value
        self.tree = KDTree(self.__points)


if __name__ == "__main__":
    # Example usage
    points = np.array(
        [(1.0, 2.0), (3.5, 4.5), (6.0, 1.5)]
    )  # Example list of (x, y) tuples
    r1 = 1.0  # Distance for state 1
    r2 = 2.5  # Distance for state 3 interaction probability

    system = PointSystem(points, r1, r2)
    deltas = np.array(
        [(0.1, -0.2), (0.0, 0.1), (-0.1, 0.3)]
    )  # Example deltas for point updates

    # Apply the update loop
    system.apply_deltas(deltas)  # Update states based on new positions

    print(system.states)  # Check updated states of points
