from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import math

app = Ursina()

window.title = 'Jogo 3D - Visão em Terceira Pessoa'
window.borderless = False
window.fullscreen = False

MAP_SIZE = 500
SPAWN_RATE = 2  
ENEMY_SPEED = 3
PLAYER_SPEED = 15
MOUSE_SENSITIVITY = 10000
PLAYER_INITIAL_HP = 1
ENEMY_INITIAL_HP = 1
PLAYER_INITIAL_SCORE = 0



class Player(Entity):
    def __init__(self):
        super().__init__(
            model='cube',
            color=color.green,
            scale=(1, 2, 1),
            position=(0, 1, 0),
            collider='box'
        )
        self.speed = PLAYER_SPEED
        self.mouse_sensitivity = MOUSE_SENSITIVITY
        self.camera_pivot = Entity(parent=self, position=(0, 2, 0))
        self.health = PLAYER_INITIAL_HP
        self.score = PLAYER_INITIAL_SCORE

    def update(self):
        self.rotation_y += mouse.velocity[0] * self.mouse_sensitivity * time.dt
        self.camera_pivot.rotation_x -= mouse.velocity[1] * self.mouse_sensitivity * time.dt
        self.camera_pivot.rotation_x = clamp(self.camera_pivot.rotation_x, -90, 90)

        direction = Vec3(
            self.forward * (held_keys['w'] - held_keys['s']) +
            self.right * (held_keys['d'] - held_keys['a'])
        ).normalized()

        self.position += direction * self.speed * time.dt
        
        self.x = clamp(self.x, -MAP_SIZE/2, MAP_SIZE/2)
        self.z = clamp(self.z, -MAP_SIZE/2, MAP_SIZE/2)
        self.y = 1
    
    def score_point(self):
        self.score += 1
        update_hud()

    def get_hit(self):
        self.health -= 1
        if self.health <= 0:
            print('Você morreu!')
            application.quit()
            destroy(self)

class Enemy(Entity):
    def __init__(self, player):
        self.player = player
        self.speed = ENEMY_SPEED
        self.original_color = color.gray
        self.can_be_hit = True
        self.health = max(1, floor(ENEMY_INITIAL_HP * player.score // 5)) 
        super().__init__(
            model='cube',
            color=self.original_color,
            scale=(1, 2, 1),
            position=self.random_position(player),
            collider='box'
        )
        

    def random_position(self, player):
        spawn_radius = 15 + 25 // max(1,player.score)
        angle = random.uniform(0, 360)
        
        x = player.position.x + spawn_radius * math.cos(math.radians(angle))
        z = player.position.z + spawn_radius * math.sin(math.radians(angle))
        
        x = clamp(x, -MAP_SIZE/2 + 10, MAP_SIZE/2 - 10)
        z = clamp(z, -MAP_SIZE/2 + 10, MAP_SIZE/2 - 10)
        
        return Vec3(x, 1, z)

    def update(self):
        direction = (self.player.position - self.position).normalized()
        self.position += direction * self.speed * time.dt
        self.look_at(self.player.position)

        if (self.position - self.player.position).length() < 1.5:
            self.player.get_hit()
            destroy(self)

    def hit_reaction(self):
        if self.can_be_hit:
            self.can_be_hit = False
            self.color = color.red
            self.position -= self.forward * 3
            self.health -= 1

            invoke(setattr, self, 'color', self.original_color, delay=.2)
            invoke(setattr, self, 'can_be_hit', True, delay=1)

            if (self.health <= 0):
                self.player.score_point()
                # show_hit_marker()
                destroy(self)
                
class JumpingEnemy(Enemy):
    def __init__(self, player):
        super().__init__(player)
        self.jump_force = 1
        self.gravity = 4
        self.vertical_velocity = 0
        self.is_grounded = False

    def update(self):
        # Movimento horizontal normal
        direction = (self.player.position - self.position).normalized()
        self.position += direction * self.speed * time.dt
        
        # Lógica do pulo
        if self.is_grounded:
            self.vertical_velocity = self.jump_force
            self.is_grounded = False
            
        # Aplica gravidade
        self.vertical_velocity -= self.gravity * time.dt
        self.y += self.vertical_velocity
        
        # Verifica colisão com o chão
        if self.y <= 1:
            self.y = 1
            self.vertical_velocity = 0
            self.is_grounded = True
        
        self.look_at(self.player.position)
        self.color = color.blue

class slowTankyEnemy(Enemy):
    def update(self):
        direction = (self.player.position - self.position).normalized()
        self.color = color.orange
        self.scale = (1.5, 3, 1.5)
        self.position += direction * self.speed * time.dt
        self.look_at(self.player.position)

        if (self.position - self.player.position).length() < 1.5:
            self.player.get_hit()
            destroy(self)

class fastFragileEnemy(Enemy):
    def update(self):
        direction = (self.player.position - self.position).normalized()
        self.position += direction * self.speed * time.dt
        self.color = color.black
        self.look_at(self.player.position)
        self.health = 1
        self.scale = (1, 1, 1)

        if (self.position - self.player.position).length() < 1.5:
            self.player.get_hit()
            destroy(self)


player = Player()

camera.parent = player.camera_pivot
camera.position = (0, 1.5, -8)  
camera.rotation = (0, 0, 0)
camera.fov = 90

crosshair = Entity(
    parent=camera.ui,
    eternal=True
)

crosshair_lines = []
for i in range(4):
    line = Entity(
        parent=crosshair,
        model='quad',
        color=color.red,
        scale=(0.005, 0.05),
        rotation_z=45 + 90*i
    )
    crosshair_lines.append(line)

hit_x = Entity(
    parent=crosshair,
    model='quad',
    texture='circle',
    color=color.red,
    scale=0,
    alpha=0,
    rotation_z=45
)

def show_hit_marker():
    hit_x.animate('scale', 0.03, duration=0.1)
    hit_x.animate('alpha', 0.8, duration=0.1)
    hit_x.animate('scale', 0, duration=0.2, delay=0.2)
    hit_x.animate('alpha', 0, duration=0.2, delay=0.2)

# Sistema de HUD
health_bar_bg = Entity(
    parent=camera.ui,
    model='quad',
    color=color.dark_gray,
    scale=(0.3, 0.03),
    position=(-0.7, 0.45)
)

health_bar = Entity(
    parent=camera.ui,
    model='quad',
    color=color.red,
    scale=(0.3, 0.03),
    position=(-0.7, 0.45),
    origin=(-0.5, 0)
)

score_text = Text(
    parent=camera.ui,
    text='Pontos: 0',
    position=(0.7, 0.45),
    origin=(0.5, 0.5),
    scale=2,
    color=color.white
)

def update_hud():
    health_bar.scale_x = (player.health / 10) * 0.3
    score_text.text = f'Pontos: {player.score}'


crosshair.position = (0, 0)

ground = Entity(
    model='plane',
    texture='grass',
    scale=(MAP_SIZE, 1, MAP_SIZE),
    collider='box',
    position=(0, 0, 0)
)

enemies = []

def spawn_enemy():
    temp_enemies = []

    if player.score < 10:
        enemy1 = Enemy(player)
        temp_enemies.append(enemy1)
    if player.score < 20:
        enemy1 = JumpingEnemy(player)
        enemy2 = Enemy(player)
        temp_enemies.append(enemy1)
        temp_enemies.append(enemy2)

    elif player.score < 30:
        enemy = slowTankyEnemy(player)
        enemy2 = Enemy(player)
        enemy3 = fastFragileEnemy(player)
        temp_enemies.append(enemy)
        temp_enemies.append(enemy2)
        temp_enemies.append(enemy3)

    else:
        enemy = fastFragileEnemy(player)
        enemy2 = Enemy(player)
        enemy3 = fastFragileEnemy(player)
        enemy4 = slowTankyEnemy(player)
        temp_enemies.append(enemy)
        temp_enemies.append(enemy2)
        temp_enemies.append(enemy3)
        temp_enemies.append(enemy4)

    for enemy in temp_enemies:
            enemies.append(enemy)
            
    safe_score = player.score if player.score != 0 else 1
    invoke(spawn_enemy, delay=SPAWN_RATE / safe_score)

spawn_enemy()

mouse.locked = True
mouse.visible = False

def input(key):
    if key == 'escape':
        mouse.locked = not mouse.locked
        mouse.visible = not mouse.visible
    
    if key == 'left mouse down' and mouse.locked:
        hit_info = raycast(camera.world_position, camera.forward, distance=50)
        if hit_info.entity in enemies:
            hit_info.entity.hit_reaction()


update_hud()

app.run()