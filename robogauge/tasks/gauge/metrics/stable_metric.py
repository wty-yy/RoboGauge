# -*- coding: utf-8 -*-
'''
@File    : stable_metric.py
@Time    : 2025/12/18 20:18:33
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Stability-related metrics implementation
'''
import numpy as np

from robogauge.tasks.robots import RobotConfig
from robogauge.tasks.gauge.metrics.base_metric import BaseMetric, GoalData, SimData
from robogauge.utils.math_utils import get_projected_gravity

from robogauge.utils.logger import logger


class OrientationStabilityMetric(BaseMetric):
    """ Metric to log body orientation stability. """
    name = 'orientation_stability_metric'

    def __init__(self,
        robot_cfg: RobotConfig,
        **kwargs
    ):
        super().__init__(robot_cfg)
    
    def __call__(self, sim_data: SimData, goal_data: GoalData) -> float:
        projected_gravity = get_projected_gravity(sim_data.proprio.base.quat)
        projected_y = projected_gravity[1]
        metric_value = 1 - abs(projected_y)  # consider roll only
        logger.log(abs(projected_y), f'stable_metric/projected_y_abs', step=sim_data.n_step)
        return metric_value

class TorqueSmoothnessMetric(BaseMetric):
    """ Metric to log torque smoothness. """
    name = 'torque_smoothness_metric'

    def __init__(self,
        robot_cfg: RobotConfig,
        scaling_factor: float = 30.0,
        **kwargs
    ):
        super().__init__(robot_cfg)
        self.last_torque = None
        self.scaling_factor = scaling_factor
    
    def reset(self):
        self.last_torque = None
    
    def __call__(self, sim_data: SimData, goal_data: GoalData) -> float:
        current_torque = np.array(sim_data.proprio.joint.torque, np.float32)
        if self.last_torque is None:
            self.last_torque = current_torque
            return 1.0  # No change at first step
        torque_diff = current_torque - self.last_torque
        self.last_torque = current_torque
        rms_value = np.sqrt(np.mean(np.square(torque_diff)))
        metric_value = 1.0 - rms_value / self.scaling_factor
        logger.log(rms_value, f'stable_metric/torque_rms_diff', step=sim_data.n_step)
        return metric_value


def _normalize_name(name: str) -> str:
    if name is None:
        return ""
    return name.rsplit('/', 1)[-1]


class FrictionMarginMetric(BaseMetric):
    """ Metric to log the friction margin of the contacting feet. """
    name = 'friction_margin_metric'

    def __init__(self,
        robot_cfg: RobotConfig,
        foot_geom_names: list = None,
        force_threshold: float = 1e-6,
        **kwargs
    ):
        super().__init__(robot_cfg)
        if foot_geom_names is None:
            foot_geom_names = getattr(robot_cfg.assets, 'foot_geom_names', None)
        if foot_geom_names is None or len(foot_geom_names) == 0:
            raise ValueError(
                "[FrictionMarginMetric] foot_geom_names is required. "
                "Please configure robot_cfg.assets.foot_geom_names."
            )
        self.foot_geom_names = {_normalize_name(name) for name in foot_geom_names}
        self.force_threshold = force_threshold

    def __call__(self, sim_data: SimData, goal_data: GoalData) -> float:
        dynamics = sim_data.dynamics
        if dynamics is None or dynamics.contacts is None:
            raise RuntimeError("Friction margin metric requires sim_data.dynamics.contacts, but got None.")

        contacts = dynamics.contacts
        if contacts.positions.shape[0] == 0:
            logger.log(1.0, 'stable_metric/friction_margin', step=sim_data.n_step)
            logger.log(0.0, 'stable_metric/friction_margin_foot_count', step=sim_data.n_step)
            logger.log(0.0, 'stable_metric/friction_margin_contact_count', step=sim_data.n_step)
            logger.log(0.0, 'stable_metric/friction_margin_worst_utilization', step=sim_data.n_step)
            return 1.0

        foot_force_map = {}
        valid_contact_count = 0
        for idx, geom_name in enumerate(contacts.robot_geom_names):
            normalized_geom_name = _normalize_name(geom_name)
            if normalized_geom_name not in self.foot_geom_names:
                continue

            if normalized_geom_name not in foot_force_map:
                foot_force_map[normalized_geom_name] = {
                    'normal': 0.0,
                    'tangent': 0.0,
                    'friction_limit': 0.0,
                }

            normal_force = float(contacts.normal_forces[idx])
            tangent_force = float(contacts.tangent_forces[idx])
            friction_coeff = float(contacts.friction_coefficients[idx])
            foot_force_map[normalized_geom_name]['normal'] += normal_force
            foot_force_map[normalized_geom_name]['tangent'] += tangent_force
            foot_force_map[normalized_geom_name]['friction_limit'] += friction_coeff * normal_force
            valid_contact_count += 1

        if len(foot_force_map) == 0:
            logger.warning(
                f"Friction margin metric found no matching foot contacts using "
                f"foot_geom_names={sorted(self.foot_geom_names)}."
            )
            logger.log(1.0, 'stable_metric/friction_margin', step=sim_data.n_step)
            logger.log(0.0, 'stable_metric/friction_margin_foot_count', step=sim_data.n_step)
            logger.log(0.0, 'stable_metric/friction_margin_contact_count', step=sim_data.n_step)
            logger.log(0.0, 'stable_metric/friction_margin_worst_utilization', step=sim_data.n_step)
            return 1.0

        foot_margins = []
        foot_normal_forces = []
        utilization_values = []
        for foot_name, force_data in foot_force_map.items():
            if force_data['normal'] <= self.force_threshold:
                continue
            if force_data['friction_limit'] <= self.force_threshold:
                # logger.warning(
                #     f"Friction margin metric got too small friction limit on foot {foot_name}, returning 0 for this foot."
                # )
                foot_margins.append(0.0)
                foot_normal_forces.append(force_data['normal'])
                utilization_values.append(float('inf'))
                continue

            utilization = force_data['tangent'] / force_data['friction_limit']
            foot_margins.append(max(0.0, 1.0 - utilization))
            foot_normal_forces.append(force_data['normal'])
            utilization_values.append(utilization)

        if len(foot_margins) == 0:
            logger.log(1.0, 'stable_metric/friction_margin', step=sim_data.n_step)
            logger.log(0.0, 'stable_metric/friction_margin_foot_count', step=sim_data.n_step)
            logger.log(float(valid_contact_count), 'stable_metric/friction_margin_contact_count', step=sim_data.n_step)
            logger.log(0.0, 'stable_metric/friction_margin_worst_utilization', step=sim_data.n_step)
            return 1.0

        metric_value = float(np.average(foot_margins, weights=np.array(foot_normal_forces, dtype=np.float32)))
        worst_utilization = max(utilization_values)
        if not np.isfinite(worst_utilization):
            worst_utilization = 0.0
        logger.log(metric_value, 'stable_metric/friction_margin', step=sim_data.n_step)
        logger.log(float(len(foot_margins)), 'stable_metric/friction_margin_foot_count', step=sim_data.n_step)
        logger.log(float(valid_contact_count), 'stable_metric/friction_margin_contact_count', step=sim_data.n_step)
        logger.log(float(worst_utilization), 'stable_metric/friction_margin_worst_utilization', step=sim_data.n_step)
        return metric_value


def _cross_2d(o: np.ndarray, a: np.ndarray, b: np.ndarray) -> float:
    oa = a - o
    ob = b - o
    return float(oa[0] * ob[1] - oa[1] * ob[0])


def _convex_hull_2d(points: np.ndarray) -> np.ndarray:
    if points.shape[0] <= 1:
        return points.copy()
    pts = np.unique(points, axis=0)
    if pts.shape[0] <= 1:
        return pts
    pts = pts[np.lexsort((pts[:, 1], pts[:, 0]))]

    lower = []
    for point in pts:
        while len(lower) >= 2 and _cross_2d(lower[-2], lower[-1], point) <= 0.0:
            lower.pop()
        lower.append(point)

    upper = []
    for point in pts[::-1]:
        while len(upper) >= 2 and _cross_2d(upper[-2], upper[-1], point) <= 0.0:
            upper.pop()
        upper.append(point)

    hull = np.array(lower[:-1] + upper[:-1], dtype=np.float32)
    return hull if hull.size > 0 else pts[:1]


def _polygon_area_2d(points: np.ndarray) -> float:
    if points.shape[0] < 3:
        return 0.0
    x = points[:, 0]
    y = points[:, 1]
    return 0.5 * abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))


def _point_on_segment_2d(point: np.ndarray, start: np.ndarray, end: np.ndarray) -> bool:
    seg = end - start
    rel = point - start
    seg_norm_sq = float(np.dot(seg, seg))
    if seg_norm_sq == 0.0:
        return float(np.linalg.norm(rel)) == 0.0
    cross = abs(seg[0] * rel[1] - seg[1] * rel[0])
    if cross > 0.0:
        return False
    dot = float(np.dot(rel, seg))
    return 0.0 <= dot <= seg_norm_sq


def _point_in_support_region(point: np.ndarray, support_polygon: np.ndarray) -> bool:
    if support_polygon.shape[0] == 0:
        return False
    if support_polygon.shape[0] == 1:
        return float(np.linalg.norm(point - support_polygon[0])) == 0.0
    if support_polygon.shape[0] == 2:
        return _point_on_segment_2d(point, support_polygon[0], support_polygon[1])

    prev_sign = None
    for idx in range(support_polygon.shape[0]):
        start = support_polygon[idx]
        end = support_polygon[(idx + 1) % support_polygon.shape[0]]
        cross = _cross_2d(start, end, point)
        if cross == 0.0:
            continue
        cur_sign = cross > 0.0
        if prev_sign is None:
            prev_sign = cur_sign
        elif prev_sign != cur_sign:
            return False
    return True


class ZmpMarginMetric(BaseMetric):
    """ Zero Moment Point metric. """
    name = 'zmp_margin_metric'
    D_NORM_MIN = 1e-5

    def __init__(self,
        robot_cfg: RobotConfig,
        contact_threshold: float = 1e-3,
        force_threshold: float = 1e-6,
        draw_point: bool = False,
        draw_point_size: float = 0.03,
        draw_height_offset: float = 0.02,
        draw_point_rgba: list = None,
        **kwargs
    ):
        super().__init__(robot_cfg)
        self.contact_threshold = contact_threshold
        self.force_threshold = force_threshold
        self.draw_point = draw_point
        self.draw_point_size = draw_point_size
        self.draw_height_offset = draw_height_offset
        if draw_point_rgba is None:
            draw_point_rgba = [1.0, 0.85, 0.1, 1.0]
        self.draw_point_rgba = np.array(draw_point_rgba, dtype=np.float32)

    def _clear_zmp_visualization(self, sim_data: SimData):
        sim_data.visual.zmp_world_pos = None
        sim_data.visual.zmp_draw_enabled = self.draw_point
        sim_data.visual.zmp_draw_size = self.draw_point_size
        sim_data.visual.zmp_draw_height_offset = self.draw_height_offset
        sim_data.visual.zmp_draw_rgba = self.draw_point_rgba.copy()

    def _set_zmp_visualization(self, sim_data: SimData, zmp_world_pos: np.ndarray):
        sim_data.visual.zmp_world_pos = np.array(zmp_world_pos, dtype=np.float32)
        sim_data.visual.zmp_draw_enabled = self.draw_point
        sim_data.visual.zmp_draw_size = self.draw_point_size
        sim_data.visual.zmp_draw_height_offset = self.draw_height_offset
        sim_data.visual.zmp_draw_rgba = self.draw_point_rgba.copy()

    def _log_invalid(self, sim_data: SimData, contact_count: int = 0, metric_value: float = 1.0):
        self._clear_zmp_visualization(sim_data)
        logger.log(float(metric_value), 'stable_metric/zmp_margin', step=sim_data.n_step)
        logger.log(0.0, 'stable_metric/zmp_x', step=sim_data.n_step)
        logger.log(0.0, 'stable_metric/zmp_y', step=sim_data.n_step)
        logger.log(0.0, 'stable_metric/zmp_norm', step=sim_data.n_step)
        logger.log(0.0, 'stable_metric/zmp_d_norm', step=sim_data.n_step)
        logger.log(0.0, 'stable_metric/total_force_z', step=sim_data.n_step)
        logger.log(0.0, 'stable_metric/support_polygon_area', step=sim_data.n_step)
        logger.log(float(contact_count), 'stable_metric/support_contact_count', step=sim_data.n_step)
        logger.log(0.0, 'stable_metric/fzmp', step=sim_data.n_step)
        logger.log(0.0, 'stable_metric/zmp_valid', step=sim_data.n_step)

    def __call__(self, sim_data: SimData, goal_data: GoalData) -> float:
        dynamics = sim_data.dynamics
        if dynamics is None:
            raise RuntimeError("ZMP metric requires sim_data.dynamics, but got None.")

        rigid_bodies = dynamics.rigid_bodies
        if rigid_bodies is None or rigid_bodies.mass.shape[0] == 0:
            raise RuntimeError("ZMP metric requires non-empty dynamics.rigid_bodies.")

        contact_mask = dynamics.contacts.distances <= self.contact_threshold
        support_contacts = dynamics.contacts.positions[contact_mask]
        if support_contacts.shape[0] == 0:
            self._log_invalid(sim_data)
            return 1.0

        support_center = np.mean(support_contacts, axis=0)
        rel_com_pos = rigid_bodies.com_pos - support_center[None, :]

        gravity = np.asarray(dynamics.gravity, dtype=np.float32)
        body_forces = rigid_bodies.mass[:, None] * (gravity[None, :] - rigid_bodies.com_lin_acc)
        total_force = np.sum(body_forces, axis=0)
        total_force_z = float(total_force[2])
        if abs(total_force_z) < self.force_threshold:
            self._log_invalid(sim_data, contact_count=support_contacts.shape[0])
            return 1.0

        inertia_alpha = np.einsum('nij,nj->ni', rigid_bodies.inertia_world, rigid_bodies.ang_acc)
        inertia_omega = np.einsum('nij,nj->ni', rigid_bodies.inertia_world, rigid_bodies.ang_vel)
        gyro = np.cross(rigid_bodies.ang_vel, inertia_omega)
        body_moments = np.cross(rel_com_pos, body_forces) - (inertia_alpha + gyro)
        total_moment = np.sum(body_moments, axis=0)

        zmp_xy = np.array([
            -total_moment[1] / total_force_z,
            total_moment[0] / total_force_z
        ], dtype=np.float32)
        zmp_norm = float(np.linalg.norm(zmp_xy))

        if dynamics.default_diagonal_foot_distance is None:
            raise RuntimeError("ZMP metric requires dynamics.default_diagonal_foot_distance, but got None.")
        d_norm = float(dynamics.default_diagonal_foot_distance)
        if d_norm < self.D_NORM_MIN:
            logger.warning(
                f"ZMP metric got too small default_diagonal_foot_distance={d_norm:.8f} "
                f"(threshold={self.D_NORM_MIN:.1e}), returning 0.0."
            )
            self._log_invalid(
                sim_data,
                contact_count=support_contacts.shape[0],
                metric_value=0.0,
            )
            return 0.0

        metric_value = max(0.0, 1.0 - zmp_norm / d_norm)
        zmp_world_pos = np.array([
            support_center[0] + zmp_xy[0],
            support_center[1] + zmp_xy[1],
            support_center[2],
        ], dtype=np.float32)
        self._set_zmp_visualization(sim_data, zmp_world_pos)

        support_polygon = _convex_hull_2d(support_contacts[:, :2] - support_center[None, :2])
        support_area = _polygon_area_2d(support_polygon)
        is_inside_support = _point_in_support_region(zmp_xy, support_polygon)
        fzmp = 0.0 if is_inside_support else 1.0

        logger.log(metric_value, 'stable_metric/zmp_margin', step=sim_data.n_step)
        logger.log(float(zmp_xy[0]), 'stable_metric/zmp_x', step=sim_data.n_step)
        logger.log(float(zmp_xy[1]), 'stable_metric/zmp_y', step=sim_data.n_step)
        logger.log(zmp_norm, 'stable_metric/zmp_norm', step=sim_data.n_step)
        logger.log(d_norm, 'stable_metric/zmp_d_norm', step=sim_data.n_step)
        logger.log(total_force_z, 'stable_metric/total_force_z', step=sim_data.n_step)
        logger.log(float(support_contacts.shape[0]), 'stable_metric/support_contact_count', step=sim_data.n_step)
        logger.log(float(support_area), 'stable_metric/support_polygon_area', step=sim_data.n_step)
        logger.log(float(fzmp), 'stable_metric/fzmp', step=sim_data.n_step)
        logger.log(1.0, 'stable_metric/zmp_valid', step=sim_data.n_step)
        return metric_value
