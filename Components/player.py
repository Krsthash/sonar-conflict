import math


class Player:
    def __init__(self, x, y, azimuth, pitch):
        self.x = x
        self.y = y
        self.azimuth = azimuth
        self.pitch = pitch
        self.depth = 0
        self.health = 100
        self.ballast = 50
        self.velocity = 0
        self.acceleration = 0
        self.gear = 0
        self.detection_chance = 0.04

    def change_gear(self, direction):
        """
        Changes the gear in the appropriate direction.
        """
        if (direction == 1 and self.gear != 3) or (direction == -1 and self.gear != -3):
            self.gear += direction
        if self.gear == 1:
            self.detection_chance = 0.1
        elif self.gear == 2:
            self.detection_chance = 0.3
        elif self.gear == 3:
            self.detection_chance = 0.5
        elif self.gear == 0:
            self.detection_chance = 0.04
        elif self.gear == -1:
            self.detection_chance = 0.1
        elif self.gear == -2:
            self.detection_chance = 0.3
        elif self.gear == -3:
            self.detection_chance = 0.5

    def calculate_movement(self, fps_d):
        water_drag = 0.00001
        if self.gear == 1:
            self.acceleration = 0.000014
            if self.velocity >= 0.008:
                self.acceleration -= (self.velocity - 0.008) / 200
        elif self.gear == 2:
            self.acceleration = 0.000018
            if self.velocity >= 0.014:
                self.acceleration -= (self.velocity - 0.014) / 200
        elif self.gear == 3:
            self.acceleration = 0.00002
            if self.velocity >= 0.018:
                self.acceleration -= (self.velocity - 0.018) / 200
        elif self.gear == 0:
            self.acceleration = 0
        elif self.gear == -1:
            self.acceleration = -0.000014
            if self.velocity <= -0.008:
                self.acceleration += (abs(self.velocity + 0.008)) / 200
        elif self.gear == -2:
            self.acceleration = -0.000018
            if self.velocity <= -0.014:
                self.acceleration += (abs(self.velocity + 0.014)) / 200
        elif self.gear == -3:
            self.acceleration = -0.00002
            if self.velocity <= -0.018:
                self.acceleration += (abs(self.velocity + 0.018)) / 200

        self.velocity += self.acceleration

        # Slowing down from water drag
        if self.velocity - water_drag >= 0:
            self.velocity -= water_drag
        elif self.velocity + water_drag <= 0:
            self.velocity += water_drag
        else:
            self.velocity = 0

        self.x += (self.velocity * fps_d) * math.cos(
            math.radians(self.azimuth - 90))
        self.y += (self.velocity * fps_d) * math.sin(
            math.radians(self.azimuth - 90))

        if -1 < self.pitch < 1:
            pitch = 0
        else:
            pitch = self.pitch
        self.depth -= (self.velocity * fps_d) * math.sin(math.radians(pitch)) * 1.2
        if 49 < self.ballast < 51:
            BALLAST = 50
        else:
            BALLAST = self.ballast
        self.depth += (BALLAST - 50) * 0.0005 * fps_d
        if self.depth < 0:
            self.depth = 0
        elif self.depth >= 700:
            self.depth = 700
