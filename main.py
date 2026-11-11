"""MISSÃO MARTE — trabalho prático de Computação Gráfica.
Python + Pygame + PyOpenGL 3.3, framework didático do projeto.
Execute: python main.py
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

try:
    import pygame
except ImportError as exc:
    raise SystemExit('Pygame ausente. Execute: python -m pip install -r requirements.txt') from exc
try:
    from OpenGL.GL import glReadPixels, GL_RGBA, GL_UNSIGNED_BYTE, glGetString, GL_VERSION
except ImportError as exc:
    raise SystemExit('PyOpenGL ausente. Execute: python -m pip install -r requirements.txt') from exc
try:
    import numpy
except ImportError as exc:
    raise SystemExit('NumPy ausente. Execute: python -m pip install -r requirements.txt') from exc

from framework.camera import OrbitCamera
from framework.renderer import MarsRenderer
from framework.hud import MissionHUD
from framework.mission import Mission
from models.world import MarsWorld


def save_screenshot(width,height,filename):
    """Captura o framebuffer OpenGL após desenhar a cena e o HUD."""
    pixel_bytes=glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE)
    surface=pygame.image.fromstring(bytes(pixel_bytes),(width,height),'RGBA',True)
    path=Path(filename).resolve()
    path.parent.mkdir(parents=True,exist_ok=True)
    pygame.image.save(surface,str(path))
    print('[FOTO] Imagem salva em:',path)


def parse_args():
    parser=argparse.ArgumentParser(description='Missão Marte: rover e drone em OpenGL 3D.')
    parser.add_argument('--width',type=int,default=1280,help='Largura da janela (padrão: 1280)')
    parser.add_argument('--height',type=int,default=720,help='Altura da janela (padrão: 720)')
    parser.add_argument('--shadow',type=int,choices=[512,1024,2048,4096],default=2048,
                        help='Resolução do shadow mapping (padrão: 2048)')
    parser.add_argument('--frames',type=int,default=0,help='Encerrar após N frames (teste técnico)')
    parser.add_argument('--screenshot',type=str,help='Salvar uma captura PNG antes de encerrar')
    return parser.parse_args()


def run():
    args=parse_args()
    args.width=max(800,args.width)
    args.height=max(540,args.height)
    pygame.init()
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION,3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION,3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,pygame.GL_CONTEXT_PROFILE_CORE)
    pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE,24)
    pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER,1)
    try:
        pygame.display.set_mode((args.width,args.height),pygame.OPENGL|pygame.DOUBLEBUF)
        pygame.display.set_caption('MISSÃO MARTE | Rover + Drone | Computação Gráfica')
        renderer=MarsRenderer(args.width,args.height,args.shadow)
    except Exception as exc:
        pygame.quit()
        raise RuntimeError('Não foi possível iniciar o OpenGL 3.3. Verifique o driver de vídeo e o README.\n'
                           f'Detalhes técnicos: {exc}') from exc
    camera=OrbitCamera()
    mission=Mission()
    world=MarsWorld()
    hud=MissionHUD(args.width,args.height)
    clock=pygame.time.Clock()
    elapsed=0.
    paused=False
    hud_visible=True
    follow=False
    mouse_drag=False
    frames=0
    print('[OK] Missão Marte iniciada. P=pause, H=HUD, C=seguir, F9=print, ESC=sair.')
    try:
        running=True
        while running:
            dt=clock.tick(60)/1000.0
            for event in pygame.event.get():
                if event.type==pygame.QUIT:running=False
                elif event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_ESCAPE:running=False
                    elif event.key==pygame.K_p:paused=not paused
                    elif event.key==pygame.K_h:hud_visible=not hud_visible
                    elif event.key==pygame.K_c:follow=not follow
                    elif event.key==pygame.K_1:camera.preset(1);follow=False
                    elif event.key==pygame.K_2:camera.preset(2);follow=False
                    elif event.key==pygame.K_3:camera.preset(3);follow=False
                    elif event.key==pygame.K_F9:
                        # Salvar após a renderização deste frame, não imediatamente.
                        screenshot_request='captura_missao_marte.png'
                elif event.type==pygame.MOUSEBUTTONDOWN:
                    if event.button==1:mouse_drag=True
                    elif event.button==4:camera.zoom(-1.3)
                    elif event.button==5:camera.zoom(1.3)
                elif event.type==pygame.MOUSEBUTTONUP:
                    if event.button==1:mouse_drag=False
                elif event.type==pygame.MOUSEMOTION and mouse_drag:
                    dx,dy=event.rel
                    camera.orbit(-dx*.006,-dy*.004)
                    follow=False
                elif event.type==pygame.MOUSEWHEEL:
                    camera.zoom(-event.y*1.3)
            keys=pygame.key.get_pressed()
            speed=min(dt,.10)
            if keys[pygame.K_LEFT]:camera.orbit(-1.20*speed,0);follow=False
            if keys[pygame.K_RIGHT]:camera.orbit(1.20*speed,0);follow=False
            if keys[pygame.K_UP]:camera.orbit(0,.8*speed);follow=False
            if keys[pygame.K_DOWN]:camera.orbit(0,-.8*speed);follow=False
            if keys[pygame.K_w]:camera.pan(0,7.*speed);follow=False
            if keys[pygame.K_s]:camera.pan(0,-7.*speed);follow=False
            if keys[pygame.K_a]:camera.pan(-7.*speed,0);follow=False
            if keys[pygame.K_d]:camera.pan(7.*speed,0);follow=False
            if keys[pygame.K_q]:camera.zoom(-10.*speed)
            if keys[pygame.K_e]:camera.zoom(10.*speed)
            if keys[pygame.K_r]:camera.target[1]+=6.*speed
            if keys[pygame.K_f]:camera.target[1]-=6.*speed
            if not paused:elapsed+=dt
            pose=mission.sample(elapsed)
            world.update(pose,elapsed)
            if follow:
                import numpy as np
                want=pose.rover_position+np.array((0.,1.25,0.),dtype=np.float32)
                camera.target+=(want-camera.target)*min(1.,speed*2.5)
            overlay=hud.draw(pose,elapsed,clock.get_fps(),paused,follow) if hud_visible else None
            renderer.render(world.meshes(),camera,elapsed,overlay)
            # A foto é gravada com o frame já composto, antes do swap.
            if 'screenshot_request' in locals():
                save_screenshot(args.width,args.height,screenshot_request)
                del screenshot_request
            frames+=1
            if args.frames and frames>=args.frames:
                if args.screenshot:
                    save_screenshot(args.width,args.height,args.screenshot)
                running=False
            pygame.display.flip()
    finally:
        pygame.quit()

if __name__=='__main__':
    try:run()
    except (RuntimeError,pygame.error) as exc:
        print('\n[ERRO]',exc,file=sys.stderr)
        sys.exit(1)
