import math

from Components.decoy import Decoy


class SonarDecoy:
    def __init__(self):
        self.designation = 'Sonar decoy'
        self.speed = 0.03
        self.range = 50  # 100 km

    def launch(self, player, bearing, depth, mode):
        angle = player.azimuth + bearing
        if angle > 360:
            angle -= 360
        time = self.range / (self.speed * 60)
        impact_x = player.x - self.range * math.cos(math.radians(angle + 90))
        impact_y = player.y - self.range * math.sin(math.radians(angle + 90))
        return Decoy(player.x, player.y, player.azimuth, player.depth,
                     impact_x, impact_y, depth, time, mode)

    def render_description(self, font, x_size, window):
        txtsurf_ = font.render(f'Type: ', True, '#b6b6d1')
        window.blit(txtsurf_, (x_size - 300, 50 - txtsurf_.get_height() / 2))
        txtsurf = font.render(f'Countermeasure', True, '#ffff82')
        window.blit(txtsurf, (x_size - 300 + txtsurf_.get_width(), 50 - txtsurf.get_height() / 2))
        txtsurf = font.render(f'Characteristics:', True, '#b6b6d1')
        window.blit(txtsurf, (x_size - 300, 125 - txtsurf.get_height() / 2))
        txtsurf_ = font.render(f'Maximum range: ', True, '#b6b6d1')
        window.blit(txtsurf_, (x_size - 300, 150 - txtsurf_.get_height() / 2))
        txtsurf = font.render(f'80km', True, '#DADAFA')
        window.blit(txtsurf, (x_size - 300 + txtsurf_.get_width(), 150 - txtsurf.get_height() / 2))
        txtsurf_ = font.render(f'Max speed: ', True, '#b6b6d1')
        window.blit(txtsurf_, (x_size - 300, 175 - txtsurf_.get_height() / 2))
        txtsurf = font.render(f'85 km/h', True, '#DADAFA')
        window.blit(txtsurf, (x_size - 300 + txtsurf_.get_width(), 175 - txtsurf.get_height() / 2))
        txtsurf_ = font.render(f'Launch depth: ', True, '#b6b6d1')
        window.blit(txtsurf_, (x_size - 300, 200 - txtsurf_.get_height() / 2))
        txtsurf = font.render(f'400m', True, '#DADAFA')
        window.blit(txtsurf, (x_size - 300 + txtsurf_.get_width(), 200 - txtsurf.get_height() / 2))
        txtsurf = font.render(f'Description:', True, '#b6b6d1')
        window.blit(txtsurf, (x_size - 300, 225 - txtsurf.get_height() / 2))
        desc = f"Sonar decoy is a countermeasure\nagainst torpedoes. It is fired\nfrom a torpedo " \
               f"tube and has\nan increased sonar signature to\nfool sensors on a torpedo. " \
               f"Newer models\nare fitted with a noisemaker\nwhich can fool enemy passive sonar.\n" \
               f"Once deployed the decoy will go to the\nspecified bearing and distance before\n" \
               f"self destructing. There are two\nmodes, active and passive,\nactive mode will simulate " \
               f"active\nsonar echoes coming from the\ntarget which can confuse\nenemy active sonar " \
               f"torpedoes\nbut will not be effective\nagainst the passive sensors."
        i = 0
        for line in desc.split('\n'):
            txtsurf = font.render(line, True, '#DADAFA')
            window.blit(txtsurf, (x_size - 300, 250 + i * 25 - txtsurf.get_height() / 2))
            i += 1
