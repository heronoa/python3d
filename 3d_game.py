from ursina import *

# Cria a aplicação
app = Ursina()

# Configuração da janela
window.title = 'Movimento 3D'
window.borderless = False
window.fullscreen = False

# Cria o personagem (cubo vermelho)
player = Entity(
    model='cube',
    color=color.red,
    scale=(1, 2, 1),
    position=(0, 0.5, 0)
)

# Cria o chão
ground = Entity(
    model='plane',
    texture='grass',
    scale=(20, 1, 20),
    collider='box'
)

# Configura a câmera
camera.position = (0, 10, -20)
camera.look_at(player)

# Velocidade de movimento
speed = 5

def update():
    # Movimentação do jogador
    movimentacao = Vec3(0, 0, 0)
    
    if held_keys['up arrow']:
        movimentacao.z += speed * time.dt
    if held_keys['down arrow']:
        movimentacao.z -= speed * time.dt
    if held_keys['left arrow']:
        movimentacao.x -= speed * time.dt
    if held_keys['right arrow']:
        movimentacao.x += speed * time.dt

    player.position += movimentacao

    # Atualiza a posição da câmera para seguir o jogador
    camera.position = (player.x, 10, player.z - 20)
    camera.look_at(player)

app.run()