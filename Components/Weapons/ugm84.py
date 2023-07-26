import math

from Components.utilities import random_int
from Components.missiles import ASM


class Ugm84:
    def __init__(self):
        self.designation = 'UGM-84'
        self.sensor_range = 16
        self.speed = 1.92
        self.range = 45

    def launch(self, player, bearing, distance):
        if distance > self.range:
            time = self.range / self.speed
        else:
            time = distance / self.speed
        angle = player.azimuth + bearing
        if angle > 360:
            angle -= 360
        impact_x = player.x - distance * math.cos(math.radians(angle + 90))
        impact_y = player.y - distance * math.sin(math.radians(angle + 90))
        # Anti missile defence
        if random_int(0, 10) < 1:
            destruction = 0
            # log.debug("Defense system defeated the missile.")
        else:
            destruction = random_int(40, 60)
        if distance > self.range:
            message = 'Out of fuel!'
        else:
            message = 'Target missed!'
        return ASM(time, impact_x, impact_y, message, self.designation, destruction, self.sensor_range)