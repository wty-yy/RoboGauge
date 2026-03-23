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
    RobotProprioception, JointState, BaseState, IMUState,
    RigidBodyDynamics, GroundContactState, DynamicsState, VisualState
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
        self.robot_name_prefix = None
        self.robot_body_ids = None
        self.robot_body_id_set = set()
        self.dynamic_body_ids = None
        self.dynamic_body_names = []
        self.dynamic_body_mass = None
        self.dynamic_body_inertia_local = None
        self.dynamic_body_iquat = None
        self.foot_body_ids = None
        self.default_diagonal_foot_distance = 0.0
        self.prev_body_com_pos = None
        self.prev_body_rot = None
        self.prev_body_com_lin_vel = None
        self.prev_body_ang_vel = None
        self.zmp_world_pos = None
        self.zmp_draw_enabled = False
        self.zmp_draw_size = 0.03
        self.zmp_draw_height_offset = 0.02
        self.zmp_draw_rgba = np.array([1.0, 0.85, 0.1, 1.0], dtype=np.float32)

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
        robot_base = robot_mjcf.find('body', 'base_link')
        if robot_base is not None:
            origin_robot_height = robot_base.pos.copy() if robot_base.pos is not None else None
            robot_base.pos = [0, 0, 0]  # move base_link translation to terrain_spawn_pos
        else:
            raise ValueError("Robot base_link body not found in the robot MJCF model.")
        attachment_frame = terrain_mjcf.attach(robot_mjcf)
        attachment_frame.add('freejoint', name='root')
        if origin_robot_height is not None:
            terrain_spawn_pos = np.array(terrain_spawn_pos) + origin_robot_height
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
        self.robot_name_prefix = f'{robot_mjcf.model}/'

        # Domain randomization: base mass
        base_body_name = f'{robot_mjcf.model}/base_link'
        body_id = mujoco.mj_name2id(self.mj_model, mujoco.mjtObj.mjOBJ_BODY, base_body_name)
        assert body_id != -1, f"Body '{base_body_name}' not found in the model."
        if self.cfg.domain_rand.base_mass != 0.0:
            original_mass = self.mj_model.body_mass[body_id]
            new_mass = max(0.01, original_mass + self.cfg.domain_rand.base_mass)
            self.mj_model.body_mass[body_id] = new_mass
            logger.info(f"Randomized base mass: {original_mass:.3f} -> {new_mass:.3f} kg")
        
        # Domain randomization: friction
        if self.cfg.domain_rand.friction != 0.0:
            for i in range(self.mj_model.ngeom):
                # Both change robot friction and terrain friction
                # If one of the two geoms has higher priority, the friction of that geom is used.
                # If both geoms have the save priopirty, the maximum of the two friction is used.
                # (Go2 foot friction is 0.4 and priority is 1, terrain priority is 0 except floor)
                self.mj_model.geom_friction[i][0] = self.cfg.domain_rand.friction
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
        self.preload_dynamics_data()
        self.reset_dynamics_cache()

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
        dynamics = self.get_dynamics_data()
        visual = VisualState()

        sim_data = SimData(
            n_step=self.n_step,
            sim_dt=self.sim_dt,
            sim_time=self.sim_time,
            proprio=proprio,
            dynamics=dynamics,
            visual=visual,
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

        def add_zmp_sphere(geom_elem):
            zmp_pos = np.array(self.zmp_world_pos, dtype=np.float32).copy()
            zmp_pos[2] += self.zmp_draw_height_offset
            mujoco.mjv_initGeom(
                geom_elem,
                type=mujoco.mjtGeom.mjGEOM_SPHERE,
                size=[self.zmp_draw_size, 0, 0],
                pos=zmp_pos,
                mat=np.eye(3).flatten(),
                rgba=np.array(self.zmp_draw_rgba, dtype=np.float32)
            )

        def add_thick_arrow(geom_elem, pos, vec, rgba, scale=0.7):
            vel_norm = np.linalg.norm(vec)
            display_norm = min(vel_norm * scale, 1.0)

            if display_norm < 0.10:
                mujoco.mjv_initGeom(
                    geom_elem,
                    type=mujoco.mjtGeom.mjGEOM_NONE,
                    size=[0,0,0], pos=pos, mat=np.eye(3).flatten(), rgba=[0,0,0,0]
                )
                return

            mat = np.zeros(9)
            target_quat = np.zeros(4)
            vec_normalized = vec / vel_norm
            mujoco.mju_quatZ2Vec(target_quat, vec_normalized)
            mujoco.mju_quat2Mat(mat, target_quat)
            
            mat = mat.reshape(3, 3)
            mat[:, 2] *= display_norm 
            
            mujoco.mjv_initGeom(
                geom_elem,
                type=mujoco.mjtGeom.mjGEOM_ARROW,
                size=[0.02, 0.02, display_norm], # [height, width, length]
                pos=pos,
                mat=mat.flatten(),
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

        if self.zmp_draw_enabled and self.zmp_world_pos is not None:
            if ctype == 'viewer':
                add_zmp_sphere(handle.user_scn.geoms[viewer_geom_idx])
                viewer_geom_idx += 1
            else:
                handle.scene.ngeom += 1
                add_zmp_sphere(handle.scene.geoms[self.renderer.scene.ngeom - 1])
        
        if self.target_velocity is not None:
            base_pos_world = self.mj_data.qpos[:3]
            base_quat = self.mj_data.qpos[3:7]
            
            # rendering arrows start position
            offset_body = np.array([0.0, 0.0, 0.2])
            offset_world = np.zeros(3)
            mujoco.mju_rotVecQuat(offset_world, offset_body, base_quat)
            start_pos = base_pos_world + offset_world

            tgt_vel_body = np.array([self.target_velocity.lin_vel_x, self.target_velocity.lin_vel_y, 0.0])
            
            raw_cur_vel = self.proprio.base.lin_vel
            cur_vel_body = np.array([raw_cur_vel[0], raw_cur_vel[1], 0.0])

            tgt_vel_world = np.zeros(3)
            cur_vel_world = np.zeros(3)
            mujoco.mju_rotVecQuat(tgt_vel_world, tgt_vel_body, base_quat)
            if ctype == 'viewer':
                mujoco.mju_rotVecQuat(cur_vel_world, cur_vel_body, base_quat)
            else:
                mujoco.mju_rotVecQuat(cur_vel_world, cur_vel_body, base_quat)

            COLOR_CMD = [0, 1, 0, 1]   # Green 0x00ff00
            COLOR_REAL = [0, 0, 1, 1]  # Blue  0x0000ff

            if ctype == 'viewer':
                # Cmd Arrow
                add_thick_arrow(handle.user_scn.geoms[viewer_geom_idx], start_pos, tgt_vel_world, COLOR_CMD)
                viewer_geom_idx += 1
                # Real Arrow
                add_thick_arrow(handle.user_scn.geoms[viewer_geom_idx], start_pos, cur_vel_world, COLOR_REAL)
                viewer_geom_idx += 1
            else:
                # Renderer Append
                handle.scene.ngeom += 1
                add_thick_arrow(handle.scene.geoms[handle.scene.ngeom - 1], start_pos, tgt_vel_world, COLOR_CMD)
                handle.scene.ngeom += 1
                add_thick_arrow(handle.scene.geoms[handle.scene.ngeom - 1], start_pos, cur_vel_world, COLOR_REAL)

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
        self.reset_dynamics_cache()

        self.action = None
        self.zmp_world_pos = None
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
        if len(found) == 0:
            logger.warning(f"No sensors found for pattern='{pattern}' tag_name='{tag_name}'")
        return found

    def get_sensor_data(self, cache_key: str) -> np.ndarray:
        ids = self.sensor_cache.get(cache_key, [])
        if not ids:
            return np.array([])

        data_list = []
        for adr, dim in ids:
            data_list.append(self.mj_data.sensordata[adr:adr+dim])
        return np.concatenate(data_list)

    def update_visuals(self, sim_data: SimData):
        visual = sim_data.visual
        if visual is None:
            self.zmp_world_pos = None
            self.zmp_draw_enabled = False
            return

        self.zmp_world_pos = visual.zmp_world_pos
        self.zmp_draw_enabled = bool(visual.zmp_draw_enabled)
        self.zmp_draw_size = float(visual.zmp_draw_size)
        self.zmp_draw_height_offset = float(visual.zmp_draw_height_offset)
        if visual.zmp_draw_rgba is not None:
            self.zmp_draw_rgba = np.array(visual.zmp_draw_rgba, dtype=np.float32)

    @staticmethod
    def _quat_to_rotmat(quat: np.ndarray) -> np.ndarray:
        quat = np.asarray(quat, dtype=np.float64)
        if quat.ndim == 1:
            quat = quat[None, :]
        quat_norm = np.linalg.norm(quat, axis=1, keepdims=True)
        quat_norm = np.maximum(quat_norm, 1e-12)
        quat = quat / quat_norm
        w, x, y, z = quat[:, 0], quat[:, 1], quat[:, 2], quat[:, 3]
        rot = np.empty((quat.shape[0], 3, 3), dtype=np.float32)
        rot[:, 0, 0] = 1.0 - 2.0 * (y * y + z * z)
        rot[:, 0, 1] = 2.0 * (x * y - z * w)
        rot[:, 0, 2] = 2.0 * (x * z + y * w)
        rot[:, 1, 0] = 2.0 * (x * y + z * w)
        rot[:, 1, 1] = 1.0 - 2.0 * (x * x + z * z)
        rot[:, 1, 2] = 2.0 * (y * z - x * w)
        rot[:, 2, 0] = 2.0 * (x * z - y * w)
        rot[:, 2, 1] = 2.0 * (y * z + x * w)
        rot[:, 2, 2] = 1.0 - 2.0 * (x * x + y * y)
        return rot

    @staticmethod
    def _rotation_delta_to_angular_velocity(
            prev_rot: np.ndarray,
            cur_rot: np.ndarray,
            dt: float
        ) -> np.ndarray:
        ang_vel = np.zeros((cur_rot.shape[0], 3), dtype=np.float32)
        if prev_rot is None or dt <= 0.0:
            return ang_vel

        rot_delta = cur_rot @ np.transpose(prev_rot, (0, 2, 1))
        traces = np.trace(rot_delta, axis1=1, axis2=2)
        cos_theta = np.clip((traces - 1.0) * 0.5, -1.0, 1.0)
        theta = np.arccos(cos_theta)
        skew = np.stack([
            rot_delta[:, 2, 1] - rot_delta[:, 1, 2],
            rot_delta[:, 0, 2] - rot_delta[:, 2, 0],
            rot_delta[:, 1, 0] - rot_delta[:, 0, 1],
        ], axis=1)

        small_mask = theta < 1e-6
        if np.any(small_mask):
            ang_vel[small_mask] = 0.5 * skew[small_mask] / dt

        normal_mask = ~small_mask
        if np.any(normal_mask):
            idx = np.where(normal_mask)[0]
            sin_theta = np.sin(theta[idx])
            singular_mask = np.abs(sin_theta) < 1e-6
            if np.any(singular_mask):
                singular_idx = idx[singular_mask]
                ang_vel[singular_idx] = 0.5 * skew[singular_idx] / dt
            regular_idx = idx[~singular_mask]
            if regular_idx.size > 0:
                axis = skew[regular_idx] / (2.0 * sin_theta[~singular_mask, None])
                ang_vel[regular_idx] = axis * theta[regular_idx, None] / dt
        return ang_vel

    @staticmethod
    def _max_pairwise_xy_distance(positions: np.ndarray) -> float:
        if positions.shape[0] < 2:
            return 0.0
        xy = positions[:, :2]
        diffs = xy[:, None, :] - xy[None, :, :]
        dist = np.linalg.norm(diffs, axis=-1)
        return float(np.max(dist))

    def _get_body_name(self, body_id: int) -> str:
        if body_id == 0:
            return "worldbody"
        name = mujoco.mj_id2name(self.mj_model, mujoco.mjtObj.mjOBJ_BODY, body_id)
        return name if name is not None else f"body_{body_id}"

    def _get_geom_name(self, geom_id: int) -> str:
        name = mujoco.mj_id2name(self.mj_model, mujoco.mjtObj.mjOBJ_GEOM, geom_id)
        return name if name is not None else f"geom_{geom_id}"

    def reset_dynamics_cache(self):
        self.prev_body_com_pos = None
        self.prev_body_rot = None
        self.prev_body_com_lin_vel = None
        self.prev_body_ang_vel = None

    def preload_dynamics_data(self):
        self.robot_body_ids = []
        robot_body_names = []
        for body_id in range(self.mj_model.nbody):
            body_name = mujoco.mj_id2name(self.mj_model, mujoco.mjtObj.mjOBJ_BODY, body_id)
            if body_name is not None and body_name.startswith(self.robot_name_prefix):
                self.robot_body_ids.append(body_id)
                robot_body_names.append(body_name)
        self.robot_body_ids = np.array(self.robot_body_ids, dtype=np.int32)
        self.robot_body_id_set = set(int(body_id) for body_id in self.robot_body_ids.tolist())

        if self.robot_body_ids.size == 0:
            logger.warning("No robot bodies found for dynamics preprocessing.")
            self.dynamic_body_ids = np.array([], dtype=np.int32)
            self.dynamic_body_names = []
            self.dynamic_body_mass = np.zeros((0,), dtype=np.float32)
            self.dynamic_body_inertia_local = np.zeros((0, 3), dtype=np.float32)
            self.dynamic_body_iquat = np.zeros((0, 4), dtype=np.float32)
            self.foot_body_ids = np.array([], dtype=np.int32)
            self.default_diagonal_foot_distance = 0.0
            return

        robot_body_mass = np.array(self.mj_model.body_mass[self.robot_body_ids], dtype=np.float32)
        dynamic_mask = robot_body_mass > 0.0
        self.dynamic_body_ids = self.robot_body_ids[dynamic_mask]
        self.dynamic_body_names = [
            robot_body_names[idx]
            for idx, is_dynamic in enumerate(dynamic_mask.tolist())
            if is_dynamic
        ]
        self.dynamic_body_mass = np.array(self.mj_model.body_mass[self.dynamic_body_ids], dtype=np.float32)
        self.dynamic_body_inertia_local = np.array(self.mj_model.body_inertia[self.dynamic_body_ids], dtype=np.float32)
        if hasattr(self.mj_model, 'body_iquat'):
            self.dynamic_body_iquat = np.array(self.mj_model.body_iquat[self.dynamic_body_ids], dtype=np.float32)
        else:
            self.dynamic_body_iquat = np.tile(np.array([[1.0, 0.0, 0.0, 0.0]], dtype=np.float32), (len(self.dynamic_body_ids), 1))

        self.foot_body_ids = np.array([
            body_id for body_id, body_name in zip(self.robot_body_ids.tolist(), robot_body_names)
            if 'foot' in body_name.rsplit('/', 1)[-1].lower()
        ], dtype=np.int32)
        self.default_diagonal_foot_distance = self.compute_default_diagonal_foot_distance()
        logger.info(
            f"Dynamics preprocessing: robot_bodies={len(self.robot_body_ids)}, "
            f"dynamic_bodies={len(self.dynamic_body_ids)}, foot_bodies={len(self.foot_body_ids)}, "
            f"default_diagonal_foot_distance={self.default_diagonal_foot_distance:.4f}"
        )

    def compute_default_diagonal_foot_distance(self) -> float:
        if self.foot_body_ids is not None and self.foot_body_ids.size >= 2:
            if hasattr(self.mj_data, 'xpos'):
                foot_pos = np.array(self.mj_data.xpos[self.foot_body_ids], dtype=np.float32)
            else:
                foot_pos = np.array(self.mj_data.xipos[self.foot_body_ids], dtype=np.float32)
            return self._max_pairwise_xy_distance(foot_pos)

        contacts = self.get_ground_contact_state()
        if contacts.positions.shape[0] >= 2:
            return self._max_pairwise_xy_distance(contacts.positions)
        return 0.0

    def get_ground_contact_state(self) -> GroundContactState:
        positions = []
        distances = []
        normal_forces = []
        tangent_forces = []
        friction_coefficients = []
        robot_geom_names = []
        other_geom_names = []
        robot_body_names = []
        other_body_names = []

        for i in range(self.mj_data.ncon):
            contact = self.mj_data.contact[i]
            geom1 = int(contact.geom1)
            geom2 = int(contact.geom2)
            body1 = int(self.mj_model.geom_bodyid[geom1])
            body2 = int(self.mj_model.geom_bodyid[geom2])
            is_robot1 = body1 in self.robot_body_id_set
            is_robot2 = body2 in self.robot_body_id_set
            if is_robot1 == is_robot2:
                continue

            robot_geom = geom1 if is_robot1 else geom2
            other_geom = geom2 if is_robot1 else geom1
            robot_body = body1 if is_robot1 else body2
            other_body = body2 if is_robot1 else body1

            contact_force = np.zeros(6, dtype=np.float64)
            mujoco.mj_contactForce(self.mj_model, self.mj_data, i, contact_force)
            friction = np.array(contact.friction, dtype=np.float32).reshape(-1)

            positions.append(np.array(contact.pos, dtype=np.float32))
            distances.append(float(contact.dist))
            normal_forces.append(float(abs(contact_force[0])))
            tangent_forces.append(float(np.linalg.norm(contact_force[1:3])))
            friction_coefficients.append(float(friction[0]) if friction.size > 0 else 0.0)
            robot_geom_names.append(self._get_geom_name(robot_geom))
            other_geom_names.append(self._get_geom_name(other_geom))
            robot_body_names.append(self._get_body_name(robot_body))
            other_body_names.append(self._get_body_name(other_body))

        positions = np.array(positions, dtype=np.float32).reshape(-1, 3)
        distances = np.array(distances, dtype=np.float32)
        normal_forces = np.array(normal_forces, dtype=np.float32)
        tangent_forces = np.array(tangent_forces, dtype=np.float32)
        friction_coefficients = np.array(friction_coefficients, dtype=np.float32)
        return GroundContactState(
            positions=positions,
            distances=distances,
            normal_forces=normal_forces,
            tangent_forces=tangent_forces,
            friction_coefficients=friction_coefficients,
            robot_geom_names=robot_geom_names,
            other_geom_names=other_geom_names,
            robot_body_names=robot_body_names,
            other_body_names=other_body_names,
        )

    def get_dynamics_data(self) -> DynamicsState:
        if self.dynamic_body_ids is None or self.dynamic_body_ids.size == 0:
            empty_body = RigidBodyDynamics(
                names=[],
                mass=np.zeros((0,), dtype=np.float32),
                com_pos=np.zeros((0, 3), dtype=np.float32),
                com_lin_vel=np.zeros((0, 3), dtype=np.float32),
                com_lin_acc=np.zeros((0, 3), dtype=np.float32),
                ang_vel=np.zeros((0, 3), dtype=np.float32),
                ang_acc=np.zeros((0, 3), dtype=np.float32),
                inertia_world=np.zeros((0, 3, 3), dtype=np.float32),
            )
            return DynamicsState(
                gravity=np.array(self.mj_model.opt.gravity, dtype=np.float32),
                rigid_bodies=empty_body,
                contacts=self.get_ground_contact_state(),
                default_diagonal_foot_distance=float(self.default_diagonal_foot_distance),
            )

        com_pos = np.array(self.mj_data.xipos[self.dynamic_body_ids], dtype=np.float32)
        body_rot = np.array(self.mj_data.xmat[self.dynamic_body_ids], dtype=np.float32).reshape(-1, 3, 3)
        com_lin_vel = np.zeros_like(com_pos)
        com_lin_acc = np.zeros_like(com_pos)
        ang_vel = np.zeros_like(com_pos)
        ang_acc = np.zeros_like(com_pos)

        if self.prev_body_com_pos is not None:
            com_lin_vel = (com_pos - self.prev_body_com_pos) / self.sim_dt
            if self.prev_body_com_lin_vel is not None:
                com_lin_acc = (com_lin_vel - self.prev_body_com_lin_vel) / self.sim_dt
        if self.prev_body_rot is not None:
            ang_vel = self._rotation_delta_to_angular_velocity(self.prev_body_rot, body_rot, self.sim_dt)
            if self.prev_body_ang_vel is not None:
                ang_acc = (ang_vel - self.prev_body_ang_vel) / self.sim_dt

        if hasattr(self.mj_data, 'ximat'):
            inertial_rot = np.array(self.mj_data.ximat[self.dynamic_body_ids], dtype=np.float32).reshape(-1, 3, 3)
        else:
            inertial_rot = body_rot @ self._quat_to_rotmat(self.dynamic_body_iquat)
        inertia_local = np.zeros((self.dynamic_body_ids.size, 3, 3), dtype=np.float32)
        inertia_local[:, 0, 0] = self.dynamic_body_inertia_local[:, 0]
        inertia_local[:, 1, 1] = self.dynamic_body_inertia_local[:, 1]
        inertia_local[:, 2, 2] = self.dynamic_body_inertia_local[:, 2]
        inertia_world = inertial_rot @ inertia_local @ np.transpose(inertial_rot, (0, 2, 1))

        self.prev_body_com_pos = com_pos.copy()
        self.prev_body_rot = body_rot.copy()
        self.prev_body_com_lin_vel = com_lin_vel.copy()
        self.prev_body_ang_vel = ang_vel.copy()

        return DynamicsState(
            gravity=np.array(self.mj_model.opt.gravity, dtype=np.float32),
            rigid_bodies=RigidBodyDynamics(
                names=self.dynamic_body_names,
                mass=self.dynamic_body_mass.copy(),
                com_pos=com_pos,
                com_lin_vel=com_lin_vel,
                com_lin_acc=com_lin_acc,
                ang_vel=ang_vel,
                ang_acc=ang_acc,
                inertia_world=inertia_world,
            ),
            contacts=self.get_ground_contact_state(),
            default_diagonal_foot_distance=float(self.default_diagonal_foot_distance),
        )

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
