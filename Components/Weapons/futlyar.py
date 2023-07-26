import math


class Futlyar:
    def __init__(self):
        self.designation = 'Futlyar'
        self.speed = 0.0367
        self.range = 35

    def launch(self, player, bearing, distance, mode, depth, id):
        angle = player.azimuth + bearing
        if angle > 360:
            angle -= 360
        time = self.range / (self.speed * 60)
        impact_x = player.x - distance * math.cos(math.radians(angle + 90))
        impact_y = player.y - distance * math.sin(math.radians(angle + 90))
        return [[player.x, player.y, player.azimuth, self.speed, player.depth], [impact_x, impact_y, depth], False,
                time, 'Enemy', 0, mode, id]
