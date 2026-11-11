"""Geometrias procedurais; vértices intercalados [pos3, normal3, uv2].
Não requer arquivos .obj ou Blender: toda a modelagem é feita por primitivas.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
import numpy as np

@dataclass(eq=False)
class Geometry:
    name: str
    vertices: np.ndarray  # float32 Nx8
    indices: np.ndarray  # uint32 M, múltiplo de 3


def _geometry(name, vertices, indices):
    v = np.asarray(vertices, dtype=np.float32).reshape((-1, 8))
    idx = np.asarray(indices, dtype=np.uint32).reshape(-1)
    return Geometry(name, v, idx)


def box():
    verts, inds = [], []
    # plano quadrilateral por face: canto, eixo U, eixo V, normal.
    faces = [
        ((-.5,-.5,.5), (1,0,0), (0,1,0), (0,0,1)),
        ((.5,-.5,-.5), (-1,0,0), (0,1,0), (0,0,-1)),
        ((.5,-.5,.5), (0,0,-1), (0,1,0), (1,0,0)),
        ((-.5,-.5,-.5), (0,0,1), (0,1,0), (-1,0,0)),
        ((-.5,.5,.5), (1,0,0), (0,0,-1), (0,1,0)),
        ((-.5,-.5,-.5), (1,0,0), (0,0,1), (0,-1,0)),
    ]
    for p, u, v, n in faces:
        base = len(verts)
        for a,b in ((0,0),(1,0),(1,1),(0,1)):
            pt = [p[i] + u[i]*a + v[i]*b for i in range(3)]
            verts.append(pt + list(n) + [a,b])
        # FACES foram definidas para que (U x V) coincida com a normal.
        # Em faces onde orientação muda, corrigir dinamicamente.
        c = np.cross(u,v)
        if float(np.dot(c,n)) > 0:
            inds.extend([base,base+1,base+2, base,base+2,base+3])
        else:
            inds.extend([base,base+2,base+1, base,base+3,base+2])
    return _geometry('cubo',verts,inds)


def cylinder(sides=20):
    verts, inds = [], []
    for i in range(sides+1):
        a = 2*math.pi*i/sides
        c,s=math.cos(a),math.sin(a)
        for y,v in ((-.5,0.),(.5,1.)):
            verts.append([c,y,s,c,0,s,i/sides,v])
    for i in range(sides):
        k = 2*i
        # orientação: cross(d_theta, +Y) -> para dentro; inverter
        inds.extend([k,k+1,k+2,k+1,k+3,k+2])
    for y,ny in ((.5,1.),(-.5,-1.)):
        center=len(verts)
        verts.append([0,y,0,0,ny,0,.5,.5])
        for i in range(sides+1):
            a=2*math.pi*i/sides
            c,s=math.cos(a),math.sin(a)
            verts.append([c,y,s,0,ny,0,(c+1)/2,(s+1)/2])
        for i in range(sides):
            if ny > 0: # cross tangent at angle increasing? radial test
                inds.extend([center,center+i+2,center+i+1])
            else:
                inds.extend([center,center+i+1,center+i+2])
    return _geometry('cilindro',verts,inds)


def sphere(segments=18, rings=12):
    verts, inds=[],[]
    for j in range(rings+1):
        theta=math.pi*j/rings
        y=math.cos(theta)
        r=math.sin(theta)
        for i in range(segments+1):
            a=2*math.pi*i/segments
            x,z=r*math.cos(a),r*math.sin(a)
            verts.append([x,y,z,x,y,z,i/segments,j/rings])
    for j in range(rings):
        for i in range(segments):
            k=j*(segments+1)+i
            # conferir orientação usando teste de face abaixo
            inds.extend([k,k+segments+1,k+1,k+1,k+segments+1,k+segments+2])
    return _geometry('esfera',verts,[v for a,b,c in np.asarray(inds).reshape(-1,3) for v in (a,c,b)])


def cone(sides=9):
    verts, inds=[],[]
    for i in range(sides):
        a=2*math.pi*i/sides
        b=2*math.pi*(i+1)/sides
        ca,sa,cb,sb=math.cos(a),math.sin(a),math.cos(b),math.sin(b)
        normal=np.cross([cb-ca,0,sb-sa],[-ca,1,-sa]);normal=normal/np.linalg.norm(normal)
        start=len(verts)
        verts.extend([
            [ca,-.5,sa,*normal,0,0],
            [cb,-.5,sb,*normal,1,0],
            [0,.5,0,*normal,.5,1],
        ])
        inds.extend([start,start+1,start+2])
    cap=len(verts)
    verts.append([0,-.5,0,0,-1,0,.5,.5])
    for i in range(sides+1):
        a=2*math.pi*i/sides;c,s=math.cos(a),math.sin(a)
        verts.append([c,-.5,s,0,-1,0,(c+1)*.5,(s+1)*.5])
    for i in range(sides):
        inds.extend([cap,cap+i+1,cap+i+2])
    return _geometry('cone',verts,inds)


def ring(segments=64):
    verts,inds=[],[]
    for i in range(segments+1):
        a=2*math.pi*i/segments;c,s=math.cos(a),math.sin(a)
        for r in (.88,1.):
            verts.append([c*r,0,s*r,0,1,0,(c*r+1)/2,(s*r+1)/2])
    for i in range(segments):
        k=i*2
        # torus plana, dupla face desabilitada no material emissivo
        inds.extend([k,k+1,k+2,k+1,k+3,k+2])
    return _geometry('anel',verts,[v for a,b,c in np.asarray(inds).reshape(-1,3) for v in (a,c,b)])


def terrain(size=84.0, steps=64):
    """Solo discretamente ondulado, triangulado com UV repetidas."""
    def height(x,z):
        return (0.07*math.sin(.24*x+.18*z)+0.05*math.cos(.31*z-.17*x)
                +0.055*math.sin(.57*x)*math.cos(.49*z))
    def normal(x,z):
        eps=.10
        dx=(height(x+eps,z)-height(x-eps,z))/(2*eps)
        dz=(height(x,z+eps)-height(x,z-eps))/(2*eps)
        v=np.array([-dx,1.,-dz],dtype=np.float32)
        return (v/np.linalg.norm(v)).tolist()
    verts,inds=[],[]
    for j in range(steps+1):
        z=size*(j/steps-.5)
        for i in range(steps+1):
            x=size*(i/steps-.5)
            y=height(x,z)
            verts.append([x,y,z,*normal(x,z),x*.18,z*.18])
    for j in range(steps):
        for i in range(steps):
            k=j*(steps+1)+i
            # plano: e_x cross e_z = -Y, logo inverter ordem
            inds.extend([k,k+steps+1,k+1,k+1,k+steps+1,k+steps+2])
    return _geometry('terreno',verts,inds),height
