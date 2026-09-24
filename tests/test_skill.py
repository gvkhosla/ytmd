"""Packaged skill install from the running ytmd copy."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
from unittest.mock import patch

from test_ytmd import Isolated, y


class Skill(Isolated):
    def setUp(self):
        super().setUp()
        self.home = self.root / "home"
        self.home.mkdir()
        self.home_env = patch.dict(os.environ, {"HOME": str(self.home)})
        self.home_env.start()
        self.addCleanup(self.home_env.stop)

    def run_skill(self, *flags, json_mode=True):
        out, err = io.StringIO(), io.StringIO()
        argv = ["skill", *flags]
        if json_mode:
            argv.append("--json")
        with redirect_stdout(out), redirect_stderr(err):
            code = y.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_installs_shared_and_claude_skills_from_packaged_file(self):
        code, out, err = self.run_skill()
        self.assertEqual(code, 0, err)
        self.assertEqual(err, "")
        data = json.loads(out)
        self.assertEqual(data["status"], "installed")
        self.assertEqual(data["agent"], "all")
        self.assertEqual(data["version"], y.VERSION)
        self.assertTrue(Path(data["packaged"]).is_file())
        paths = [Path(item["path"]) for item in data["files"]]
        self.assertEqual(paths, [self.home / ".agents/skills/ytmd/SKILL.md", self.home / ".claude/skills/ytmd/SKILL.md"])
        for path in paths:
            self.assertTrue(path.is_file())
            self.assertEqual(path.read_bytes(), Path(data["packaged"]).read_bytes())

    def test_status_does_not_write(self):
        code, out, err = self.run_skill("--status")
        self.assertEqual(code, 0, err)
        data = json.loads(out)
        self.assertEqual(data["status"], "status")
        self.assertFalse((self.home / ".agents/skills/ytmd/SKILL.md").exists())

    def test_claude_only(self):
        code, out, err = self.run_skill("--agent", "claude")
        self.assertEqual(code, 0, err)
        data = json.loads(out)
        self.assertEqual(len(data["files"]), 1)
        self.assertTrue(str(data["files"][0]["path"]).endswith(".claude/skills/ytmd/SKILL.md"))
        self.assertFalse((self.home / ".agents/skills/ytmd/SKILL.md").exists())

    def test_installs_project_skills_without_writing_home(self):
        project = self.root / "project"
        project.mkdir()
        code, out, err = self.run_skill("--project", str(project))
        self.assertEqual(code, 0, err)
        data = json.loads(out)
        self.assertEqual(data["scope"], "project")
        self.assertEqual(data["project"], str(project.resolve()))
        paths = [Path(item["path"]) for item in data["files"]]
        resolved = project.resolve()
        self.assertEqual(paths, [resolved / ".agents/skills/ytmd/SKILL.md", resolved / ".claude/skills/ytmd/SKILL.md"])
        self.assertFalse((self.home / ".agents/skills/ytmd/SKILL.md").exists())
        for path in paths:
            self.assertEqual(path.read_bytes(), Path(data["packaged"]).read_bytes())

    def test_project_install_refuses_to_replace_changes_without_force(self):
        project = self.root / "project"
        stale = project / ".agents/skills/ytmd/SKILL.md"
        stale.parent.mkdir(parents=True)
        stale.write_text("local changes\n")
        code, out, err = self.run_skill("--project", str(project), "--agent", "shared")
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertEqual(json.loads(err)["error"]["code"], "skill_exists")
        self.assertEqual(stale.read_text(), "local changes\n")

        code, out, err = self.run_skill("--project", str(project), "--agent", "shared", "--force")
        self.assertEqual(code, 0, err)
        self.assertEqual(stale.read_bytes(), Path(json.loads(out)["packaged"]).read_bytes())

    def test_project_status_and_bad_directory_do_not_create_paths(self):
        project = self.root / "project"
        project.mkdir()
        code, out, err = self.run_skill("--project", str(project), "--status")
        self.assertEqual(code, 0, err)
        self.assertFalse((project / ".agents").exists())

        missing = self.root / "typo"
        code, out, err = self.run_skill("--project", str(missing))
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(err)["error"]["code"], "invalid_project")
        self.assertFalse(missing.exists())

    def test_project_install_does_not_follow_skill_paths_outside_project(self):
        project = self.root / "project"
        outside = self.root / "outside"
        project.mkdir()
        outside.mkdir()
        (project / ".agents").symlink_to(outside, target_is_directory=True)
        code, out, err = self.run_skill("--project", str(project), "--agent", "shared")
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(err)["error"]["code"], "unsafe_project_path")
        self.assertFalse((outside / "skills").exists())

    def test_missing_packaged_skill_is_an_error(self):
        err = io.StringIO()
        with patch.object(y, "packaged_skill_path", return_value=self.root / "missing.md"), redirect_stdout(io.StringIO()), redirect_stderr(err):
            code = y.main(["skill", "--json"])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(err.getvalue())["error"]["code"], "missing_skill")
