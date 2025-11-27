# -*- coding: utf-8 -*-
'''
@File    : mujoco_simulator.py
@Time    : 2025/11/27 15:54:20
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : None
'''
import mujoco
import mujoco.viewer
from dm_control import mjcf

import time
import imageio
import numpy as np

from robogauge.utils.logger import logger
from robogauge.utils.helpers import pares_path
from robogauge.tasks.simulator.mujoco_config import MujocoConfig

class MujocoSimulator:
    def __init__(self, sim_cfg: MujocoConfig):
        self.cfg = sim_cfg
        self.terrain_xml = None
        self.robot_xml = None
        self.terrain_spawn_xy = None
        self.robot_spawn_height = None
        self.viewer = None
        self.renderer = None
        self.vid_writer = None
        self.vid_count = 0
        self._pause = True
    
    def load(
        self,
        terrain_xml: str = None,
        robot_xml: str = None,
        terrain_spawn_xy: list = None,
        robot_spawn_height: float = None,
    ):
        """ Load terrain and robot into the simulator, support re-loading. """
        if terrain_xml is not None:
            self.terrain_xml = pares_path(terrain_xml)
        if robot_xml is not None:
            self.robot_xml = pares_path(robot_xml)
        if terrain_spawn_xy is not None:
            self.terrain_spawn_xy = terrain_spawn_xy
        if robot_spawn_height is not None:
            self.robot_spawn_height = robot_spawn_height

        terrain_xml = self.terrain_xml
        robot_xml = self.robot_xml
        terrain_spawn_xy = self.terrain_spawn_xy
        robot_spawn_height = self.robot_spawn_height
        if terrain_xml is None or robot_xml is None:
            raise ValueError("Terrain and robot XML paths must be provided.")
        
        robot_mjcf = mjcf.from_path(robot_xml)
        terrain_mjcf = mjcf.from_path(terrain_xml)
        for j in robot_mjcf.find_all('joint'):
            if j.tag == 'freejoint':
                j.remove()
        attachment_frame = terrain_mjcf.attach(robot_mjcf)
        attachment_frame.add('freejoint')
        attachment_frame.pos = [*terrain_spawn_xy, robot_spawn_height]

        if self.viewer is not None:
            self.close_viewer()
        self.mj_physics = mjcf.Physics.from_mjcf_model(terrain_mjcf)
        self.mj_model = self.mj_physics.model.ptr
        self.mj_data = self.mj_physics.data.ptr
        self.mj_model.opt.timestep = self.cfg.physics.simulation_dt
        self.headless = self.cfg.viewer.headless
        if self.cfg.render.save_video and self.headless:
            logger.warning("Cannot save video in headless mode, disabling video saving.")
            self.cfg.render.save_video = False
        if not self.headless:
            self.viewer = mujoco.viewer.launch_passive(self.mj_model, self.mj_data, key_callback=self.key_callback)
            self.last_render_time = time.time()
            if self.cfg.render.save_video:
                self.renderer = mujoco.Renderer(self.mj_model, height=self.cfg.render.height, width=self.cfg.render.width)

                vid_dir = logger.log_dir / "videos"
                vid_dir.mkdir(parents=True, exist_ok=True)
                vid_path = str(vid_dir / f"sim_video_{self.vid_count:03d}.mp4")
                self.vid_writer = imageio.get_writer(
                    vid_path,
                    fps=int(1 / self.cfg.physics.simulation_dt),
                )
                logger.info(f"Saving simulation video to: {vid_path}")
                self.vid_count += 1
        self._pause = False
    
    def key_callback(self, keycode):
        if keycode == 32:
            self._pause = not self._pause
            logger.info(f"Pause toggled: {self._pause}")
    
    def step(self) -> dict:
        """ Simulation step, pause will block thread. """
        while self._pause:
            time.sleep(0.1)
        self.mj_physics.step()
        if self.viewer is not None:
            if self.viewer.is_running():
                time_untile_next_render = self.cfg.physics.simulation_dt - (time.time() - self.last_render_time)
                if time_untile_next_render > 0:
                    time.sleep(time_untile_next_render)
                self.viewer.sync()
                if self.vid_writer is not None:
                    self.renderer.update_scene(self.mj_data, camera=self.viewer.cam)
                    frame = self.renderer.render()
                    self.vid_writer.append_data(frame)
                self.last_render_time = time.time()
            else:
                logger.warning("Viewer closed by user, stop video recording.")
                self.close_viewer()

        info = {}
        return info
    
    def reset(self):
        """ Reset the simulator to initial state. """
        self.mj_physics.reset()
        if self.viewer is not None:
            self.viewer.sync()

    def apply_action(self, action: np.ndarray):
        """ Apply action to the simulator. """
        self.mj_data.ctrl[:] = action
    
    def close_viewer(self):
        """ Close the viewer and video writer. """
        if self.viewer is not None:
            self.viewer.close()
            self.viewer = None
            logger.info("Closing viewer.")
        if self.vid_writer is not None:
            self.vid_writer.close()
            self.vid_writer = None
            self.renderer = None
            logger.info("Closing video writer.")
