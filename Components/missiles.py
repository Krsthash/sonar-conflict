class LAM:
    def __init__(self, time, hit_status, hit_target, message, weapon_name, destruction):
        self.destruction = destruction
        self.weapon_name = weapon_name
        self.message = message
        self.hit_target = hit_target
        self.hit_status = hit_status
        self.time = time


class ASM:
    def __init__(self, time, impact_x, impact_y, message, weapon_name, destruction, sensor_range):
        self.impact_y = impact_y
        self.impact_x = impact_x
        self.sensor_range = sensor_range
        self.destruction = destruction
        self.weapon_name = weapon_name
        self.message = message
        self.time = time
