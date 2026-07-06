"""Headless tests for Scene + the editable scene template (no FreeCAD)."""

import unittest

from robotics_sim.demos import scene_template
from robotics_sim.scene import Scene


class TestScene(unittest.TestCase):
    def _scene(self):
        # No doc / no geometry_sync -> pure headless model.
        return scene_template.build(doc=None, geometry_sync_factory=None)

    def test_build_headless(self):
        scene = self._scene()
        self.assertIsInstance(scene, Scene)
        self.assertIn("block", scene.robot.model.links)
        self.assertEqual(scene.robot.time, 0.0)

    def test_step_makes_block_fall(self):
        scene = self._scene()
        start_z = scene.robot.model.links["block"].world_transform.translation[2]
        for _ in range(10):
            scene.step()
        z = scene.robot.model.links["block"].world_transform.translation[2]
        self.assertLess(z, start_z)
        self.assertGreater(scene.robot.time, 0.0)

    def test_reset_restores_start(self):
        scene = self._scene()
        start_z = scene.robot.model.links["block"].world_transform.translation[2]
        for _ in range(50):
            scene.step()
        scene.reset()
        z = scene.robot.model.links["block"].world_transform.translation[2]
        self.assertAlmostEqual(z, start_z)
        self.assertEqual(scene.robot.time, 0.0)

    def test_step_hook_logs_telemetry(self):
        # The template registers a throttled telemetry print via robot.log; any
        # subscriber (terminal panel / file logger) must receive lines on step.
        scene = self._scene()
        seen = []
        scene.robot.log_listeners.append(lambda v: seen.append(v))
        for _ in range(30):
            scene.step()
        self.assertTrue(seen, "expected telemetry lines from scene step hook")
        self.assertIn("block_height", seen[0])

    def test_reset_zeroes_gravity_velocity(self):
        # After reset the block must fall again from rest, not keep old velocity.
        scene = self._scene()
        for _ in range(50):
            scene.step()
        scene.reset()
        scene.step()  # one step from rest
        z = scene.robot.model.links["block"].world_transform.translation[2]
        start_z = scene.robot.model.links["block"].world_transform.translation[2]
        # velocity after a single dt from rest is small: drop << full-speed drop
        drop = scene._snapshot["links"]["block"].translation[2] - z
        self.assertLess(drop, 5.0)  # gentle first step, not a fast-moving body


if __name__ == "__main__":
    unittest.main()
