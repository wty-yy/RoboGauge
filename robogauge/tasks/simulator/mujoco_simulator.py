# -*- coding: utf-8 -*-
'''
@File    : mujoco_simulator.py
@Time    : 2025/11/27 15:54:20
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Mujoco Simulator for Robogauge
'''
import mujoco
import mujoco.viewer
from dm_control import mjcf

import re
import time
import imageio
import numpy as np
from pathlib import Path
from typing import Literal, List, Optional, Union

from robogauge.utils.logger import logger
from robogauge.utils.helpers import parse_path
from robogauge.utils.math_utils import get_projected_gravity, quat_rotate_inverse
from robogauge.tasks.simulator.mujoco_config import MujocoConfig
from robogauge.tasks.simulator.sim_data import (
    SimData,
    RobotProprioception, JointState, BaseState, IMUState
)
from robogauge.tasks.gauge.goal_data import VelocityGoal

class MujocoSimulator:
    def __init__(self, sim_cfg: MujocoConfig):
        self.cfg = sim_cfg
        self.terrain_xmls = None
        self.robot_xml = None
        self.terrain_spawn_pos = None
        self.robot_spawn_height = None
        self.default_dof_pos = None
        self.invert_yaw = None
        self.viewer = None
        self.offscreen_cam = mujoco.MjvCamera()
        self.renderer = None
        self.vid_writer = None
        self.vid_count = 0
        self._pause = True
        self.n_step = 0
        self.sim_time = 0.0
        self.target_pos = None
        self.target_velocity: Optional[VelocityGoal] = None
        self.penetration_reset_count = 0

    def load(
        self,
        terrain_xmls: List[str] = None,
        robot_xml: str = None,
        terrain_spawn_pos: list = None,
        default_dof_pos: list = None,
        invert_yaw: bool = None,
    ):
        """ Load terrain and robot into the simulator, support re-loading. """
        if terrain_xmls is not None:
            self.terrain_xmls = [parse_path(xml) for xml in terrain_xmls]
        if robot_xml is not None:
            self.robot_xml = parse_path(robot_xml)
        if terrain_spawn_pos is not None:
            self.terrain_spawn_pos = terrain_spawn_pos
        if default_dof_pos is not None:
            self.default_dof_pos = default_dof_pos
        if invert_yaw is not None:
            self.invert_yaw = invert_yaw

        terrain_xmls = self.terrain_xmls
        robot_xml = self.robot_xml
        terrain_spawn_pos = self.terrain_spawn_pos
        if terrain_xmls is None or robot_xml is None:
            raise ValueError("Terrain and robot XML paths must be provided.")
        if default_dof_pos is None:
            raise ValueError("Default DOF positions must be provided.")
        
        # Create MJCF models
        robot_mjcf = mjcf.from_path(robot_xml)
        terrain_mjcf = mjcf.from_path(terrain_xmls[0])
        visual_elem = terrain_mjcf.visual
        global_elem = visual_elem.get_children('global')
        global_elem.offwidth = 1920
        global_elem.offheight = 1080

        for path in terrain_xmls[1:]:
            next_terrain = mjcf.from_path(path)
            terrain_mjcf.attach(next_terrain)
        for j in robot_mjcf.find_all('joint'):
            if j.tag == 'freejoint':
                j.remove()
        attachment_frame = terrain_mjcf.attach(robot_mjcf)
        attachment_frame.add('freejoint')
        attachment_frame.pos = terrain_spawn_pos

        self.close_viewer()
        self.close_video_writer()
        self.mj_physics = mjcf.Physics.from_mjcf_model(terrain_mjcf)
        self.mj_model = self.mj_physics.model.ptr
        self.mj_data = self.mj_physics.data.ptr
        self.mj_model.opt.timestep = self.cfg.physics.simulation_dt
        self.sim_dt = self.cfg.physics.simulation_dt
        if self.invert_yaw:
            self.mj_data.qpos[3] = 0.0
            self.mj_data.qpos[6] = 1.0
        self.mj_data.qpos[7:] = default_dof_pos

        # Domain randomization: base mass
        base_body_name = f'{Path(self.robot_xml).stem}/base_link'
        body_id = mujoco.mj_name2id(self.mj_model, mujoco.mjtObj.mjOBJ_BODY, base_body_name)
        assert body_id != -1, f"Body '{base_body_name}' not found in the model."
        if self.cfg.domain_rand.base_mass != 0.0:
            original_mass = self.mj_model.body_mass[body_id]
            new_mass = max(0.01, original_mass + self.cfg.domain_rand.base_mass)
            self.mj_model.body_mass[body_id] = new_mass
            logger.info(f"Randomized base mass: {original_mass:.3f} -> {new_mass:.3f} kg")
        
        # Domain randomization: friction
        if self.cfg.domain_rand.friction != 1.0:
            for i in range(self.mj_model.ngeom):
                # Both change robot friction and terrain friction, usually robot friction < 1.0
                # Mujoco friction calculation takes the *max* between two contacting geoms
                geom_friction = self.mj_model.geom_friction[i]
                geom_friction[0] *= self.cfg.domain_rand.friction
                self.mj_model.geom_friction[i] = geom_friction
            logger.info(f"Scaled geom friction by factor: {self.cfg.domain_rand.friction:.3f}")
        mujoco.mj_forward(self.mj_model, self.mj_data)

        # Setup offscreen camera
        self.offscreen_cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
        self.offscreen_cam.trackbodyid = body_id
        self.offscreen_cam.distance = self.cfg.viewer.camera_distance
        self.offscreen_cam.elevation = self.cfg.viewer.camera_elevation
        self.offscreen_cam.azimuth = self.cfg.viewer.camera_azimuth
        self.offscreen_cam.lookat = np.array([0.0, 0.0, 0.0])

        # Setup viewer
        self.headless = self.cfg.viewer.headless
        if not self.headless:
            self.viewer = mujoco.viewer.launch_passive(
                self.mj_model, self.mj_data, key_callback=self.key_callback
            )

            # set viewer.camera to follow robot
            self.viewer.cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
            self.viewer.cam.trackbodyid = body_id
            self.viewer.cam.distance = self.cfg.viewer.camera_distance
            self.viewer.cam.elevation = self.cfg.viewer.camera_elevation
            self.viewer.cam.azimuth = self.cfg.viewer.camera_azimuth
            self.last_render_time = time.time()
        
        # Setup video writer
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
                fps=self.cfg.render.video_fps,
            )
            self.vid_frame_skip = int(1 / (self.cfg.render.video_fps * self.sim_dt))
            logger.info(f"Simulation video saved at: {vid_path}")
            self.vid_count += 1

        # Initialize simulation state
        self._pause = False
        self.n_step = 0
        self.sim_time = 0.0
        self.penetration_reset_count = 0
        self.load_dof_limits()
        self.preload_sensors()

        # Robot controller placeholders
        self.action = None
        self.p_gains = None
        self.d_gains = None
        self.control_type = None

    def key_callback(self, keycode):
        if keycode == 32:
            self._pause = not self._pause
            logger.info(f"Pause toggled: {self._pause}")

    def step(self) -> SimData:
        """ Simulation step, pause will block thread. """
        while self._pause:
            time.sleep(0.1)
        self.update_torque()
        self.mj_physics.step()

        # Viewer sync
        if self.viewer is not None:
            if self.viewer.is_running():
                self.update_external_rendering(self.viewer, ctype='viewer')
                self.viewer.sync()
                time_untile_next_render = self.cfg.physics.simulation_dt - (
                    time.time() - self.last_render_time
                )
                if time_untile_next_render > 0:
                    time.sleep(time_untile_next_render)
                self.last_render_time = time.time()
            else:
                logger.warning("Viewer closed by user.")
                self.close_viewer()

        # Video recording
        if self.vid_writer is not None and self.n_step % self.vid_frame_skip == 0:
            render_cam = self.viewer.cam if self.viewer is not None else self.offscreen_cam
            # mujoco.mjv_updateCamera(render_cam)
            self.renderer.update_scene(self.mj_data, camera=render_cam)
            self.update_external_rendering(self.renderer, ctype='renderer')
            frame = self.renderer.render()
            self.vid_writer.append_data(frame)

        self.proprio = proprio = RobotProprioception(
            joint=JointState(
                pos=self.get_sensor_data('joint_pos'),
                vel=self.get_sensor_data('joint_vel'),
                torque=self.get_sensor_data('joint_eff'),
                limits=self.dof_limits,
                names=self.dof_names,
            ),
            imu=IMUState(
                pos=self.get_sensor_data('imu_pos'),
                quat=self.get_sensor_data('imu_quat'),
                acc=self.get_sensor_data('imu_acc'),
                lin_vel=self.get_sensor_data('imu_lin_vel'),  # body frame, check direction, go2 is inverted
                ang_vel=self.get_sensor_data('imu_ang_vel'),  # body frame, check direction, go2 is inverted
            ),
            base=BaseState(
                pos=self.mj_data.qpos[:3],      # world frame
                quat=self.mj_data.qpos[3:7],    # world frame
                lin_vel=quat_rotate_inverse(self.mj_data.qpos[3:7], self.mj_data.qvel[:3]),  # body frame
                ang_vel=quat_rotate_inverse(self.mj_data.qpos[3:7], self.mj_data.qvel[3:6]), # body frame
            )
        )
        if self.n_step % int(0.1 / self.sim_dt) == 0:
            logger.log(value=np.mean(proprio.imu.quat - proprio.base.quat), tag="sim/delta_quat", step=self.n_step)
            logger.log(value=np.mean(proprio.imu.ang_vel - proprio.base.ang_vel), tag="sim/delta_ang_vel", step=self.n_step)
            logger.log(value=np.mean(proprio.imu.lin_vel - proprio.base.lin_vel), tag="sim/delta_lin_vel", step=self.n_step)
            logger.log(value=proprio.imu.lin_vel[0], tag="sim/imu_lin_vel_x", step=self.n_step)
            logger.log(value=proprio.imu.lin_vel[1], tag="sim/imu_lin_vel_y", step=self.n_step)
            logger.log(value=proprio.base.lin_vel[0], tag="sim/base_lin_vel_x", step=self.n_step)
            logger.log(value=proprio.base.lin_vel[1], tag="sim/base_lin_vel_y", step=self.n_step)
        if self.n_step == 0:
            self.debug_print_proprio_shapes()

        sim_data = SimData(
            n_step=self.n_step,
            sim_dt=self.sim_dt,
            sim_time=self.sim_time,
            proprio=proprio
        )

        # input("DEBUG")
        self.n_step += 1
        self.sim_time = self.n_step * self.sim_dt
        self.check_truncation(sim_data)
        return sim_data
    
    def update_external_rendering(self,
            handle: Union[mujoco.viewer.Handle, mujoco.Renderer],
            ctype: Literal['viewer', 'renderer'],
        ):
        """ Update external rendering handle (viewer or renderer). """
        def add_target_sphere(geom_elem):
            mujoco.mjv_initGeom(
                geom_elem,
                type=mujoco.mjtGeom.mjGEOM_SPHERE,
                size=[0.1, 0, 0],
                pos=self.target_pos,
                mat=np.eye(3).flatten(),
                rgba=[1, 0, 0, 1]
            )

        def add_arrow(geom_elem, pos, vec, rgba, scale=1.0):
            vel_norm = np.linalg.norm(vec)
            if vel_norm < 1e-3: 
                mujoco.mjv_initGeom(
                    geom_elem,
                    type=mujoco.mjtGeom.mjGEOM_NONE,
                    size=[0, 0, 0], pos=pos, mat=np.eye(3).flatten(), rgba=[0, 0, 0, 0]
                )
                return

            mat = np.zeros(9)
            target_quat = np.zeros(4)
            vec_normalized = vec / vel_norm
            mujoco.mju_quatZ2Vec(target_quat, vec_normalized)
            mujoco.mju_quat2Mat(mat, target_quat)
            total_length = max(vel_norm * scale * 0.5, 0.05)
            shaft_radius = 0.015
            head_radius = 0.035
            mujoco.mjv_initGeom(
                geom_elem,
                type=mujoco.mjtGeom.mjGEOM_ARROW,
                size=[shaft_radius, head_radius, total_length], 
                pos=pos,
                mat=mat,
                rgba=rgba
            )

        viewer_geom_idx = 0
        if ctype == 'viewer':
            handle.user_scn.ngeom = 0  # reset user scene geometry

        if self.target_pos is not None:
            if ctype == 'viewer':
                add_target_sphere(handle.user_scn.geoms[viewer_geom_idx])
                viewer_geom_idx += 1
            else:
                handle.scene.ngeom += 1
                add_target_sphere(handle.scene.geoms[self.renderer.scene.ngeom - 1])
        
        if self.target_velocity is not None:
            base_pos_world = self.mj_data.qpos[:3]
            base_quat = self.mj_data.qpos[3:7]
            
            # rendering arrows start position
            offset_body = np.array([0.0, 0.0, 0.6])
            offset_world = np.zeros(3)
            mujoco.mju_rotVecQuat(offset_world, offset_body, base_quat)
            start_pos = base_pos_world + offset_world

            # Body Frame -> World Frame
            target_lin_vel_body = np.array([
                self.target_velocity.lin_vel_x, 
                self.target_velocity.lin_vel_y, 
                0.0
            ])
            target_lin_vel_world = np.zeros(3)
            mujoco.mju_rotVecQuat(target_lin_vel_world, target_lin_vel_body, base_quat)

            # Body Frame -> World Frame
            raw_current_vel = self.proprio.base.lin_vel
            current_lin_vel_body = np.array([
                raw_current_vel[0],
                raw_current_vel[1],
                0.0
            ])
            current_lin_vel_world = np.zeros(3)
            mujoco.mju_rotVecQuat(current_lin_vel_world, current_lin_vel_body, base_quat)

            COLOR_GREEN = [0, 1, 0, 1] # target
            COLOR_BLUE = [0, 0, 1, 1]  # current

            if ctype == 'viewer':
                add_arrow(handle.user_scn.geoms[viewer_geom_idx], start_pos, target_lin_vel_world, COLOR_GREEN)
                viewer_geom_idx += 1
                add_arrow(handle.user_scn.geoms[viewer_geom_idx], start_pos, current_lin_vel_world, COLOR_BLUE)
                viewer_geom_idx += 1
            else:
                handle.scene.ngeom += 1
                add_arrow(handle.scene.geoms[handle.scene.ngeom - 1], start_pos, target_lin_vel_world, COLOR_GREEN)
                handle.scene.ngeom += 1
                add_arrow(handle.scene.geoms[handle.scene.ngeom - 1], start_pos, current_lin_vel_world, COLOR_BLUE)

        if ctype == 'viewer':
            handle.user_scn.ngeom = viewer_geom_idx
    
    def check_penetration(self, threshold: float = -0.02):
        if self.penetration_reset_count >= self.cfg.truncation.penetration_max_reset_num:
            return False, None, None, None
        for i in range(self.mj_data.ncon):
            contact = self.mj_data.contact[i]
            if contact.dist < threshold:
                geom1_name = mujoco.mj_id2name(self.mj_model, mujoco.mjtObj.mjOBJ_GEOM, contact.geom1)
                geom2_name = mujoco.mj_id2name(self.mj_model, mujoco.mjtObj.mjOBJ_GEOM, contact.geom2)
                return True, geom1_name, geom2_name, contact.dist
        return False, None, None, None
    
    def check_truncation(self, sim_data: SimData):
        if self.cfg.truncation.enabled:
            projected_gravity = get_projected_gravity(sim_data.proprio.base.quat)
            if -projected_gravity[2] < np.cos(self.cfg.truncation.projected_gravity_rad):
                raise RuntimeError(f"[Roll Error] Episode truncated due to excessive projected gravity, angle: {np.arccos(-projected_gravity[2]):.3f} rad, projected: {projected_gravity}")

            is_penetrated, geom1, geom2, dist = self.check_penetration(self.cfg.truncation.penetration_threshold)
            if is_penetrated:
                is_err = True
                if self.cfg.truncation.skip_penetration_geoms is not None and (
                    any(skip_geom in geom1.lower() for skip_geom in self.cfg.truncation.skip_penetration_geoms) or
                    any(skip_geom in geom2.lower() for skip_geom in self.cfg.truncation.skip_penetration_geoms)
                ):
                    is_err = False
                if self.cfg.truncation.skip_self_penetration:
                    if geom1.split('/')[0] == geom2.split('/')[0]:
                        is_err = False
                if is_err:
                    self.penetration_reset_count += 1
                    raise RuntimeError(f"[Penetration Error] Episode truncated: Penetration ({geom1} <-> {geom2}), distance: {dist}")
    
    def reset(self):
        """ Reset the simulator to initial state. """
        self.mj_physics.reset()
        if self.invert_yaw:
            self.mj_data.qpos[3] = 0.0
            self.mj_data.qpos[6] = 1.0
        self.mj_data.qpos[7:] = self.default_dof_pos
        mujoco.mj_forward(self.mj_model, self.mj_data)

        self.action = None
        if self.viewer is not None:
            self.viewer.sync()

    def setup_action(self,
            action: np.ndarray,
            p_gains: np.ndarray = None,
            d_gains: np.ndarray = None,
            control_type: Literal['P'] = 'P'
        ):
        """ Setup action to the simulator. """
        self.action = action
        self.p_gains = p_gains
        self.d_gains = d_gains
        self.control_type = control_type
    
    def update_torque(self):
        if self.action is None:
            return
        dof_pos = self.proprio.joint.pos
        dof_vel = self.proprio.joint.vel
        if self.control_type == 'P':
            torques = self.p_gains * (self.action - dof_pos) - self.d_gains * dof_vel
        else:
            raise NotImplementedError(f"Control type '{self.control_type}' not implemented.")
        self.mj_data.ctrl[:] = torques
    
    def close_viewer(self):
        """ Close the viewer and video writer. """
        if self.viewer is not None:
            self.viewer.close()
            self.viewer = None
            logger.info("Closing viewer.")
    
    def close_video_writer(self):
        """ Close the video writer if exists. """
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
        actuator_names = [mujoco.mj_id2name(self.mj_model, mujoco.mjtObj.mjOBJ_ACTUATOR, i) for i in range(self.mj_model.nu)]
        logger.info(
            f"""\nRobot XML: {self.robot_xml}\n"""
            f"""Robot joint names: {[x.rsplit('/')[-1] for x in self.dof_names]}\n"""
            f"""{'='*20} XML SENSOR NAMES {'='*20}\n"""
            f"""Joint Position Sensors [{len(self.joint_pos_sensor_names)}]: {[x.rsplit('/')[-1] for x in self.joint_pos_sensor_names]}\n"""
            f"""Joint Velocity Sensors [{len(self.joint_vel_sensor_names)}]: {[x.rsplit('/')[-1] for x in self.joint_vel_sensor_names]}\n"""
            f"""Joint Effort Sensors [{len(self.joint_eff_sensor_names)}]: {[x.rsplit('/')[-1] for x in self.joint_eff_sensor_names]}\n"""
            f"""Actuators [{len(actuator_names)}]: {[x.rsplit('/')[-1] for x in actuator_names]}\n"""
            f"""IMU Sensors: Quat{self.imu_quat}, AngVel{self.imu_ang_vel}, Acc{self.imu_acc}, Pos{self.imu_pos}, LinVel{self.imu_lin_vel}\n"""
            f"""!!!Checkout actuators order is consistent with joint sensors!!!\n"""
            f"{'='*58}"
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

    def debug_print_proprio_shapes(self):
        """Log shapes (or lengths) of each numpy vector inside a RobotProprioception.

        This helps debug mismatched sensor sizes between robots.
        """
        def _shape(x):
            try:
                arr = np.asarray(x)
                return arr.shape
            except Exception:
                return None

        jp = self.proprio.joint
        bs = self.proprio.base
        imu = self.proprio.imu

        logger.info("Proprioception shapes:")
        logger.info(f"  joint.pos: { _shape(jp.pos) }")
        logger.info(f"  joint.vel: { _shape(jp.vel) }")
        logger.info(f"  joint.torque: { _shape(jp.torque) }")

        logger.info(f"  base.pos: { _shape(bs.pos) }")
        logger.info(f"  base.quat: { _shape(bs.quat) }")
        logger.info(f"  base.vel: { _shape(bs.lin_vel) }")
        logger.info(f"  base.ang_vel: { _shape(bs.ang_vel) }")

        logger.info(f"  imu.quat: { _shape(imu.quat) }")
        logger.info(f"  imu.ang_vel: { _shape(imu.ang_vel) }")
        logger.info(f"  imu.acc: { _shape(imu.acc) }")
        logger.info(f"  imu.pos: { _shape(imu.pos) }")
        logger.info(f"  imu.lin_vel: { _shape(imu.lin_vel) }")

    def load_dof_limits(self):
        self.dof_limits = []
        self.dof_names = []
        for i in range(self.mj_model.njnt):
            name = mujoco.mj_id2name(self.mj_model, mujoco.mjtObj.mjOBJ_JOINT, i)
            jnt_type = self.mj_model.jnt_type[i]
            if jnt_type == mujoco.mjtJoint.mjJNT_FREE:
                continue
            limits = self.mj_model.jnt_range[i]
            self.dof_limits.append(limits)
            self.dof_names.append(name)
        self.dof_limits = np.array(self.dof_limits, np.float32)
