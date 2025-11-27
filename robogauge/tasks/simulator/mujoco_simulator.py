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

import re
import time
import imageio
import numpy as np

from robogauge.utils.logger import logger
from robogauge.utils.helpers import pares_path
from robogauge.tasks.simulator.mujoco_config import MujocoConfig
from robogauge.tasks.simulator.sim_data import RobotProprioception, JointState, BaseState, IMUState

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
        self.n_step = 0

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
            self.viewer = mujoco.viewer.launch_passive(
                self.mj_model, self.mj_data, key_callback=self.key_callback
            )
            self.last_render_time = time.time()
            if self.cfg.render.save_video:
                self.renderer = mujoco.Renderer(
                    self.mj_model, height=self.cfg.render.height,
                    width=self.cfg.render.width
                )

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
        self.n_step = 0
        self.preload_sensors()

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
                time_untile_next_render = self.cfg.physics.simulation_dt - (
                    time.time() - self.last_render_time
                )
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

        n_sensor = self.mj_model.nsensor
        
        proprio = RobotProprioception(
            joint=JointState(
                pos=self.get_sensor_data('joint_pos'),
                vel=self.get_sensor_data('joint_vel'),
                force=self.get_sensor_data('joint_eff'),
            ),
            imu=IMUState(
                quat=self.get_sensor_data('imu_quat'),
                ang_vel=self.get_sensor_data('imu_ang_vel'),
                acc=self.get_sensor_data('imu_acc'),
                pos=self.get_sensor_data('imu_pos'),
                lin_vel=self.get_sensor_data('imu_lin_vel'),
            ),
            base=BaseState(
                pos=self.mj_data.qpos[:3],      # world frame
                quat=self.mj_data.qpos[3:7],    # world frame
                vel=self.mj_data.qvel[:3],      # body frame
                ang_vel=self.mj_data.qvel[3:6], # body frame
            )
        )
        if self.n_step == 0:
            self.debug_print_proprio_shapes(proprio)
        self.n_step += 1

        return proprio
    
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
    
    def preload_sensors(self):
        # Preload sensor names
        self.joint_pos_sensor_names = self.find_sensors(tag_name="jointpos")
        self.joint_vel_sensor_names = self.find_sensors(tag_name="jointvel")
        self.joint_eff_sensor_names = self.find_sensors(tag_name="jointactuatorfrc")
        self.imu_quat = self.find_sensors(tag_name="framequat")
        self.imu_ang_vel = self.find_sensors(tag_name="gyro")
        self.imu_acc = self.find_sensors(tag_name="accelerometer")
        self.imu_pos = self.find_sensors(tag_name="framepos")
        self.imu_lin_vel = self.find_sensors(tag_name="framelinvel")
        logger.info(
            f"\n{'='*20} XML SENSOR NAMES {'='*20}\n"
            f"""Joint Position Sensors [{len(self.joint_pos_sensor_names)}]: {self.joint_pos_sensor_names}\n"""
            f"""Joint Velocity Sensors [{len(self.joint_vel_sensor_names)}]: {self.joint_vel_sensor_names}\n"""
            f"""Joint Effort Sensors [{len(self.joint_eff_sensor_names)}]: {self.joint_eff_sensor_names}\n"""
            f"""IMU Sensors: Quat{self.imu_quat}, AngVel{self.imu_ang_vel}, Acc{self.imu_acc}, Pos{self.imu_pos}, LinVel{self.imu_lin_vel}"""
        )

        # Cache sensor indices
        self.sensor_cache = {}
        all_lists = {
            'joint_pos': self.joint_pos_sensor_names,
            'joint_vel': self.joint_vel_sensor_names,
            'joint_eff': self.joint_eff_sensor_names,
            'imu_quat': self.imu_quat,
            'imu_ang_vel': self.imu_ang_vel,
            'imu_acc': self.imu_acc,
            'imu_pos': self.imu_pos,
            'imu_lin_vel': self.imu_lin_vel
        }
        
        for key, name_list in all_lists.items():
            indices = []
            for name in name_list:
                sid = mujoco.mj_name2id(self.mj_model, mujoco.mjtObj.mjOBJ_SENSOR, name)
                if sid == -1: continue
                adr = int(self.mj_model.sensor_adr[sid])
                dim = int(self.mj_model.sensor_dim[sid])
                indices.append((adr, dim))
            self.sensor_cache[key] = indices

    def find_sensors(self, *, pattern: re.Pattern = None, tag_name: str = None) -> list:
        model = self.mj_model
        found = []
        tag_map = {
            "jointpos":         mujoco.mjtSensor.mjSENS_JOINTPOS,
            "jointvel":         mujoco.mjtSensor.mjSENS_JOINTVEL,
            "jointactuatorfrc": mujoco.mjtSensor.mjSENS_JOINTACTFRC,
            "accelerometer":    mujoco.mjtSensor.mjSENS_ACCELEROMETER,
            "gyro":             mujoco.mjtSensor.mjSENS_GYRO,
            "framepos":         mujoco.mjtSensor.mjSENS_FRAMEPOS,
            "framequat":        mujoco.mjtSensor.mjSENS_FRAMEQUAT,
            "framelinvel":      mujoco.mjtSensor.mjSENS_FRAMELINVEL,
            "frameangvel":      mujoco.mjtSensor.mjSENS_FRAMEANGVEL,
        }
        tag_type_id = None
        if tag_name:
            if tag_name not in tag_map:
                logger.warning(f"Unknown tag_name '{tag_name}', ignoring tag filter.")
                return []
            tag_type_id = tag_map[tag_name]

        for i in range(model.nsensor):
            if tag_type_id is not None and model.sensor_type[i] != tag_type_id:
                continue
            name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_SENSOR, i)
            if pattern is None or name and pattern.search(name):
                found.append(name)
        return found

    def get_sensor_data(self, cache_key: str) -> np.ndarray:
        ids = self.sensor_cache.get(cache_key, [])
        if not ids:
            return np.array([])

        data_list = []
        for adr, dim in ids:
            data_list.append(self.mj_data.sensordata[adr:adr+dim])
        return np.concatenate(data_list)

    def debug_print_proprio_shapes(self, proprio: RobotProprioception):
        """Log shapes (or lengths) of each numpy vector inside a RobotProprioception.

        This helps debug mismatched sensor sizes between robots.
        """
        def _shape(x):
            try:
                arr = np.asarray(x)
                return arr.shape
            except Exception:
                return None

        jp = proprio.joint
        bs = proprio.base
        imu = proprio.imu

        logger.info("Proprioception shapes:")
        logger.info(f"  joint.pos: { _shape(jp.pos) }")
        logger.info(f"  joint.vel: { _shape(jp.vel) }")
        logger.info(f"  joint.force: { _shape(jp.force) }")

        logger.info(f"  base.pos: { _shape(bs.pos) }")
        logger.info(f"  base.quat: { _shape(bs.quat) }")
        logger.info(f"  base.vel: { _shape(bs.vel) }")
        logger.info(f"  base.ang_vel: { _shape(bs.ang_vel) }")

        logger.info(f"  imu.quat: { _shape(imu.quat) }")
        logger.info(f"  imu.ang_vel: { _shape(imu.ang_vel) }")
        logger.info(f"  imu.acc: { _shape(imu.acc) }")
        logger.info(f"  imu.pos: { _shape(imu.pos) }")
        logger.info(f"  imu.lin_vel: { _shape(imu.lin_vel) }")
