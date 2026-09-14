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

    def test_missing_packaged_skill_is_an_error(self):
        err = io.StringIO()
        with patch.object(y, "packaged_skill_path", return_value=self.root / "missing.md"), redirect_stdout(io.StringIO()), redirect_stderr(err):
            code = y.main(["skill", "--json"])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(err.getvalue())["error"]["code"], "missing_skill")
