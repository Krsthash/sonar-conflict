import math

from Components.utilities import random_int
from Components.missiles import ASM


class Tasm:
    def __init__(self):
        self.designation = 'TASM'
        self.sensor_range = 15
        self.speed = 2
        self.range = 55

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

    def render_description(self, font, x_size, window):
        txtsurf_ = font.render(f'Type: ', True, '#b6b6d1')
        window.blit(txtsurf_, (x_size - 300, 50 - txtsurf_.get_height() / 2))
        txtsurf = font.render(f'Anti-ship missile', True, '#16c7c7')
        window.blit(txtsurf, (x_size - 300 + txtsurf_.get_width(), 50 - txtsurf.get_height() / 2))
        txtsurf = font.render(f'Characteristics:', True, '#b6b6d1')
        window.blit(txtsurf, (x_size - 300, 125 - txtsurf.get_height() / 2))
        txtsurf_ = font.render(f'Maximum range: ', True, '#b6b6d1')
        window.blit(txtsurf_, (x_size - 300, 150 - txtsurf_.get_height() / 2))
        txtsurf = font.render(f'110km', True, '#DADAFA')
        window.blit(txtsurf, (x_size - 300 + txtsurf_.get_width(), 150 - txtsurf.get_height() / 2))
        txtsurf_ = font.render(f'Max speed: ', True, '#b6b6d1')
        window.blit(txtsurf_, (x_size - 300, 175 - txtsurf_.get_height() / 2))
        txtsurf = font.render(f'0.8 Mach', True, '#DADAFA')
        window.blit(txtsurf, (x_size - 300 + txtsurf_.get_width(), 175 - txtsurf.get_height() / 2))
        txtsurf_ = font.render(f'Damage: ', True, '#b6b6d1')
        window.blit(txtsurf_, (x_size - 300, 200 - txtsurf_.get_height() / 2))
        txtsurf = font.render(f'50-65%', True, '#DADAFA')
        window.blit(txtsurf, (x_size - 300 + txtsurf_.get_width(), 200 - txtsurf.get_height() / 2))
        txtsurf_ = font.render(f'Sensor range: ', True, '#b6b6d1')
        window.blit(txtsurf_, (x_size - 300, 225 - txtsurf_.get_height() / 2))
        txtsurf = font.render(f'30km', True, '#DADAFA')
        window.blit(txtsurf, (x_size - 300 + txtsurf_.get_width(), 225 - txtsurf.get_height() / 2))
        txtsurf_ = font.render(f'Launch depth: ', True, '#b6b6d1')
        window.blit(txtsurf_, (x_size - 300, 250 - txtsurf_.get_height() / 2))
        txtsurf = font.render(f'60m', True, '#DADAFA')
        window.blit(txtsurf, (x_size - 300 + txtsurf_.get_width(), 250 - txtsurf.get_height() / 2))
        txtsurf = font.render(f'Description:', True, '#b6b6d1')
        window.blit(txtsurf, (x_size - 300, 275 - txtsurf.get_height() / 2))
        desc = f"The TASM was the first version\nof the anti-ship variant\nof the Tomahawk, equipped\nwith an " \
               f"active radar\nseeker, rather than TERCOM.\nTASM, along with other Tomahawk\nconventional " \
               f"variants,\ncarried a 454 kg conventional\nwarhead. Its range was\nshorter than other " \
               f"variants\n" \
               f"but it was known for its agility,\ncapable of various flight patterns.\nDue to the lower " \
               f"speeds\nof the missile, ship defence\nsystems have an easier time\nshooting them down."
        i = 0
        for line in desc.split('\n'):
            txtsurf = font.render(line, True, '#DADAFA')
            window.blit(txtsurf, (x_size - 300, 300 + i * 25 - txtsurf.get_height() / 2))
            i += 1