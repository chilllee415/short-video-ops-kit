from __future__ import annotations
import json, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import fetch_account_data
import publish_report

class PipelineTest(unittest.TestCase):
    def run_script(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, *arguments], cwd=ROOT, check=True, text=True, capture_output=True)

    def test_demo_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root, analysis_input, final, site = Path(raw), Path(raw)/"input.json", Path(raw)/"final.json", Path(raw)/"site"
            self.run_script("scripts/analyze_comments.py", "--input", "examples/demo-collected.json", "--output", str(analysis_input))
            self.run_script("scripts/finalize_analysis.py", "--input", str(analysis_input), "--findings", "examples/demo-findings.json", "--output", str(final))
            self.run_script("scripts/publish_report.py", "--account", "demo_account", "--data", str(final), "--output-dir", str(site))
            index = json.loads((site/"comment-insight-index.json").read_text(encoding="utf-8"))
            self.assertEqual(index["reports"][0]["commentCount"], 5)
            detail = (site/"demo_account.html").read_text(encoding="utf-8")
            self.assertIn("示例创作者", detail)
            self.assertNotIn("private_real_account", detail)
            self.assertIn("AI GENERATED CONCLUSION", detail)
            self.assertIn("用户需求画像", detail)
            self.assertIn("profile-ranked", detail)
            self.assertIn("profile-rank-track", detail)
            self.assertIn("评论类型分层", detail)
            self.assertIn("高赞评论排行", detail)
            self.assertIn("profile-summary-canonical", detail)
            self.assertIn(".opportunity .evidence{display:none}", detail)
            template = (ROOT/"assets/templates/report.html").read_text(encoding="utf-8")
            start, end = "/* INSIGHT_DATA_START */", "/* INSIGHT_DATA_END */"
            template_shell = template.split(start, 1)[0] + start + end + template.split(end, 1)[1]
            detail_shell = detail.split(start, 1)[0] + start + end + detail.split(end, 1)[1]
            self.assertEqual(template_shell, detail_shell)

    def test_invalid_evidence_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            analysis_input, findings, output = Path(raw)/"input.json", Path(raw)/"findings.json", Path(raw)/"output.json"
            self.run_script("scripts/analyze_comments.py", "--input", "examples/demo-collected.json", "--output", str(analysis_input))
            payload = json.loads((ROOT/"examples/demo-findings.json").read_text(encoding="utf-8")); payload["viewpoints"][0]["evidenceCommentIds"] = ["missing-comment"]
            findings.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            result = subprocess.run([sys.executable, "scripts/finalize_analysis.py", "--input", str(analysis_input), "--findings", str(findings), "--output", str(output)], cwd=ROOT, text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0); self.assertIn("missing-comment", result.stderr + result.stdout)

    def test_publish_rejects_path_traversal_account(self) -> None:
        result = subprocess.run([sys.executable, "scripts/publish_report.py", "--account", "../outside", "--data", "examples/demo-findings.json"], cwd=ROOT, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("账号只能包含", result.stderr + result.stdout)

    def test_nested_avatar_url_is_supported(self) -> None:
        url = "https://example.com/avatar.jpg"
        profile = {"avatar_300x300": {"url_list": ["https://example.com/avatar.heic", url]}}
        self.assertEqual(fetch_account_data.avatar_value(profile), url)

    def test_remote_avatar_is_saved_as_local_asset(self) -> None:
        response = mock.Mock()
        response.content = b"fake-jpeg"
        response.headers = {"Content-Type": "image/jpeg"}
        response.raise_for_status.return_value = None
        with tempfile.TemporaryDirectory() as raw, mock.patch.object(publish_report.requests, "get", return_value=response):
            payload = {"avatar": "https://example.com/avatar.jpg"}
            publish_report.localize_avatar(payload, Path(raw), "demo")
            self.assertEqual(payload["avatar"], "assets/demo-avatar.jpg")
            self.assertTrue((Path(raw)/payload["avatar"]).exists())

if __name__ == "__main__": unittest.main()
