"""Grafo de cena hierárquico: nó transformável, malhas e materiais."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from .math3d import transform, vec3

@dataclass
class Material:
    color: tuple[float,float,float]=(1.,1.,1.)
    roughness: float=.65
    emissive: float=0.
    texture: str|None=None
    double_sided: bool=False

class Node:
    def __init__(self,name,position=(0,0,0),rotation=(0,0,0),scale=(1,1,1)):
        self.name=name
        self.position=np.array(position,dtype=np.float32)
        self.rotation=np.array(rotation,dtype=np.float32)
        self.scale=np.array(scale,dtype=np.float32)
        self.children=[]
        self.parent=None
    def add(self,child):
        child.parent=self
        self.children.append(child)
        return child
    def traverse(self,parent_matrix=None):
        if parent_matrix is None:
            parent_matrix=np.eye(4,dtype=np.float32)
        world=parent_matrix @ transform(self.position,self.rotation,self.scale)
        if isinstance(self,Mesh):
            yield self,world
        for child in self.children:
            yield from child.traverse(world)

class Mesh(Node):
    def __init__(self,name,geometry,material,cast_shadow=True,**kwargs):
        super().__init__(name,**kwargs)
        self.geometry=geometry
        self.material=material
        self.cast_shadow=cast_shadow


def part(parent,name,geometry,material,pos=(0,0,0),scale=(1,1,1),rot=(0,0,0),cast=True):
    return parent.add(Mesh(name,geometry,material,position=pos,scale=scale,rotation=rot,cast_shadow=cast))
