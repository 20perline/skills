import contextlib
import importlib
import io
import sys
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).parents[1] / "skills" / "volcengine-cv" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

video = importlib.import_module("video")


class BuildBodyTests(unittest.TestCase):
    def test_valid_batch_options_are_preserved(self):
        body = video.build_body(
            {
                "mode": "t2v",
                "prompt": "test",
                "aspect_ratio": "16:9",
                "frames": 121,
            }
        )

        self.assertEqual(body["aspect_ratio"], "16:9")
        self.assertEqual(body["frames"], 121)

    def test_invalid_batch_aspect_ratio_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "无效的视频宽高比"):
            video.build_body(
                {
                    "mode": "t2v",
                    "prompt": "test",
                    "aspect_ratio": "2:1",
                }
            )

    def test_invalid_batch_frame_count_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "无效的视频帧数"):
            video.build_body(
                {
                    "mode": "t2v",
                    "prompt": "test",
                    "frames": 120,
                }
            )

    def test_invalid_batch_camera_strength_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "无效的运镜强度"):
            video.build_body(
                {
                    "mode": "i2v-camera",
                    "prompt": "test",
                    "image_url": "https://example.com/image.png",
                    "template_id": "dynamic_orbit",
                    "camera_strength": "extreme",
                }
            )

    def test_invalid_batch_options_do_not_submit_a_task(self):
        output = io.StringIO()

        with (
            mock.patch.object(video, "submit_task") as submit_task,
            contextlib.redirect_stderr(output),
        ):
            result = video.generate_one(
                {
                    "mode": "t2v",
                    "prompt": "test",
                    "frames": 120,
                },
                Path("."),
                "ak",
                "sk",
            )

        submit_task.assert_not_called()
        self.assertIsNone(result["task_id"])
        self.assertIn("无效的视频帧数", result["error"])
        self.assertIn("参数错误", output.getvalue())


if __name__ == "__main__":
    unittest.main()
