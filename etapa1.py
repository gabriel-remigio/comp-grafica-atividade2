import numpy as np
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *

# Retorna os vertices do arquivo .ply de entrada
# Linha por linha, primeiro procura pela linha "element vertex" para descobrir a quantidade N de vertices
# Entao, apos ler "end header", coleta todos os N vertices seguintes numa matriz
def read_model(model_path):
  try:
      with open(model_path, 'r') as file:
        points_to_collect = -1
        points = []
        collecting = False

        for line in file:
          if collecting and points_to_collect > 0:
            coordinates = line.strip().split()
            points.append([float(coordinates[0]), float(coordinates[1]), float(coordinates[2])])
            points_to_collect -= 1

            if points_to_collect <= 0:
              return np.array(points)

            continue

          if line.startswith("end_header"):
            collecting = True
            continue

          if line.startswith("element vertex"):
            points_to_collect = int(line.strip().split()[2])
            continue

        return None

  except FileNotFoundError:
      print("modelo.ply not found")

# Retorna uma matriz de translacao com o deslocamento de entrada
# formula pega aqui: https://www.mathworks.com/help/images/matrix-representation-of-geometric-transformations.html
def translation_matrix(x, y, z):
  return np.array([[1.0, 0.0, 0.0, x],
                   [0.0, 1.0, 0.0, y],
                   [0.0, 0.0, 1.0, z],
                   [0.0, 0.0, 0.0, 1.0]])

# Retorna uma matriz de rotação a partir de um angulo e um eixo de rotacao
# Formula de angulo + eixo de rotacao para quaternion pega aqui: https://www.euclideanspace.com/maths/geometry/rotations/conversions/angleToQuaternion/index.htm
# Formula de quaternion para matriz de rotação pega aqui: https://www.mathworks.com/help/nav/ref/quaternion.rotmat.html#d126e189177
def rotation_matrix(angle_degrees, axis_x, axis_y, axis_z):
  length = np.sqrt(axis_x * axis_x + axis_y * axis_y + axis_z * axis_z)

  theta = np.deg2rad(angle_degrees)
  w = np.cos(theta / 2.0)
  x = axis_x * np.sin(theta / 2.0) / length
  y = axis_y * np.sin(theta / 2.0) / length
  z = axis_z * np.sin(theta / 2.0) / length

  return np.array([[1.0 - 2.0 * (y*y + z*z), 2.0 * (x*y - w*z), 2.0 * (x*z + w*y), 0.0],
                   [2.0 * (x*y + w*z), 1.0 - 2.0 * (x*x + z*z), 2.0 * (y*z - w*x), 0.0],
                   [2.0 * (x*z - w*y), 2.0 * (y*z + w*x), 1.0 - 2.0 * (x*x + y*y), 0.0],
                   [0.0, 0.0, 0.0, 1.0]])

# Retorna uma matriz de perspectiva baseada no field-of-view, comprimento e altura da tela, e no z maximo e minimo
# Formula para a matriz foi encontrada aqui: https://stackoverflow.com/questions/53245632/general-formula-for-perspective-projection-matrix
def perspective_matrix(fov, width, height, zfar, znear):
  f = 1.0 / np.tan(np.deg2rad(fov) / 2.0)
  aspect = width / height
  return np.array([[f / aspect, 0.0, 0.0, 0.0],
                   [0.0, f, 0.0, 0.0],
                   [0.0, 0.0, (zfar + znear) / (znear - zfar), 2.0 * zfar * znear / (znear - zfar)],
                   [0.0, 0.0, -1.0, 0.0]])

import pygame

# Carrega modelo.ply
model_path = "modelo.ply"
points = read_model(model_path)

# prepara a janela
clock = pygame.time.Clock()
pygame.display.set_mode((800, 600), pygame.DOUBLEBUF | pygame.OPENGL)
running = True

# Valores iniciais 
angle = 0
x = 0
y = 0
fov = 70

while running:
  # Controles da posicao x e y, angulo de rotacao e field-of-view
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      running = False
    if event.type == pygame.KEYDOWN:
      if event.key == pygame.K_ESCAPE:
        running = False
      if event.key == pygame.K_e:
        angle += 10
      if event.key == pygame.K_q:
        angle -= 10
      if event.key == pygame.K_d:
        x += 0.25
      if event.key == pygame.K_a:
        x -= 0.25
      if event.key == pygame.K_w:
        y += 0.25
      if event.key == pygame.K_s:
        y -= 0.25
      if event.key == pygame.K_g:
        fov += 5
      if event.key == pygame.K_f:
        fov -= 5

  # Limpa a tela e o buffer de profundidade
  glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
  glMatrixMode(GL_PROJECTION)
  glLoadIdentity()

  # Carrego a matriz de projecao
  projection_matrix = perspective_matrix(fov, 800, 600, 10, 0.1)
  projection_matrix_openGL = projection_matrix.T.flatten()
  glLoadMatrixf(projection_matrix_openGL)

  glMatrixMode(GL_MODELVIEW)
  glLoadIdentity()

  # Carrego a matriz de transformacao
  transform_matrix = translation_matrix(x, y, -1.0) @ rotation_matrix(angle, 1.0, 1.0, 0.5)
  transform_matrix_openGL = transform_matrix.T.flatten()
  glLoadMatrixf(transform_matrix_openGL)

  glBegin(GL_POINTS)
  glColor3f(1.0, 1.0, 1.0)

  # Desenho os pontos do modelo
  for point in points:
    glVertex3fv(point)

  glEnd()

  # Exibo na tela
  pygame.display.flip()
  clock.tick(60)

