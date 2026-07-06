"""Headless tests for URDF + MJCF exporters (structural validity)."""

import unittest
import xml.etree.ElementTree as ET

from robotics_sim.document_model import RobotModel
from robotics_sim.link_model import Link
from robotics_sim.joint_model import Joint
from robotics_sim.kinematics import Transform
from robotics_sim.exporters import export_urdf, export_mjcf


def _model():
    m = RobotModel("bot")
    m.add_link(Link("base", objects=["Box"], world_transform=Transform.identity()))
    m.add_link(Link("arm", objects=["Cyl"],
                     world_transform=Transform.from_translation((0, 0, 100))))
    m.add_joint(Joint("j1", "revolute", "base", "arm", axis=(0, 0, 1),
                      origin=Transform.from_translation((0, 0, 100)),
                      lower_limit=-1.5, upper_limit=1.5))
    return m


class TestURDF(unittest.TestCase):
    def test_valid_xml_and_content(self):
        xml = export_urdf(_model())
        root = ET.fromstring(xml)
        self.assertEqual(root.tag, "robot")
        self.assertEqual(root.get("name"), "bot")
        links = [l.get("name") for l in root.findall("link")]
        self.assertEqual(set(links), {"base", "arm"})
        joints = root.findall("joint")
        self.assertEqual(len(joints), 1)
        self.assertEqual(joints[0].get("type"), "revolute")
        self.assertIsNotNone(joints[0].find("axis"))
        self.assertIsNotNone(joints[0].find("limit"))

    def test_fixed_joint_no_axis(self):
        m = RobotModel("b")
        m.add_link(Link("a"))
        m.add_link(Link("c"))
        m.add_joint(Joint("f", "fixed", "a", "c"))
        root = ET.fromstring(export_urdf(m))
        j = root.find("joint")
        self.assertIsNone(j.find("axis"))


class TestMJCF(unittest.TestCase):
    def test_valid_xml_and_tree(self):
        xml = export_mjcf(_model())
        root = ET.fromstring(xml)
        self.assertEqual(root.tag, "mujoco")
        world = root.find("worldbody")
        self.assertIsNotNone(world)
        base = world.find("body")
        self.assertEqual(base.get("name"), "base")
        # arm nested under base
        arm = base.find("body")
        self.assertEqual(arm.get("name"), "arm")
        joint = arm.find("joint")
        self.assertEqual(joint.get("type"), "hinge")

    def test_prismatic_is_slide(self):
        m = RobotModel("b")
        m.add_link(Link("a"))
        m.add_link(Link("c"))
        m.add_joint(Joint("p", "prismatic", "a", "c", axis=(1, 0, 0),
                          lower_limit=0, upper_limit=100))
        root = ET.fromstring(export_mjcf(m))
        joint = root.find("worldbody/body/body/joint")
        self.assertEqual(joint.get("type"), "slide")


if __name__ == "__main__":
    unittest.main()
