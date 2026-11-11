"""Transformações de um grafo de cena, projeção perspectiva e câmera look-at.
Convenção: vetores-coluna; matrizes NumPy em ordem de linhas, convertidas para GLSL
com glUniformMatrix4fv(..., GL_TRUE, ...).
"""
from __future__ import annotations
import math
import numpy as np


def vec3(x=0.0, y=0.0, z=0.0):
    return np.array((x, y, z), dtype=np.float32)


def normalize(v):
    v = np.asarray(v, dtype=np.float32)
    length = float(np.linalg.norm(v))
    return v / length if length > 1e-8 else v * 0.0


def translation(v):
    m = np.eye(4, dtype=np.float32)
    m[:3, 3] = v
    return m


def scaling(v):
    m = np.eye(4, dtype=np.float32)
    m[0, 0], m[1, 1], m[2, 2] = v
    return m


def rotation_x(a):
    s, c = math.sin(a), math.cos(a)
    m = np.eye(4, dtype=np.float32)
    m[1, 1], m[1, 2], m[2, 1], m[2, 2] = c, -s, s, c
    return m


def rotation_y(a):
    s, c = math.sin(a), math.cos(a)
    m = np.eye(4, dtype=np.float32)
    m[0, 0], m[0, 2], m[2, 0], m[2, 2] = c, s, -s, c
    return m


def rotation_z(a):
    s, c = math.sin(a), math.cos(a)
    m = np.eye(4, dtype=np.float32)
    m[0, 0], m[0, 1], m[1, 0], m[1, 1] = c, -s, s, c
    return m


def transform(position, rotation, scale):
    """Euler em radianos (X, Y, Z); yaw Y precede pitch/roll no espaço local."""
    return (translation(position) @ rotation_y(rotation[1]) @ rotation_x(rotation[0])
            @ rotation_z(rotation[2]) @ scaling(scale)).astype(np.float32)


def perspective(fov_degrees, aspect, near, far):
    f = 1.0 / math.tan(math.radians(fov_degrees) / 2)
    m = np.zeros((4, 4), dtype=np.float32)
    m[0, 0] = f / aspect
    m[1, 1] = f
    m[2, 2] = (far + near) / (near - far)
    m[2, 3] = 2 * far * near / (near - far)
    m[3, 2] = -1.0
    return m


def orthographic(left, right, bottom, top, near, far):
    m = np.eye(4, dtype=np.float32)
    m[0, 0] = 2 / (right - left)
    m[1, 1] = 2 / (top - bottom)
    m[2, 2] = -2 / (far - near)
    m[0, 3] = -(right + left) / (right - left)
    m[1, 3] = -(top + bottom) / (top - bottom)
    m[2, 3] = -(far + near) / (far - near)
    return m


def look_at(eye, target, up=(0, 1, 0)):
    eye, target = np.asarray(eye, dtype=np.float32), np.asarray(target, dtype=np.float32)
    forward = normalize(target - eye)
    side = normalize(np.cross(forward, up))
    camera_up = np.cross(side, forward)
    m = np.eye(4, dtype=np.float32)
    m[0, :3], m[1, :3], m[2, :3] = side, camera_up, -forward
    m[:3, 3] = -(m[:3, :3] @ eye)
    return m


def lerp(a, b, t):
    return np.asarray(a) * (1.0 - t) + np.asarray(b) * t


def smoothstep(t):
    t = max(0., min(1., float(t)))
    return t * t * (3 - 2 * t)


def ease_in_out(t):
    """Aceleração/desaceleração mais discreta nos extremos."""
    t = max(0., min(1., float(t)))
    return t*t*t*(t*(t*6 - 15) + 10)


def angle_for_motion(vx, vz):
    """Orientação Y para um veículo cujo nariz aponta para -Z."""
    return math.atan2(-vx, -vz)
