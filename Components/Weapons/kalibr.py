import math

from Components.missiles import LAM
from Components.utilities import random_int


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

    def render_description(self, font, x_size, window):
        txtsurf_ = font.render(f'Type: ', True, '#b6b6d1')
        window.blit(txtsurf_, (x_size - 300, 50 - txtsurf_.get_height() / 2))
        txtsurf = font.render(f'Land-attack missile', True, '#c95918')
        window.blit(txtsurf, (x_size - 300 + txtsurf_.get_width(), 50 - txtsurf.get_height() / 2))
        txtsurf = font.render(f'Characteristics:', True, '#b6b6d1')
        window.blit(txtsurf, (x_size - 300, 125 - txtsurf.get_height() / 2))
        txtsurf_ = font.render(f'Maximum range: ', True, '#b6b6d1')
        window.blit(txtsurf_, (x_size - 300, 150 - txtsurf_.get_height() / 2))
        txtsurf = font.render(f'300km', True, '#DADAFA')
        window.blit(txtsurf, (x_size - 300 + txtsurf_.get_width(), 150 - txtsurf.get_height() / 2))
        txtsurf_ = font.render(f'Max speed: ', True, '#b6b6d1')
        window.blit(txtsurf_, (x_size - 300, 175 - txtsurf_.get_height() / 2))
        txtsurf = font.render(f'3 Mach', True, '#DADAFA')
        window.blit(txtsurf, (x_size - 300 + txtsurf_.get_width(), 175 - txtsurf.get_height() / 2))
        txtsurf_ = font.render(f'Damage: ', True, '#b6b6d1')
        window.blit(txtsurf_, (x_size - 300, 200 - txtsurf_.get_height() / 2))
        txtsurf = font.render(f'25-50%', True, '#DADAFA')
        window.blit(txtsurf, (x_size - 300 + txtsurf_.get_width(), 200 - txtsurf.get_height() / 2))
        txtsurf_ = font.render(f'Sensor range: ', True, '#b6b6d1')
        window.blit(txtsurf_, (x_size - 300, 225 - txtsurf_.get_height() / 2))
        txtsurf = font.render(f'20km', True, '#DADAFA')
        window.blit(txtsurf, (x_size - 300 + txtsurf_.get_width(), 225 - txtsurf.get_height() / 2))
        txtsurf_ = font.render(f'Launch depth: ', True, '#b6b6d1')
        window.blit(txtsurf_, (x_size - 300, 250 - txtsurf_.get_height() / 2))
        txtsurf = font.render(f'60m', True, '#DADAFA')
        window.blit(txtsurf, (x_size - 300 + txtsurf_.get_width(), 250 - txtsurf.get_height() / 2))
        txtsurf = font.render(f'Description:', True, '#b6b6d1')
        window.blit(txtsurf, (x_size - 300, 275 - txtsurf.get_height() / 2))
        desc = f"The Novator Kalibr, (Калибр, caliber),\nalso referred to as 3M54-1" \
               f"Kalibr,\nis a family of Russian cruise " \
               f"missiles\ndeveloped by NPO Novator (OKB-8).\nIt first saw service " \
               f"in 1994. There are \nship-launched, submarine-launched\nand " \
               f"air-launched versions of the missile.\nVariants are made for anti-ship,\n" \
               f"anti-submarine and land attack\nuse. The missile can carry " \
               f"a warhead\nweighing up to 500 kilograms\n(1,100 lb) of explosive."
        i = 0
        for line in desc.split('\n'):
            txtsurf = font.render(line, True, '#DADAFA')
            window.blit(txtsurf, (x_size - 300, 300 + i * 25 - txtsurf.get_height() / 2))
            i += 1
