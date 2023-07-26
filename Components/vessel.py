import math


class Vessel:
    def __init__(self, x, y, azimuth, depth, obj_type, detection_chance, velocity=0):
        self.velocity = velocity
        self.detection_chance = detection_chance
        self.obj_type = obj_type
        self.depth = depth
        self.azimuth = azimuth
        self.y = y
        self.x = x
        self.health = 100
        self.active_sonar = -25

    def movement_simulation(self, fps_d):
        if self.velocity != 0:
            self.x += (self.velocity * fps_d) * math.cos(
                math.radians(self.azimuth - 90))
            self.y += (self.velocity * fps_d) * math.sin(
                math.radians(self.azimuth - 90))
