import json
import os
import plistlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "search_emoji.py"
WORKFLOW_PLIST = ROOT / "info.plist"


def run_search(query: str) -> dict:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), query],
        check=True,
        capture_output=True,
        encoding="utf-8",
    )
    return json.loads(completed.stdout)


class EmojiSearchTests(unittest.TestCase):
    def test_chinese_question_mark_returns_every_question_mark_emoji(self) -> None:
        payload = run_search("问号")

        self.assertEqual([item["arg"] for item in payload["items"]], ["❓", "❔", "⁉️"])

    def test_question_mark_symbol_returns_every_question_mark_emoji(self) -> None:
        payload = run_search("?")

        self.assertEqual([item["arg"] for item in payload["items"]], ["❓", "❔", "⁉️"])

    def test_english_name_search_returns_matching_emoji(self) -> None:
        payload = run_search("smile")

        self.assertIn("😀", [item["arg"] for item in payload["items"]])

    def test_result_copies_its_emoji_argument_when_selected(self) -> None:
        payload = run_search("问号")
        result = payload["items"][0]

        self.assertTrue(result["valid"])
        self.assertEqual(result["arg"], "❓")
        self.assertEqual(result["text"]["copy"], "❓")
        self.assertEqual(result["text"]["largetype"], "❓")

    def test_workflow_requires_a_space_after_emj(self) -> None:
        with WORKFLOW_PLIST.open("rb") as plist_file:
            workflow = plistlib.load(plist_file)

        script_filter = workflow["objects"][0]["config"]
        self.assertEqual(script_filter["keyword"], "emj")
        self.assertTrue(script_filter["withspace"])

    def test_script_filter_finds_its_assets_outside_the_workflow_directory(self) -> None:
        with WORKFLOW_PLIST.open("rb") as plist_file:
            workflow = plistlib.load(plist_file)
        command = workflow["objects"][0]["config"]["script"].replace("{query}", "?")

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            sync_root = temporary_path / "alfred"
            preferences_path = sync_root / "Alfred.alfredpreferences"
            workflows_path = preferences_path / "workflows"
            workflows_path.mkdir(parents=True)
            (workflows_path / "user.workflow.test").symlink_to(ROOT, target_is_directory=True)

            environment = os.environ.copy()
            environment["alfred_preferences"] = str(sync_root)
            completed = subprocess.run(
                ["/bin/zsh", "-c", command],
                check=True,
                cwd=temporary_path,
                env=environment,
                capture_output=True,
                encoding="utf-8",
            )

        payload = json.loads(completed.stdout)
        self.assertEqual([item["arg"] for item in payload["items"]], ["❓", "❔", "⁉️"])

    def test_script_filter_prefers_the_icloud_workflow_over_a_local_copy(self) -> None:
        with WORKFLOW_PLIST.open("rb") as plist_file:
            workflow = plistlib.load(plist_file)
        command = workflow["objects"][0]["config"]["script"].replace("{query}", "?")

        with tempfile.TemporaryDirectory() as temporary_directory:
            home_path = Path(temporary_directory) / "home"
            icloud_workflow = (
                home_path
                / "Library/Mobile Documents/com~apple~CloudDocs/alfred"
                / "Alfred.alfredpreferences/workflows/user.workflow.icloud"
            )
            local_preferences = home_path / "Library/Application Support/Alfred/Alfred.alfredpreferences"
            local_workflow = local_preferences / "workflows/user.workflow.local"

            for workflow_path, source in ((icloud_workflow, "icloud"), (local_workflow, "local")):
                workflow_path.mkdir(parents=True)
                (workflow_path / "info.plist").write_bytes(WORKFLOW_PLIST.read_bytes())
                runner = workflow_path / "run-search.sh"
                payload = json.dumps({"items": [{"arg": source}]})
                runner.write_text(
                    "#!/bin/zsh\nprint -r -- '{}'\n".format(payload),
                    encoding="utf-8",
                )
                runner.chmod(0o755)

            environment = os.environ.copy()
            environment["HOME"] = str(home_path)
            environment["alfred_preferences"] = str(local_preferences)
            completed = subprocess.run(
                ["/bin/zsh", "-c", command],
                check=True,
                cwd=home_path,
                env=environment,
                capture_output=True,
                encoding="utf-8",
            )

        self.assertEqual(json.loads(completed.stdout)["items"][0]["arg"], "icloud")


if __name__ == "__main__":
    unittest.main()
