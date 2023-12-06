import pygame, time, moderngl
from .config import config
from .core_funcs import clip
from .mgl import MGL

class Window:
    def __init__(self, game):
        self.game = game

        pygame.init()

        # config ------------------------------------------------------------------------- #
        self.scaled_resolution = config['window']['scaled_resolution']
        self.base_resolution = config['window']['base_resolution']
        self.offset = [0, 0]
        self.background_color = config['window']['background_color']
        self.title = config['window']['title']

        # screen ------------------------------------------------------------------------- #
        self.screen = pygame.display.set_mode(self.scaled_resolution, pygame.OPENGL | pygame.DOUBLEBUF)
        self.display = pygame.Surface((self.base_resolution[0], self.base_resolution[1]))
        self.mgl = MGL(self.game)
        
        # icon and caption --------------------------------------------------------------- #
        self.icon = pygame.image.load('data/graphics/icon/icon.png')
        pygame.display.set_icon(self.icon)
        pygame.display.set_caption(self.title)

        # time and dt -------------------------------------------------------------------- #
        self.freeze_frame = {}

        self.dt = 0.1
        self.frame_history = [0.01]
        self.frame_start = time.time()
        self.show_fps = True
        self.timer = 0

        # cursor -------------------------------------------------------------------------- #
        pygame.mouse.set_visible(False)
        self.cursor_id = 'normal'
        self.cursor = None

        # zoom ---------------------------------------------------------------------------- #
        self.zoom = 1

    def fps(self):
        avg_dt = sum(self.frame_history) / len(self.frame_history)
        avg_fps = 1 / avg_dt
        return avg_fps

    def add_freeze(self, rate, duration):
        self.freeze_frame[rate] = duration

    def render_frame(self):
        if not self.cursor:
            self.cursor = self.game.assets.cursor[self.cursor_id]
        self.display.blit(self.cursor, (self.game.input.mouse_pos[0] - self.offset[0] - self.game.assets.cursor[self.cursor_id].get_width() // 2, self.game.input.mouse_pos[1] - self.offset[1] - self.game.assets.cursor[self.cursor_id].get_height() // 2))

        frame_tex = self.mgl.surf_to_texture(self.display)
        frame_tex.use(0)
        self.mgl.program['tex'] = 0
        self.mgl.program['world_timer'] = self.game.world.world_timer / 100
        self.mgl.render_object.render(mode=moderngl.TRIANGLE_STRIP)
        
        pygame.display.flip()

        frame_tex.release()

        self.dt = time.time() - self.frame_start
        self.ui_dt = self.dt

        delete_list = []

        orig_dt = self.dt

        if self.freeze_frame != {}:
            slowest_freeze = min(list(self.freeze_frame))
            if self.freeze_frame[slowest_freeze] > self.dt:
                self.dt *= slowest_freeze
            else:
                self.dt -= self.freeze_frame[slowest_freeze] * (1 - slowest_freeze)

        for freeze_amount in self.freeze_frame:
            if self.freeze_frame[freeze_amount] > orig_dt:
                self.freeze_frame[freeze_amount] -= orig_dt
            else:
                self.freeze_frame[freeze_amount] = 0
                delete_list.append(freeze_amount)

        for freeze in delete_list:
            del self.freeze_frame[freeze]

        self.timer += self.dt
        if self.dt > 0.05:
            print('lag spike', + self.timer)
            self.timer = 0

        self.dt = min(max(0.00001, self.dt), 0.1)
        self.frame_start = time.time()
        self.frame_history.append(self.ui_dt)
        self.frame_history = self.frame_history[-200:]

        if self.zoom == 1:
            pygame.transform.scale(self.display, self.scaled_resolution)
        else:
            size = [int(self.display.get_width() / self.zoom), int(self.display.get_height() / self.zoom)]
            self.display = pygame.transform.scale(clip(self.display, (self.display.get_width() - size[0]) // 2, (self.display.get_height() - size[1]) // 2, size[0], size[1]), self.screen.get_size())

        self.display.fill(self.background_color)