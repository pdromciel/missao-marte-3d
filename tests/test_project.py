"""Testes sem Pygame/OpenGL: verificar geometria, transformações e missão."""
import sys
from pathlib import Path
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))

from framework.geometry import box,cylinder,sphere,cone,ring,terrain
from framework.math3d import look_at,perspective,transform
from framework.mission import Mission,PERIOD,STAGES
from models.world import MarsWorld

class GeometryTests(unittest.TestCase):
    def test_mesh_buffers(self):
        for create in (box,cylinder,sphere,cone,ring,terrain):
            result=create()
            geo=result[0] if isinstance(result,tuple) else result
            with self.subTest(geo=geo.name):
                self.assertEqual(geo.vertices.shape[1],8)
                self.assertEqual(geo.indices.size%3,0)
                self.assertTrue(np.all(np.isfinite(geo.vertices)))
                self.assertTrue(np.all(geo.indices<len(geo.vertices)))
    def test_normals_and_winding(self):
        for create in (box,cylinder,sphere,cone,ring,terrain):
            geo=create()
            geo=geo[0] if isinstance(geo,tuple) else geo
            checked=0
            for a,b,c in geo.indices.reshape(-1,3):
                positions=geo.vertices[[a,b,c],:3]
                normal=geo.vertices[[a,b,c],3:6].mean(axis=0)
                cross=np.cross(positions[1]-positions[0],positions[2]-positions[0])
                dot=float(np.dot(cross,normal))
                if abs(dot)>1.e-7:
                    self.assertGreater(dot,0.,f'Winding invertido em {geo.name}')
                    checked+=1
            self.assertGreater(checked,0)
    def test_camera_projection(self):
        camera=look_at(np.array([5.,5.,5.]),np.zeros(3))
        projection=perspective(55,16/9,.1,120)
        self.assertTrue(np.all(np.isfinite(camera)))
        self.assertEqual(projection.shape,(4,4))
        self.assertLess(projection[3,2],0)
    def test_transform_hierarchy(self):
        matrix=transform([3,0,0],[0,0,0],[2,2,2])
        self.assertTrue(np.allclose(matrix@np.array([1,0,0,1]),[5,0,0,1]))

class MissionTests(unittest.TestCase):
    def setUp(self): self.m=Mission()
    def at_stage(self,index,fraction=.5):
        t=sum(s[1] for s in STAGES[:index])+STAGES[index][1]*fraction
        return self.m.sample(t)
    def test_all_stages_reachable(self):
        for i in range(len(STAGES)):
            p=self.at_stage(i)
            self.assertEqual(p.stage_index,i)
            self.assertTrue(np.all(np.isfinite(p.drone_position)))
    def test_rover_waits_for_drone(self):
        waiting=[self.at_stage(i) for i in (2,3,4,5)]
        for p in waiting[1:]:
            self.assertTrue(np.allclose(p.rover_position,waiting[0].rover_position))
        self.assertGreater(self.at_stage(6,.9).rover_travel,waiting[0].rover_travel)
    def test_drone_inspects_target(self):
        p=self.at_stage(3,.62)
        d=np.linalg.norm(p.drone_position[[0,2]]-self.m.target)
        self.assertLess(d,1.5)
        self.assertGreater(p.scan_strength,.5)
    def test_after_cycle_resets(self):
        p=self.m.sample(PERIOD+.01)
        self.assertEqual(p.stage_index,0)
        self.assertEqual(p.cycle_number,2)
    def test_rover_motion_is_temporal(self):
        p1=self.m.sample(4.)
        p2=self.m.sample(4.5)
        self.assertGreater(np.linalg.norm(p1.rover_position-p2.rover_position),0)

class SceneTests(unittest.TestCase):
    def test_two_actors_and_shadows(self):
        world=MarsWorld()
        p=Mission().sample(17)
        world.update(p,17)
        meshes=world.meshes()
        self.assertGreater(len(meshes),300)
        names=[mesh.name for mesh,_ in meshes]
        self.assertIn('corpo do drone',names)
        self.assertIn('chassi principal',names)
        self.assertTrue(any(m.cast_shadow for m,_ in meshes))
        self.assertTrue(any(m.material.texture for m,_ in meshes))
    def test_texture_exists(self):
        self.assertTrue((ROOT/'assets'/'mars_ground.png').is_file())
    def test_all_shaders_exist(self):
        for name in ('scene.vert','scene.frag','depth.vert','depth.frag',
                     'screen.vert','sky.frag','overlay.frag'):
            self.assertTrue((ROOT/'shaders'/name).is_file())

if __name__=='__main__': unittest.main()
