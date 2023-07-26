class Decoy:
    def __init__(self, x, y, azimuth, depth, destination_x, destination_y, destination_depth, time, mode):
        self.mode = mode
        self.time = time
        self.destination_depth = destination_depth
        self.destination_y = destination_y
        self.destination_x = destination_x
        self.depth = depth
        self.azimuth = azimuth
        self.y = y
        self.x = x
