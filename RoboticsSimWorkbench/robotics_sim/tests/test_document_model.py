"""Headless tests for the document model: validation + JSON round-trip."""

import unittest

from robotics_sim.document_model import RobotModel, DuplicateNameError
from robotics_sim.link_model import Link
from robotics_sim.joint_model import Joint
from robotics_sim.sensor_model import Sensor
from robotics_sim.kinematics import Transform


class TestRobotModel(unittest.TestCase):
    def _model(self):
        m = RobotModel("bot")
        m.add_link(Link("base", objects=["Box"], world_transform=Transform.identity()))
        m.add_link(Link("arm", objects=["Cyl"]))
        m.add_joint(Joint("j1", "revolute", "base", "arm", axis=(0, 0, 1)))
        m.add_sensor(Sensor("s1", "distance", "arm"))
        return m

    def test_duplicate_link(self):
        m = RobotModel("bot")
        m.add_link(Link("a"))
        with self.assertRaises(DuplicateNameError):
            m.add_link(Link("a"))

    def test_joint_requires_links(self):
        m = RobotModel("bot")
        m.add_link(Link("a"))
        with self.assertRaises(ValueError):
            m.add_joint(Joint("j", "revolute", "a", "missing"))

    def test_backrefs(self):
        m = self._model()
        self.assertEqual(m.links["arm"].parent_joint, "j1")
        self.assertIn("j1", m.links["base"].child_joints)

    def test_rename_link_updates_joint(self):
        m = self._model()
        m.rename_link("arm", "forearm")
        self.assertEqual(m.joints["j1"].child_link, "forearm")
        self.assertEqual(m.sensors["s1"].attached_link, "forearm")

    def test_json_round_trip(self):
        m = self._model()
        m.joints["j1"].position = 0.7
        text = m.to_json()
        m2 = RobotModel.from_json(text)
        self.assertEqual(set(m2.links), {"base", "arm"})
        self.assertEqual(set(m2.joints), {"j1"})
        self.assertEqual(set(m2.sensors), {"s1"})
        self.assertAlmostEqual(m2.joints["j1"].position, 0.7)
        self.assertEqual(m2.links["base"].objects, ["Box"])

    def test_movable_joints(self):
        m = self._model()
        m.add_link(Link("tool"))
        m.add_joint(Joint("fixed1", "fixed", "arm", "tool"))
        movable = [j.name for j in m.movable_joints()]
        self.assertEqual(movable, ["j1"])


if __name__ == "__main__":
    unittest.main()
