import math

from Components.decoy import Decoy
from Components.utilities import calculate_azimuth, random_int

DETECTED_TORPEDOES = {}
TORPEDO_SINK_QUEUE = []
TORPEDO_DAMAGE_QUEUE = []
TORPEDO_DECOY_QUEUE = []


class Torpedo:
    def __init__(self, x, y, azimuth, speed, depth, target_x, target_y, target_depth, sensor,
                 time, sender, ping_duration, mode):
        self.mode = mode
        self.ping_duration = ping_duration
        self.sender = sender
        self.time = time
        self.sensor = sensor
        self.target_depth = target_depth
        self.target_y = target_y
        self.target_x = target_x
        self.depth = depth
        self.speed = speed
        self.azimuth = azimuth
        self.y = y
        self.x = x

    def logic_calculation(self, key, fps_d, player, objects, decoys):
        max_distance = 10
        if self.mode:
            max_distance = 20
        rel_x = player.x - self.x
        rel_y = player.y - self.y
        distance = math.sqrt(rel_x * rel_x + rel_y * rel_y)
        if self.mode and distance <= 150:  # If torpedo is in the active mode
            if self.ping_duration <= 1:
                self.ping_duration = 2
        self.time -= 0.0167 * fps_d
        if self.time <= 0:
            # self.TORPEDOES.pop(key)
            return -1
        if not self.sensor:  # Sensor hasn't been activated yet
            rel_x = self.target_x - self.x
            rel_y = self.target_y - self.y
            distance = math.sqrt(rel_x * rel_x + rel_y * rel_y)
            angle = calculate_azimuth(rel_x, rel_y, distance)
            if self.azimuth - angle > 180:
                angle = (360 - self.azimuth) + angle
            elif self.azimuth - angle < -180:
                angle = -((360 - angle) + self.azimuth)
            else:
                angle = -(self.azimuth - angle)
            turn = 0.34 * fps_d
            if turn > abs(angle):
                turn = abs(angle)
            if angle > 0:
                self.azimuth += turn
            else:
                self.azimuth -= turn
            dive_rate = 0.24 * fps_d
            depth = self.target_depth - self.depth
            if dive_rate > depth:
                dive_rate = depth
            if depth > 0:
                self.depth += dive_rate
            else:
                self.depth -= dive_rate
            # print(f"Depth to destination: {depth} Distance: {distance}")
            self.x += (self.speed * fps_d) * math.cos(
                math.radians(self.azimuth - 90))
            self.y += (self.speed * fps_d) * math.sin(
                math.radians(self.azimuth - 90))
            if -10 < distance < 10 and -30 < depth < 30:
                self.sensor = True
        else:
            # Go into seeking mode
            min_distance = [None, None]
            for ship in objects:
                if ship.count('Friendly_ship'):
                    rel_x = objects[ship].x - self.x
                    rel_y = objects[ship].y - self.y
                    distance = math.sqrt(rel_x * rel_x + rel_y * rel_y)
                    if not min_distance[0]:
                        min_distance[0] = distance
                        min_distance[1] = ship
                    if min_distance[0] > distance:
                        min_distance[0] = distance
                        min_distance[1] = ship
            for decoy in decoys:
                rel_x = decoy.x - self.x
                rel_y = decoy.y - self.y
                distance = math.sqrt(rel_x * rel_x + rel_y * rel_y)
                if decoy.mode and not self.mode:
                    # loop_log.debug("Sonar decoy filtered out due to its active mode.")
                    continue  # If the decoy is active and the torpedo is passive, ignore it.
                elif decoy.mode and self.mode and distance <= 10:
                    # loop_log.debug("Torpedo is being confused by active sonar decoy!")
                    max_distance -= 12  # If both are active and close, lowers the max detection distance.
                if not min_distance[0]:
                    min_distance[0] = distance
                    min_distance[1] = decoy
                if min_distance[0] > distance:
                    min_distance[0] = distance
                    min_distance[1] = decoy
            rel_x = player.x - self.x
            rel_y = player.y - self.y
            distance = math.sqrt(rel_x * rel_x + rel_y * rel_y)
            if not min_distance[0]:
                min_distance[0] = distance
                min_distance[1] = 'Player'
            if min_distance[0] > distance:
                min_distance[0] = distance
                min_distance[1] = 'Player'
            if min_distance[1] == 'Player':
                rel_x = player.x - self.x
                rel_y = player.y - self.y
                distance = math.sqrt(rel_x * rel_x + rel_y * rel_y)
                angle = calculate_azimuth(rel_x, rel_y, distance)
                if self.azimuth - angle > 180:
                    angle = (360 - self.azimuth) + angle
                elif self.azimuth - angle < -180:
                    angle = -((360 - angle) + self.azimuth)
                else:
                    angle = -(self.azimuth - angle)
                depth = player.depth - self.depth
                if distance < max_distance and 150 > angle > -150 and -40 < depth < 40:
                    turn = 0.34 * fps_d
                    if turn > abs(angle):
                        turn = abs(angle)
                    if angle > 0:
                        self.azimuth += turn
                    else:
                        self.azimuth -= turn
                    dive_rate = 0.08 * fps_d
                    if dive_rate > depth:
                        dive_rate = depth
                    if depth > 0:
                        self.depth += dive_rate
                    else:
                        self.depth -= dive_rate
                    # print(f"Depth to target: {depth} Distance: {distance}")
                    # Updating torpedo's position
                    self.x += (self.speed * fps_d) * math.cos(
                        math.radians(self.azimuth - 90))
                    self.y += (self.speed * fps_d) * math.sin(
                        math.radians(self.azimuth - 90))
                    if -0.5 < distance < 0.5 and -0.2 < depth < 0.2:
                        TORPEDO_DAMAGE_QUEUE.append([player, random_int(30, 50)])
                        return -2
                else:
                    # Updating torpedo's position
                    self.x += (self.speed * fps_d) * math.cos(
                        math.radians(self.azimuth - 90))
                    self.y += (self.speed * fps_d) * math.sin(
                        math.radians(self.azimuth - 90))
                    return 0
            elif min_distance[1] in list(objects.keys()):
                rel_x = objects[min_distance[1]].x - self.x
                rel_y = objects[min_distance[1]].y - self.y
                distance = math.sqrt(rel_x * rel_x + rel_y * rel_y)
                angle = calculate_azimuth(rel_x, rel_y, distance)
                if self.azimuth - angle > 180:
                    angle = (360 - self.azimuth) + angle
                elif self.azimuth - angle < -180:
                    angle = -((360 - angle) + self.azimuth)
                else:
                    angle = -(self.azimuth - angle)
                depth = objects[min_distance[1]].depth - self.depth
                if self.mode and distance <= 60:
                    DETECTED_TORPEDOES[key] = [distance, min_distance[1], angle]
                if distance < max_distance and 120 > angle > -120 and -50 < depth < 50:
                    turn = 0.34 * fps_d
                    if turn > abs(angle):
                        turn = abs(angle)
                    if angle > 0:
                        self.azimuth += turn
                    else:
                        self.azimuth -= turn
                    dive_rate = 0.1 * fps_d
                    if dive_rate > depth:
                        dive_rate = depth
                    if depth > 0:
                        self.depth += dive_rate
                    else:
                        self.depth -= dive_rate
                    # Updating torpedo's position
                    self.x += (self.speed * fps_d) * math.cos(
                        math.radians(self.azimuth - 90))
                    self.y += (self.speed * fps_d) * math.sin(
                        math.radians(self.azimuth - 90))
                    if -1 < distance < 1 and -1 < depth < 1:
                        if objects[min_distance[1]].health <= 0:
                            TORPEDO_SINK_QUEUE.append(min_distance[1])
                            return -1
                        else:
                            TORPEDO_DAMAGE_QUEUE.append([min_distance[1], random_int(30, 50)])
                else:
                    # Updating torpedo's position
                    self.x += (self.speed * fps_d) * math.cos(
                        math.radians(self.azimuth - 90))
                    self.y += (self.speed * fps_d) * math.sin(
                        math.radians(self.azimuth - 90))
            elif isinstance(min_distance[1], Decoy):
                rel_x = min_distance[1].x - self.x
                rel_y = min_distance[1].y - self.y
                distance = math.sqrt(rel_x * rel_x + rel_y * rel_y)
                angle = calculate_azimuth(rel_x, rel_y, distance)
                if self.azimuth - angle > 180:
                    angle = (360 - self.azimuth) + angle
                elif self.azimuth - angle < -180:
                    angle = -((360 - angle) + self.azimuth)
                else:
                    angle = -(self.azimuth - angle)
                depth = min_distance[1].depth - self.depth
                max_distance = 10
                if distance < max_distance and 120 > angle > -120 and -50 < depth < 50:
                    turn = 0.34 * fps_d
                    if turn > abs(angle):
                        turn = abs(angle)
                    if angle > 0:
                        self.azimuth += turn
                    else:
                        self.azimuth -= turn
                    dive_rate = 0.1 * fps_d
                    if dive_rate > depth:
                        dive_rate = depth
                    if depth > 0:
                        self.depth += dive_rate
                    else:
                        self.depth -= dive_rate
                    # Updating torpedo's position
                    self.x += (self.speed * fps_d) * math.cos(
                        math.radians(self.azimuth - 90))
                    self.y += (self.speed * fps_d) * math.sin(
                        math.radians(self.azimuth - 90))
                    if -1 < distance < 1 and -1 < depth < 1:
                        TORPEDO_DECOY_QUEUE.append(min_distance[1])
                        # log.info("Torpedo hit a sonar decoy!")
                else:
                    # Updating torpedo's position
                    self.x += (self.speed * fps_d) * math.cos(
                        math.radians(self.azimuth - 90))
                    self.y += (self.speed * fps_d) * math.sin(
                        math.radians(self.azimuth - 90))
