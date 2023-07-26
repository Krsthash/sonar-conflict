import math


class Mk48:
    def __init__(self):
        self.designation = 'Mk-48'
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

    def render_description(self, font, x_size, window):
        txtsurf_ = font.render(f'Type: ', True, '#b6b6d1')
        window.blit(txtsurf_, (x_size - 300, 50 - txtsurf_.get_height() / 2))
        txtsurf = font.render(f'Torpedo', True, '#263ded')
        window.blit(txtsurf, (x_size - 300 + txtsurf_.get_width(), 50 - txtsurf.get_height() / 2))
        txtsurf = font.render(f'Characteristics:', True, '#b6b6d1')
        window.blit(txtsurf, (x_size - 300, 125 - txtsurf.get_height() / 2))
        txtsurf_ = font.render(f'Maximum range: ', True, '#b6b6d1')
        window.blit(txtsurf_, (x_size - 300, 150 - txtsurf_.get_height() / 2))
        txtsurf = font.render(f'70km (eff. 45km)', True, '#DADAFA')
        window.blit(txtsurf, (x_size - 300 + txtsurf_.get_width(), 150 - txtsurf.get_height() / 2))
        txtsurf_ = font.render(f'Max speed: ', True, '#b6b6d1')
        window.blit(txtsurf_, (x_size - 300, 175 - txtsurf_.get_height() / 2))
        txtsurf = font.render(f'106 km/h', True, '#DADAFA')
        window.blit(txtsurf, (x_size - 300 + txtsurf_.get_width(), 175 - txtsurf.get_height() / 2))
        txtsurf_ = font.render(f'Damage: ', True, '#b6b6d1')
        window.blit(txtsurf_, (x_size - 300, 200 - txtsurf_.get_height() / 2))
        txtsurf = font.render(f'30-50%', True, '#DADAFA')
        window.blit(txtsurf, (x_size - 300 + txtsurf_.get_width(), 200 - txtsurf.get_height() / 2))
        txtsurf_ = font.render(f'Sensor range: ', True, '#b6b6d1')
        window.blit(txtsurf_, (x_size - 300, 225 - txtsurf_.get_height() / 2))
        txtsurf = font.render(f'20km/40km (active)', True, '#DADAFA')
        window.blit(txtsurf, (x_size - 300 + txtsurf_.get_width(), 225 - txtsurf.get_height() / 2))
        txtsurf_ = font.render(f'Launch depth: ', True, '#b6b6d1')
        window.blit(txtsurf_, (x_size - 300, 250 - txtsurf_.get_height() / 2))
        txtsurf = font.render(f'800m', True, '#DADAFA')
        window.blit(txtsurf, (x_size - 300 + txtsurf_.get_width(), 250 - txtsurf.get_height() / 2))
        txtsurf = font.render(f'Description:', True, '#b6b6d1')
        window.blit(txtsurf, (x_size - 300, 275 - txtsurf.get_height() / 2))
        desc = f"The Mark 48 and its improved\nAdvanced Capability (ADCAP) variant\nare American heavyweight\n" \
               f"submarine-launched torpedoes.\nThey were designed to sink\ndeep-diving nuclear-powered\n" \
               f"submarines and high-performance\n surface ships." \
               f"It has a top speed\nof 114km/h and a maximum depth\nof more than 500m. Homing\noptions " \
               f"are Active or " \
               f"Passive.\nActive utilises active sonar to\ntrack the target which increases\nthe " \
               f"range at " \
               f"which " \
               f"the target\ncan be found, but\nexposes your position to the enemy."
        i = 0
        for line in desc.split('\n'):
            txtsurf = font.render(line, True, '#DADAFA')
            window.blit(txtsurf, (x_size - 300, 300 + i * 25 - txtsurf.get_height() / 2))
            i += 1