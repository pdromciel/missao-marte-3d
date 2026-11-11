"""Renderer OpenGL 3.3 Core: VBO/VAO, shaders GLSL, texturas e shadow mapping.
Passagem 1: renderização de profundidade na perspectiva da luz (2048px).
Passagem 2: renderização da câmera usando amostragem PCF do mapa de sombras.
Passagem 3: HUD 2D, desenhado em uma textura RGBA via Pygame.
"""
from __future__ import annotations
import ctypes
from pathlib import Path
import numpy as np
import pygame
from OpenGL.GL import *
from .math3d import look_at,orthographic,normalize

PROJECT_ROOT=Path(__file__).resolve().parent.parent

class Shader:
    def __init__(self,vertex_path,fragment_path):
        vert_source=(PROJECT_ROOT/'shaders'/vertex_path).read_text(encoding='utf-8')
        frag_source=(PROJECT_ROOT/'shaders'/fragment_path).read_text(encoding='utf-8')
        self.id=glCreateProgram()
        for type_,source,label in ((GL_VERTEX_SHADER,vert_source,vertex_path),
                                   (GL_FRAGMENT_SHADER,frag_source,fragment_path)):
            sh=glCreateShader(type_)
            glShaderSource(sh,source)
            glCompileShader(sh)
            if glGetShaderiv(sh,GL_COMPILE_STATUS)!=GL_TRUE:
                error=glGetShaderInfoLog(sh).decode(errors='replace')
                raise RuntimeError(f'Falha ao compilar shader {label}:\n{error}')
            glAttachShader(self.id,sh)
            glDeleteShader(sh)
        glLinkProgram(self.id)
        if glGetProgramiv(self.id,GL_LINK_STATUS)!=GL_TRUE:
            raise RuntimeError('Falha ao vincular shaders:\n'+glGetProgramInfoLog(self.id).decode(errors='replace'))
        self.locations={}
    def use(self):
        glUseProgram(self.id)
    def loc(self,name):
        if name not in self.locations:
            self.locations[name]=glGetUniformLocation(self.id,name)
        return self.locations[name]
    def mat4(self,name,v):
        loc=self.loc(name)
        if loc!=-1:
            # GL_TRUE transpõe a matriz NumPy row-major para o layout GLSL.
            glUniformMatrix4fv(loc,1,GL_TRUE,np.ascontiguousarray(v,dtype=np.float32))
    def vec3(self,name,v):
        loc=self.loc(name)
        if loc!=-1:glUniform3f(loc,float(v[0]),float(v[1]),float(v[2]))
    def float(self,name,v):
        loc=self.loc(name)
        if loc!=-1:glUniform1f(loc,float(v))
    def integer(self,name,v):
        loc=self.loc(name)
        if loc!=-1:glUniform1i(loc,int(v))

class GpuMesh:
    def __init__(self,geometry):
        self.vao=glGenVertexArrays(1)
        self.vbo=glGenBuffers(1)
        self.ebo=glGenBuffers(1)
        self.size=int(geometry.indices.size)
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER,self.vbo)
        glBufferData(GL_ARRAY_BUFFER,geometry.vertices.nbytes,geometry.vertices,GL_STATIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER,self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER,geometry.indices.nbytes,geometry.indices,GL_STATIC_DRAW)
        stride=8*4
        for index,count,offset in ((0,3,0),(1,3,12),(2,2,24)):
            glEnableVertexAttribArray(index)
            glVertexAttribPointer(index,count,GL_FLOAT,GL_FALSE,stride,ctypes.c_void_p(offset))
        glBindVertexArray(0)
    def draw(self):
        glBindVertexArray(self.vao)
        glDrawElements(GL_TRIANGLES,self.size,GL_UNSIGNED_INT,None)

class Textures:
    def __init__(self):self.loaded={}
    def get(self,filename):
        if filename in self.loaded:return self.loaded[filename]
        path=PROJECT_ROOT/'assets'/filename
        if not path.exists():raise FileNotFoundError('Textura ausente: '+str(path))
        surface=pygame.image.load(str(path))  # Não requer display surface em modo OPENGL
        w,h=surface.get_size()
        pixels=pygame.image.tostring(surface,'RGBA',True)
        tex=glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D,tex)
        glPixelStorei(GL_UNPACK_ALIGNMENT,1)
        glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,w,h,0,GL_RGBA,GL_UNSIGNED_BYTE,pixels)
        glGenerateMipmap(GL_TEXTURE_2D)
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR)
        self.loaded[filename]=tex
        return tex

class ShadowMap:
    def __init__(self,size=2048):
        self.size=size
        self.fbo=glGenFramebuffers(1)
        self.depth=glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D,self.depth)
        glTexImage2D(GL_TEXTURE_2D,0,GL_DEPTH_COMPONENT24,size,size,0,GL_DEPTH_COMPONENT,GL_FLOAT,None)
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_BORDER)
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_BORDER)
        glTexParameterfv(GL_TEXTURE_2D,GL_TEXTURE_BORDER_COLOR,np.array([1.,1.,1.,1.],dtype=np.float32))
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_COMPARE_MODE,GL_COMPARE_REF_TO_TEXTURE)
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_COMPARE_FUNC,GL_LEQUAL)
        glBindFramebuffer(GL_FRAMEBUFFER,self.fbo)
        glFramebufferTexture2D(GL_FRAMEBUFFER,GL_DEPTH_ATTACHMENT,GL_TEXTURE_2D,self.depth,0)
        glDrawBuffer(GL_NONE)
        glReadBuffer(GL_NONE)
        status=glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if status!=GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError(f'Framebuffer de sombras incompleto: 0x{status:x}')
        glBindFramebuffer(GL_FRAMEBUFFER,0)

class ScreenQuad:
    def __init__(self):
        coords=np.array([
            -1.,-1.,0.,0., 1.,-1.,1.,0., 1.,1.,1.,1.,
            -1.,-1.,0.,0., 1.,1.,1.,1., -1.,1.,0.,1.,
        ],dtype=np.float32)
        self.vao=glGenVertexArrays(1);self.vbo=glGenBuffers(1)
        glBindVertexArray(self.vao);glBindBuffer(GL_ARRAY_BUFFER,self.vbo)
        glBufferData(GL_ARRAY_BUFFER,coords.nbytes,coords,GL_STATIC_DRAW)
        glEnableVertexAttribArray(0);glVertexAttribPointer(0,2,GL_FLOAT,GL_FALSE,16,ctypes.c_void_p(0))
        glEnableVertexAttribArray(1);glVertexAttribPointer(1,2,GL_FLOAT,GL_FALSE,16,ctypes.c_void_p(8))
        glBindVertexArray(0)
    def draw(self):
        glBindVertexArray(self.vao);glDrawArrays(GL_TRIANGLES,0,6)

class MarsRenderer:
    def __init__(self,width,height,shadow_size=2048):
        self.width,self.height=width,height
        version=glGetString(GL_VERSION)
        if not version:
            raise RuntimeError('OpenGL não disponível. Atualize o driver da placa de vídeo.')
        print('[GL] Versão:',version.decode(errors='replace'))
        glEnable(GL_DEPTH_TEST);glDepthFunc(GL_LEQUAL)
        glEnable(GL_CULL_FACE);glCullFace(GL_BACK)
        glEnable(GL_MULTISAMPLE)
        glClearColor(.3,.2,.2,1.)
        self.scene=Shader('scene.vert','scene.frag')
        self.depth_shader=Shader('depth.vert','depth.frag')
        self.sky_shader=Shader('screen.vert','sky.frag')
        self.hud_shader=Shader('screen.vert','overlay.frag')
        self.shadow=ShadowMap(shadow_size)
        self.quad=ScreenQuad()
        self.tex=Textures()
        self.gpu={}
        self.hud_tex=glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D,self.hud_tex)
        glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,width,height,0,GL_RGBA,GL_UNSIGNED_BYTE,None)
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE)
        self.light_dir=normalize(np.array([-.48,.86,.53],dtype=np.float32))
        light_center=np.array([0.,0.,0.],dtype=np.float32)
        light_eye=light_center+self.light_dir*49.
        self.light_matrix=orthographic(-31,31,-31,31,2.,125.) @ look_at(light_eye,light_center)
        self.scene.use()
        self.scene.integer('uTexture',0)
        self.scene.integer('uShadowMap',1)
        self.scene.vec3('uLightDirection',self.light_dir)
        self.scene.mat4('uLightSpace',self.light_matrix)
        self.hud_shader.use();self.hud_shader.integer('uHUD',0)

    def _mesh(self,geometry):
        if geometry not in self.gpu:self.gpu[geometry]=GpuMesh(geometry)
        return self.gpu[geometry]

    def render(self,meshes,camera,time_seconds,hud_surface=None):
        # PASSAGEM 1 — mapa de profundidade a partir do Sol
        glViewport(0,0,self.shadow.size,self.shadow.size)
        glBindFramebuffer(GL_FRAMEBUFFER,self.shadow.fbo)
        glClear(GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_POLYGON_OFFSET_FILL)
        glPolygonOffset(1.7,3.0)
        self.depth_shader.use()
        self.depth_shader.mat4('uLightSpace',self.light_matrix)
        for node,model in meshes:
            if not node.cast_shadow:continue
            if node.material.double_sided:glDisable(GL_CULL_FACE)
            else:glEnable(GL_CULL_FACE)
            self.depth_shader.mat4('uModel',model)
            self._mesh(node.geometry).draw()
        glDisable(GL_POLYGON_OFFSET_FILL)
        glBindFramebuffer(GL_FRAMEBUFFER,0)
        glViewport(0,0,self.width,self.height)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        # PASSAGEM 2A — plano do céu
        glDisable(GL_DEPTH_TEST);glDisable(GL_CULL_FACE)
        self.sky_shader.use();self.sky_shader.float('uTime',time_seconds)
        self.quad.draw()
        # PASSAGEM 2B — objetos 3D iluminados, com textura + sombra
        glEnable(GL_DEPTH_TEST)
        self.scene.use()
        self.scene.mat4('uView',camera.view())
        self.scene.mat4('uProjection',camera.projection(self.width/self.height))
        self.scene.vec3('uCameraPos',camera.eye)
        glActiveTexture(GL_TEXTURE1);glBindTexture(GL_TEXTURE_2D,self.shadow.depth)
        for node,model in meshes:
            mat=node.material
            if mat.double_sided:glDisable(GL_CULL_FACE)
            else:glEnable(GL_CULL_FACE)
            self.scene.mat4('uModel',model)
            self.scene.vec3('uColor',mat.color)
            self.scene.float('uRoughness',mat.roughness)
            self.scene.float('uEmission',mat.emissive)
            has_tex=mat.texture is not None
            self.scene.integer('uHasTexture',has_tex)
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D,self.tex.get(mat.texture) if has_tex else 0)
            self._mesh(node.geometry).draw()
        # PASSAGEM 3 — interface 2D transparente em cima da cena
        if hud_surface is not None:
            glDisable(GL_DEPTH_TEST);glDisable(GL_CULL_FACE)
            glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
            glActiveTexture(GL_TEXTURE0);glBindTexture(GL_TEXTURE_2D,self.hud_tex)
            pixels=pygame.image.tostring(hud_surface,'RGBA',True)
            glPixelStorei(GL_UNPACK_ALIGNMENT,1)
            glTexSubImage2D(GL_TEXTURE_2D,0,0,0,self.width,self.height,GL_RGBA,GL_UNSIGNED_BYTE,pixels)
            self.hud_shader.use();self.quad.draw()
            glDisable(GL_BLEND)
        glBindVertexArray(0)
