"""Headless tests for kinematics + forward kinematics + sensor + gravity sim."""

import math
import unittest

from robotics_sim.kinematics import (
    Transform, rotation_from_axis_angle, joint_transform, forward_kinematics, normalize,
)
from robotics_sim.link_model import Link
from robotics_sim.joint_model import Joint
from robotics_sim.sensor_model import Sensor
from robotics_sim.robot_api import Robot
from robotics_sim.document_model import RobotModel
from robotics_sim.simulation import GravityBody


class TestTransform(unittest.TestCase):
    def test_identity_apply(self):
        t = Transform.identity()
        self.assertEqual(t.apply_point((1, 2, 3)), (1, 2, 3))

    def test_translation_compose(self):
        a = Transform.from_translation((1, 0, 0))
        b = Transform.from_translation((0, 2, 0))
        c = a.compose(b)
        self.assertEqual(c.translation, (1, 2, 0))

    def test_rotation_z_90(self):
        r = rotation_from_axis_angle((0, 0, 1), math.pi / 2)
        t = Transform(r)
        x, y, z = t.apply_point((1, 0, 0))
        self.assertAlmostEqual(x, 0, places=6)
        self.assertAlmostEqual(y, 1, places=6)
        self.assertAlmostEqual(z, 0, places=6)

    def test_normalize_zero_raises(self):
        with self.assertRaises(ValueError):
            normalize((0, 0, 0))


class TestJointTransform(unittest.TestCase):
    def test_prismatic(self):
        t = joint_transform("prismatic", (0, 0, 1), 5.0)
        self.assertAlmostEqual(t.translation[2], 5.0)

    def test_fixed(self):
        t = joint_transform("fixed", (0, 0, 1), 5.0)
        self.assertEqual(t.translation, (0, 0, 0))


class TestForwardKinematics(unittest.TestCase):
    def test_prismatic_chain(self):
        base = Link("base", world_transform=Transform.identity())
        arm = Link("arm")
        joint = Joint("j1", "prismatic", "base", "arm",
                      origin=Transform.from_translation((0, 0, 10)), axis=(0, 0, 1))
        world = forward_kinematics([base, arm], [joint], {"j1": 5.0})
        self.assertAlmostEqual(world["arm"].translation[2], 15.0)

    def test_root_keeps_world(self):
        base = Link("base", world_transform=Transform.from_translation((1, 2, 3)))
        world = forward_kinematics([base], [], {})
        self.assertEqual(world["base"].translation, (1, 2, 3))


class TestSensorAndGravity(unittest.TestCase):
    def _model(self, start_z=100.0):
        m = RobotModel("t")
        m.add_link(Link("block", world_transform=Transform.from_translation((0, 0, start_z))))
        m.add_sensor(Sensor("d", "distance", "block", max_range=1000.0, ground_height=0.0))
        return m

    def test_sensor_reads_height(self):
        robot = Robot(self._model(100.0))
        self.assertAlmostEqual(robot.read_sensor("d"), 100.0)

    def test_out_of_range(self):
        robot = Robot(self._model(5000.0))
        self.assertEqual(robot.read_sensor("d"), -1.0)

    def test_gravity_falls_to_ground(self):
        robot = Robot(self._model(500.0))
        GravityBody(robot, "block", gravity=-9810.0, ground_height=0.0).attach()
        for _ in range(1000):
            robot.step(0.01)
        self.assertAlmostEqual(robot.read_sensor("d"), 0.0, places=3)

    def test_motor_position_control(self):
        m = RobotModel("t")
        m.add_link(Link("a", world_transform=Transform.identity()))
        m.add_link(Link("b"))
        m.add_joint(Joint("j", "revolute", "a", "b", axis=(0, 0, 1),
                          lower_limit=-1.0, upper_limit=1.0))
        robot = Robot(m)
        robot.command_motor("j", target_position=0.5, max_speed=10.0)
        for _ in range(100):
            robot.step(0.01)
        self.assertAlmostEqual(robot.get_joint_position("j"), 0.5, places=3)

    def test_joint_clamp(self):
        m = RobotModel("t")
        m.add_link(Link("a"))
        m.add_link(Link("b"))
        m.add_joint(Joint("j", "revolute", "a", "b", lower_limit=-1.0, upper_limit=1.0))
        robot = Robot(m)
        robot.set_joint_position("j", 5.0)
        self.assertEqual(robot.get_joint_position("j"), 1.0)


if __name__ == "__main__":
    unittest.main()
