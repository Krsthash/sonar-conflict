import math

from Components.utilities import random_int
from Components.missiles import LAM


class Kalibr:
    def __init__(self):
        self.designation = '3M54-1 Kalibr'
        self.speed = 3.5
        self.range = 150

    def launch(self, player, bearing, distance, targets):
        if distance > self.range:
            time = self.range / self.speed
        else:
            time = distance / self.speed
        # VLS launch
        angle = player.azimuth + bearing
        if angle > 360:
            angle -= 360
        impact_x = player.x - distance * math.cos(math.radians(angle + 90))
        impact_y = player.y - distance * math.sin(math.radians(angle + 90))
        # log.debug(f"LAM Impact: ({impact_x}, {impact_y}) Distance: {distance}km.")
        flag = None
        for target in targets:
            if target[0] - 10 < impact_x < target[0] + 10 and \
                    target[1] - 10 < impact_y < target[1] + 10:
                flag = target
                # log.debug(f"Hit target at: {target[0]}, {target[1]}")

        destruction = random_int(25, 50)
        # log.debug(f"Destruction: {destruction}")

        if distance > self.range:
            flag = None
            # log.debug(f"Impact point out of self.range. Distance: {distance} self.range: {self.range}")
            return LAM(time, True, flag, 'Ran out of fuel!', self.designation, destruction)
        elif flag:
            return LAM(time, True, flag, 'Target hit!', self.designation, destruction)
        else:
            return LAM(time, False, flag, 'Target missed!', self.designation, destruction)