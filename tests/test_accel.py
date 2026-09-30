#!/usr/bin/env python3
"""Tests for Apple VideoToolbox encoding (--hw) and the Parakeet speech engines (2.4).

    python3 tests/test_accel.py          # this group alone
    python3 tests/test_all.py            # every group

The pure-logic cases run everywhere. The real VideoToolbox encodes run only on Apple Silicon with
an ffmpeg that lists the encoders; the Parakeet engines are driven through fake binaries on a
PATH that holds nothing else, so these cases never depend on what the host has installed.
"""
import argparse
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fixtures import MediaFixtures, OUT, ROOT, SCRIPTS, script, sh  # noqa: E402
from _common import STATE, add_common, apply_common, ffmpeg_encoders  # noqa: E402
from _common import asr, decision, runner  # noqa: E402


def _vt_here() -> bool:
    return (platform.system() == "Darwin" and platform.machine() == "arm64"
            and {"h264_videotoolbox", "hevc_videotoolbox"} <= ffmpeg_encoders())


def _parse(argv, codec=True, orchestrator=False):
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="?")
    ap.add_argument("-o", "--output")
    if codec and not orchestrator:
        ap.set_defaults(crf=18)
    add_common(ap, codec=codec)
    if orchestrator:
        runner.add_hw_orchestrator_args(ap)
    args = ap.parse_args(argv)
    apply_common(args)
    return args


class HwResolutionTests(unittest.TestCase):
    """--hw / --no-hw / $FFMPEG_SKILL_HW resolve the same way in every tool."""

    def setUp(self):
        self._env = mock.patch.dict(os.environ, {}, clear=False)
        self._env.start()
        for k in (runner.HW_ENV, runner.HW_FORCED_ENV):
            os.environ.pop(k, None)

    def tearDown(self):
        self._env.stop()
        STATE.reset()

    def test_off_by_default(self):
        _parse(["in.mp4"])
        self.assertFalse(STATE.hw)
        self.assertIsNone(STATE.hw_source)

    def test_env_turns_it_on_and_no_hw_turns_it_off(self):
        os.environ[runner.HW_ENV] = "1"
        _parse(["in.mp4"])
        self.assertEqual((STATE.hw, STATE.hw_source), (True, "env"))
        _parse(["in.mp4", "--no-hw"])
        self.assertEqual((STATE.hw, STATE.hw_source), (False, "flag"))

    def test_export_style_tools_ignore_the_env_default(self):
        """A delivery preset (codec=False: export.py) is on the GPU only when asked explicitly."""
        os.environ[runner.HW_ENV] = "1"
        _parse(["in.mp4"], codec=False)
        self.assertFalse(STATE.hw)
        _parse(["in.mp4", "--hw"], codec=False)
        self.assertEqual((STATE.hw, STATE.hw_source), (True, "flag"))

    def test_orchestrator_flag_reaches_export_style_children_as_explicit(self):
        """render.py/batch.py --hw is an explicit choice for every stage, export.py included;
        their --no-hw overrides a machine default for every stage."""
        _parse(["p.json", "--hw"], orchestrator=True)
        self.assertEqual((os.environ.get(runner.HW_ENV), os.environ.get(runner.HW_FORCED_ENV)), ("1", "1"))
        _parse(["in.mp4"], codec=False)          # a child export.py
        self.assertEqual((STATE.hw, STATE.hw_source), (True, "flag"))
        _parse(["p.json", "--no-hw"], orchestrator=True)
        _parse(["in.mp4"])                       # a child fit.py
        self.assertEqual((STATE.hw, STATE.hw_source), (False, "flag"))

    def test_tools_without_an_encoder_never_pick_it_up(self):
        os.environ[runner.HW_ENV] = "1"
        ap = argparse.ArgumentParser()
        ap.add_argument("input")
        add_common(ap)                           # no crf default: an analysis tool
        args = ap.parse_args(["in.mp4"])
        self.assertFalse(hasattr(args, "hw"))
        apply_common(args)
        self.assertFalse(STATE.hw)


class VtArgsTests(unittest.TestCase):
    def tearDown(self):
        STATE.reset()

    def test_quality_mapping_is_monotonic_and_bounded(self):
        for codec, hdr in (("h264", False), ("hevc", False), ("hevc", True)):
            qs = [decision.vt_quality(codec, crf, hdr) for crf in range(0, 52)]
            self.assertEqual(qs, sorted(qs, reverse=True))
            self.assertTrue(all(1 <= q <= 100 for q in qs))

    def test_an_hdr_source_gets_the_hdr_quality_curve(self):
        """HLG phone footage at the SDR curve's -q:v came out 6-8x x265's bytes at a higher SSIM
        (tests/bench_vt.py); the Main10 line takes its own, lower curve, chosen from the source."""
        STATE.hw = True
        hdr = {"video": {"bt2020_or_hdr": True, "color_transfer": "arib-std-b67"}}
        sdr = {"video": {"bt2020_or_hdr": False}}
        with mock.patch.object(decision, "hw_platform_reason", return_value=None), \
                mock.patch.object(decision, "ffmpeg_encoders", return_value={"hevc_videotoolbox"}):
            for crf in (18, 23, 28):
                q_hdr = decision._vt_args("hevc", crf, hdr, True)
                q_sdr = decision._vt_args("hevc", crf, sdr, True)
                q_hdr, q_sdr = int(q_hdr[q_hdr.index("-q:v") + 1]), int(q_sdr[q_sdr.index("-q:v") + 1])
                self.assertEqual(q_hdr, decision.vt_quality("hevc", crf, True))
                self.assertEqual(q_sdr, decision.vt_quality("hevc", crf))
                self.assertLess(q_hdr, q_sdr - 10, crf)

    def test_the_curves_keep_the_measured_values(self):
        """The CRF 18/23/28 values tests/bench_vt.py measured (the highest -q:v that matched the CPU
        encode's SSIM on every clip); a slope typo moves one of them."""
        self.assertEqual([decision.vt_quality("h264", c) for c in (18, 23, 28)], [75, 64, 53])
        self.assertEqual([decision.vt_quality("hevc", c) for c in (18, 23, 28)], [78, 68, 58])
        self.assertEqual([decision.vt_quality("hevc", c, True) for c in (18, 23, 28)], [63, 55, 47])

    def test_an_h264_line_on_an_hdr_source_keeps_the_h264_curve(self):
        """An export preset's x264 line on an HLG source: the VideoToolbox H.264 line replaces x264
        at the same CRF, so the HDR (Main10, CRF+2) curve does not apply."""
        STATE.hw = True
        hdr = {"video": {"bt2020_or_hdr": True, "color_transfer": "arib-std-b67"}}
        with mock.patch.object(decision, "hw_platform_reason", return_value=None), \
                mock.patch.object(decision, "ffmpeg_encoders", return_value={"h264_videotoolbox"}):
            line = decision.hw_preset_video(["-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p"], hdr)
        self.assertEqual(line[line.index("-q:v") + 1], "75")

    def test_av1_and_an_intel_mac_stay_on_the_cpu_with_a_note(self):
        STATE.hw = True
        self.assertIsNone(decision._vt_args("av1", 30, None, True))
        with mock.patch.object(decision, "hw_platform_reason", return_value="VideoToolbox constant-quality encoding needs Apple Silicon"):
            cpu = ["-c:v", "libx264", "-crf", "18"]
            self.assertEqual(decision._maybe_hw("h264", 18, None, True, cpu), cpu)
        self.assertTrue(any("av1" in n for n in STATE.hw_notes))
        self.assertTrue(any("Apple Silicon" in n for n in STATE.hw_notes))

    def test_run_can_put_the_cpu_line_back(self):
        STATE.hw_swaps = [(["-c:v", "h264_videotoolbox", "-q:v", "75"], ["-c:v", "libx264", "-crf", "18"])]
        cmd = ["ffmpeg", "-i", "a.mp4", "-c:v", "h264_videotoolbox", "-q:v", "75", "out.mp4"]
        self.assertEqual(runner._hw_fallback(cmd, STATE), ["ffmpeg", "-i", "a.mp4", "-c:v", "libx264", "-crf", "18", "out.mp4"])
        self.assertIsNone(runner._hw_fallback(["ffmpeg", "-i", "a", "b"], STATE))

    def test_export_preset_keeps_its_frame_rate_and_leaves_faststart_to_export(self):
        STATE.hw = True
        with mock.patch.object(decision, "hw_platform_reason", return_value=None), \
                mock.patch.object(decision, "ffmpeg_encoders", return_value={"h264_videotoolbox"}):
            vt = decision.hw_preset_video(["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-profile:v", "high",
                                           "-pix_fmt", "yuv420p", "-r", "30"], None)
        self.assertEqual(vt[vt.index("-c:v") + 1], "h264_videotoolbox")
        self.assertEqual(vt[vt.index("-r") + 1], "30")
        self.assertNotIn("-movflags", vt)
        self.assertNotIn("-preset", vt)

    def test_render_cache_key_changes_with_the_gpu_setting(self):
        """A VideoToolbox artifact is never served to a CPU run (and the other way round)."""
        import render
        with mock.patch.dict(os.environ, {runner.HW_ENV: "0"}):
            os.environ.pop(runner.HW_FORCED_ENV, None)
            cpu = render.cache_key("fit", "fit.py", ["--height", "720"], [])
        with mock.patch.dict(os.environ, {runner.HW_ENV: "1"}):
            gpu = render.cache_key("fit", "fit.py", ["--height", "720"], [])
        with mock.patch.dict(os.environ, {runner.HW_ENV: "1", runner.HW_FORCED_ENV: "1"}):
            forced = render.cache_key("fit", "fit.py", ["--height", "720"], [])
        self.assertEqual(len({cpu, gpu, forced}), 3)


class HwReviewRegressionTests(unittest.TestCase):
    """Cases a review of the first --hw implementation found."""

    def tearDown(self):
        STATE.reset()

    def _vt_ok(self):
        return (mock.patch.object(decision, "hw_platform_reason", return_value=None),
                mock.patch.object(decision, "ffmpeg_encoders", return_value={"h264_videotoolbox", "hevc_videotoolbox", "prores_videotoolbox"}))

    def test_export_edits_to_a_vt_line_keep_the_fallback_findable(self):
        """export.py strips -movflags from encoder_args()'s line; the swap must follow the edit."""
        STATE.hw = True
        a, b = self._vt_ok()
        with a, b:
            built = decision.encoder_args("hevc", 20, "medium", {"video": {"bt2020_or_hdr": True, "color_transfer": "smpte2084"}})
        stripped = decision.strip_movflags(built)
        decision.restate_last_swap(built, stripped)
        cmd = ["ffmpeg", "-i", "in.mov"] + stripped + ["-movflags", "+faststart", "out.mp4"]
        back = runner._hw_fallback(cmd, STATE)
        self.assertIsNotNone(back)
        self.assertIn("libx265", back)

    def test_export_preset_fallback_is_tagged_like_a_cpu_run(self):
        STATE.hw = True
        a, b = self._vt_ok()
        with a, b:
            decision.hw_preset_video(["-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-pix_fmt", "yuv420p"], None)
        cpu = STATE.hw_swaps[-1][1]
        self.assertTrue("-x264-params" in cpu or "-colorspace" in cpu, cpu)

    def test_vt_bt709_tags_come_from_a_bitstream_filter_on_every_version(self):
        """On FFmpeg >= 7.1 the -colorspace output options insert a real matrix conversion on an
        untagged source, so VideoToolbox gets its tags from a bitstream filter instead. A git build
        of 7.1 reads as (7, 0), so the tag path must not change with the version guess either."""
        for codec in ("h264", "hevc"):
            for v in ((6, 1), (7, 0), (7, 1), (9, 0)):
                with mock.patch.object(decision, "ffmpeg_version", return_value=v):
                    tags = decision._vt_bt709(codec)
                self.assertEqual(tags[0], "-bsf:v", (codec, v))
                self.assertNotIn("-colorspace", tags)
                self.assertNotIn("-x264-params", tags)

    def test_run_retries_a_refused_videotoolbox_encode_on_the_cpu_and_reports_it(self):
        """run() itself: a failed VT encode is re-run once with the recorded CPU line, the note and
        the recorded command follow, and the result reports the CPU encoder."""
        import importlib
        emit = importlib.import_module("_common.emit")
        STATE.hw, STATE.hw_source = True, "flag"
        STATE.hw_swaps = [(["-c:v", "h264_videotoolbox", "-q:v", "75"], ["-c:v", "libx264", "-crf", "18"])]
        refused = subprocess.CompletedProcess([], 1, "", "[vt] Error: cannot encode 8192x4608\n")
        ok = subprocess.CompletedProcess([], 0, "", "")
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(runner, "_execute", side_effect=[refused, ok]) as execute:
            out = str(Path(d) / "o.mp4")
            proc = runner.run(["ffmpeg", "-i", "a.mp4", "-c:v", "h264_videotoolbox", "-q:v", "75", out], quiet=True)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(execute.call_count, 2)
        retried = execute.call_args_list[1][0][0]
        self.assertIn("libx264", retried)
        self.assertNotIn("h264_videotoolbox", retried)
        self.assertIn("libx264", STATE.commands[-1])
        self.assertTrue(any("VideoToolbox refused" in n and "8192x4608" in n for n in STATE.hw_notes), STATE.hw_notes)
        rep = emit._encoder_report(STATE)
        self.assertEqual(rep["encoder"], "libx264")
        self.assertFalse(rep["hw"]["used"])

    def test_encoder_report_keeps_the_encode_behind_a_later_copy(self):
        import importlib
        emit = importlib.import_module("_common.emit")
        STATE.commands = ["ffmpeg -i a -c:v h264_videotoolbox -q:v 75 b.mp4", "ffmpeg -i b.mp4 -c:v copy -af loudnorm c.mp4"]
        STATE.hw, STATE.hw_source = True, "flag"
        rep = emit._encoder_report(STATE)
        self.assertEqual(rep["encoder"], "h264_videotoolbox")
        self.assertTrue(rep["hw"]["used"])
        STATE.commands = ["ffmpeg -ss 1 -i a.mp4 -c copy -t 2 b.mp4"]
        self.assertEqual(emit._encoder_report(STATE)["encoder"], "copy")
        STATE.commands = []  # batch.py: the stages are child processes it does not record
        self.assertIsNone(emit._encoder_report(STATE)["hw"]["used"])

    def test_an_env_chosen_gpu_encode_says_how_to_get_the_cpu_one(self):
        """FFMPEG_SKILL_HW=1 puts every tool on VideoToolbox, whose files are larger at the same
        quality; a result says so only when the environment chose the GPU and the GPU ran."""
        import importlib
        emit = importlib.import_module("_common.emit")
        gpu, cpu = "ffmpeg -i a -c:v h264_videotoolbox -q:v 75 b.mp4", "ffmpeg -i a -c:v libx264 -crf 18 b.mp4"
        for hw, source, command, noted in [(True, "env", gpu, True), (True, "flag", gpu, False),
                                           (True, "env", cpu, False), (False, None, cpu, False)]:
            with self.subTest(hw=hw, source=source, command=command):
                STATE.hw, STATE.hw_source, STATE.hw_notes, STATE.commands = hw, source, [], [command]
                rep = emit._encoder_report(STATE)
                if not hw:
                    self.assertNotIn("hw", rep)
                    continue
                notes = rep["hw"]["notes"]
                self.assertEqual(any("FFMPEG_SKILL_HW=1" in n and "--no-hw" in n for n in notes), noted, notes)
                self.assertEqual(STATE.hw_notes, [], "the report adds the note; the run's own list is untouched")

    def test_parakeet_cpp_runs_with_only_an_explicit_model(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"HOME": d}):
            os.environ.pop("PARAKEET_CPP_MODEL", None)
            gguf = Path(d) / "tdt-0.6b-v3-f16.gguf"
            gguf.write_bytes(b"GGUF")
            which = mock.Mock(which=lambda n: "/x/parakeet-cli" if n == "parakeet-cli" else None)
            self.assertFalse(asr._parakeet_available("parakeet.cpp", which))
            self.assertTrue(asr._parakeet_available("parakeet.cpp", which, str(gguf)))
            self.assertEqual(asr._parakeet_model_for("parakeet.cpp", str(gguf), "de"), str(gguf))
            # --engine auto must see it too, not only a forced --engine parakeet.cpp
            self.assertEqual(asr.parakeet_route("auto", "en", "a.wav", which, subprocess)[0], [])
            self.assertEqual(asr.parakeet_route("auto", "en", "a.wav", which, subprocess, str(gguf))[0], list(asr.PARAKEET_ENGINES))

    def test_hw_dry_run_runs_no_ffmpeg(self):
        """The dry-run promise: --hw's encoder check reads the build through ffprobe, never ffmpeg."""
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "calls.log"
            fake = Path(d) / "ffmpeg"
            fake.write_text(f"#!/bin/sh\necho \"$@\" >> {log}\nexit 1\n")
            fake.chmod(0o755)
            for tool in ("ffprobe",):
                os.symlink(shutil.which(tool), Path(d) / tool)
            env = dict(os.environ, PATH=f"{d}{os.pathsep}/usr/bin{os.pathsep}/bin")
            runner._ENCODERS = None
            proc = subprocess.run([sys.executable, str(SCRIPTS / "fit.py"), str(OUT / "source.mp4"), "--height", "360", "--hw",
                                   "--dry-run", "--json", "-o", str(Path(d) / "o.mp4")], env=env, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertFalse(log.exists(), log.read_text() if log.exists() else "")


@unittest.skipUnless(_vt_here(), "VideoToolbox encoders need Apple Silicon and an ffmpeg that lists them")
class VtEncodeTests(MediaFixtures):
    """Real VideoToolbox encodes, probed."""

    def test_hw_encode_reports_itself_and_keeps_an_untagged_source_unconverted(self):
        src = OUT / "vt_untagged.mkv"
        sh("ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=s=640x360:d=1",
           "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "0", src)
        out = OUT / "vt_fit.mp4"
        doc = json.loads(script("fit.py", src, "--height", "360", "--hw", "--json", "-o", out).stdout)
        self.assertEqual(doc["encoder"], "h264_videotoolbox")
        self.assertEqual(doc["hw"], {"requested": True, "source": "flag", "used": True, "notes": []})
        v = doc["probe"]["video"]
        self.assertEqual((v["color_space"], v["color_primaries"], v["color_transfer"]), ("bt709", "bt709", "bt709"))
        neutral = "setparams=colorspace=unknown:color_primaries=unknown:color_trc=unknown"
        proc = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(out), "-i", str(src), "-lavfi",
                               f"[0:v]{neutral}[a];[1:v]{neutral}[b];[a][b]psnr", "-f", "null", "-"],
                              stderr=subprocess.PIPE, text=True)
        psnr = float(proc.stderr.split("average:")[1].split()[0])
        self.assertGreater(psnr, 40, "the BT.709 tag turned into a colour conversion (~24 dB)")

    def test_hw_hdr10_side_data_survives(self):
        """PQ + mastering-display + content-light metadata come through hevc_videotoolbox."""
        src = OUT / "vt_hdr10_md.mp4"
        sh("ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=s=640x360:d=1",
           "-c:v", "libx265", "-pix_fmt", "yuv420p10le", "-tag:v", "hvc1", "-x265-params",
           "log-level=error:hdr10=1:master-display=G(13250,34500)B(7500,3000)R(34000,16000)WP(15635,16450)L(10000000,1):max-cll=1000,400",
           "-bsf:v", "hevc_metadata=colour_primaries=9:transfer_characteristics=16:matrix_coefficients=9", src)
        out = OUT / "vt_hdr10_out.mp4"
        doc = json.loads(script("fit.py", src, "--height", "360", "--hw", "--json", "-o", out).stdout)
        self.assertEqual(doc["encoder"], "hevc_videotoolbox")
        self.assertEqual(doc["probe"]["video"]["color_transfer"], "smpte2084")
        side = sh("ffprobe", "-v", "error", "-select_streams", "v", "-read_intervals", "%+#1", "-show_frames",
                  "-show_entries", "frame_side_data=side_data_type", out).stdout
        self.assertIn("Mastering display metadata", side)
        self.assertIn("Content light level metadata", side)

    def test_a_job_videotoolbox_refuses_falls_back_to_the_cpu_and_says_so(self):
        """H.264 on VideoToolbox stops at 4096 wide; an 8K frame is re-encoded on x264, reported.
        Half a second is enough for the real refusal (the full clip took ~26 s of x264 at 8K)."""
        out = OUT / "vt_8k.mp4"
        doc = json.loads(script("fit.py", self.src, "--duration", "0.5", "--method", "trim", "--width", "8192",
                                "--height", "4608", "--hw", "--fast", "--json", "-o", out).stdout)
        self.assertEqual(doc["encoder"], "libx264")
        self.assertFalse(doc["hw"]["used"])
        self.assertTrue(any("VideoToolbox refused" in n for n in doc["hw"]["notes"]), doc["hw"])

    def test_export_preset_needs_an_explicit_hw(self):
        """The env default leaves a delivery preset on the CPU (a dry run: encoder choice only);
        an explicit --hw export really runs on VideoToolbox and keeps the preset's frame rate."""
        env = dict(os.environ, FFMPEG_SKILL_HW="1")
        doc = json.loads(script("export.py", self.src, "--preset", "x", "--dry-run", "--json",
                                "-o", OUT / "vt_x_env.mp4", env=env).stdout)
        self.assertEqual(doc["encoder"], "libx264")
        doc = json.loads(script("export.py", self.src, "--preset", "x", "--hw", "--json",
                                "-o", OUT / "vt_x_hw.mp4").stdout)
        self.assertEqual(doc["encoder"], "h264_videotoolbox")
        self.assertTrue(doc["hw"]["used"])
        self.assertEqual(round(doc["probe"]["video"]["fps"]), 30)


# ------------------------------------------------------------------------------ Parakeet

MLX_DOC = {"text": "So um we start. Here.", "sentences": [
    {"text": "So um we start.", "start": 0.2, "end": 1.6, "tokens": [
        {"text": " So", "start": 0.2, "end": 0.4}, {"text": " u", "start": 0.5, "end": 0.6}, {"text": "m", "start": 0.6, "end": 0.7},
        {"text": " ", "start": 0.7, "end": 0.8}, {"text": "we", "start": 0.9, "end": 1.0}, {"text": " start", "start": 1.1, "end": 1.5},
        {"text": ".", "start": 1.5, "end": 1.6}]},
    {"text": "Here.", "start": 2.0, "end": 2.4, "tokens": [{"text": " Here", "start": 2.0, "end": 2.3}, {"text": ".", "start": 2.3, "end": 2.4}]}]}
CPP_DOC = {"text": "So um we start. Here.", "frame_sec": 0.08, "words": [
    {"w": "So", "start": 0.2, "end": 0.4, "conf": 0.99}, {"w": "um", "start": 0.5, "end": 0.7, "conf": 0.9},
    {"w": "we", "start": 0.9, "end": 1.0, "conf": 0.99}, {"w": "start.", "start": 1.1, "end": 1.6, "conf": 0.99},
    {"w": "Here.", "start": 2.0, "end": 2.4, "conf": 0.99}]}


class ParakeetParsingTests(unittest.TestCase):
    def test_mlx_subword_tokens_become_words(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(MLX_DOC, fh)
        words = asr._words_from_parakeet_mlx_json(fh.name)
        self.assertEqual([w["word"] for w in words], ["So", "um", "we", "start.", "Here."])
        self.assertEqual((words[1]["start"], words[1]["end"]), (0.5, 0.7))
        self.assertEqual(asr._cues_from_parakeet_mlx_json(fh.name), [(0.2, 1.6, "So um we start."), (2.0, 2.4, "Here.")])
        os.unlink(fh.name)

    def test_cpp_words_and_the_cues_built_from_them(self):
        words = asr._words_from_parakeet_cpp_json(json.dumps(CPP_DOC))
        self.assertEqual(len(words), 5)
        self.assertEqual(asr.cues_from_words(words), [(0.2, 1.6, "So um we start."), (2.0, 2.4, "Here.")])

    def test_malformed_engine_output_yields_no_words_instead_of_crashing(self):
        """Garbage, the wrong shape, and words missing fields are skipped, never raised."""
        for text in ("not json", "[]", "null", json.dumps({"words": "x"}), json.dumps({"words": 5}),
                     json.dumps({"words": [5, None, []]})):
            self.assertEqual(asr._words_from_parakeet_cpp_json(text), [], text)
        mixed = {"words": [{"w": "ok", "start": 0.1, "end": 0.3}, {"w": "no-times"}, {"start": 1, "end": 2},
                           {"w": "bad", "start": "x", "end": 1}, "str", {"w": "fine", "start": 1.0, "end": 1.2}]}
        self.assertEqual([w["word"] for w in asr._words_from_parakeet_cpp_json(json.dumps(mixed))], ["ok", "fine"])
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.json"
            for body in ("{truncated", "[1, 2]", json.dumps({"sentences": [{"text": "no times"}]}),
                         json.dumps({"sentences": 5}), json.dumps({"sentences": [5, None]}),
                         json.dumps({"sentences": [{"tokens": 5}]}), json.dumps({"sentences": [{"tokens": [5, None]}]})):
                p.write_text(body)
                self.assertEqual(asr._cues_from_parakeet_mlx_json(str(p)), [], body)
                self.assertEqual(asr._words_from_parakeet_mlx_json(str(p)), [], body)
            self.assertEqual(asr._words_from_parakeet_mlx_json(str(Path(d) / "missing.json")), [])

    def test_cues_split_on_a_pause_and_on_length(self):
        words = [{"word": "a", "start": 0.0, "end": 0.2}, {"word": "b", "start": 1.5, "end": 1.7}]
        self.assertEqual(len(asr.cues_from_words(words)), 2)
        # 0.5 s apart, 0.4 s long: w13 ends at 6.9 s, w14 would stretch the cue to 7.4 s (> 7 s)
        long = [{"word": f"w{i}", "start": i * 0.5, "end": i * 0.5 + 0.4} for i in range(20)]
        self.assertEqual(asr.cues_from_words(long), [
            (0.0, 6.9, " ".join(f"w{i}" for i in range(14))),
            (7.0, 9.9, " ".join(f"w{i}" for i in range(14, 20)))])


class ParakeetRoutingTests(unittest.TestCase):
    def test_auto_routes_by_language(self):
        which = mock.Mock(side_effect=lambda n: "/x/" + n if n == "parakeet-mlx" else None)
        sh_ = mock.Mock(which=which)
        self.assertEqual(asr.parakeet_route("auto", "en", "a.wav", sh_, subprocess)[0], ["parakeet-mlx", "parakeet.cpp"])
        self.assertEqual(asr.parakeet_route("auto", "fr", "a.wav", sh_, subprocess)[0], [])
        self.assertEqual(asr.parakeet_route("whisper.cpp", None, "a.wav", sh_, subprocess)[0], [])
        self.assertEqual(asr.parakeet_route("parakeet.cpp", "de", "a.wav", sh_, subprocess)[0], ["parakeet.cpp"])
        with mock.patch.object(asr, "detect_language", return_value="ja"):
            self.assertEqual(asr.parakeet_route("auto", None, "a.wav", sh_, subprocess)[0], [])
        with mock.patch.object(asr, "detect_language", return_value=None):
            eng, route = asr.parakeet_route("auto", None, "a.wav", sh_, subprocess)
            self.assertEqual(eng, ["parakeet-mlx", "parakeet.cpp"])
            self.assertIn("assumed English", route["routing"])

    def test_english_only_model_refuses_another_language(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PARAKEET_MODEL", None)
            with self.assertRaises(SystemExit):
                asr._parakeet_model_for("parakeet-mlx", None, "fr")
            self.assertIn("v3", asr._parakeet_model_for("parakeet-mlx", "mlx-community/parakeet-tdt-0.6b-v3", "fr"))
            self.assertEqual(asr._parakeet_model_for("parakeet-mlx", "large-v3-turbo", "en"), asr.PARAKEET_MLX_DEFAULT_MODEL)

    def test_unknown_engine_in_the_environment_is_refused(self):
        with mock.patch.dict(os.environ, {asr.ASR_ENGINE_ENV: "vosk"}):
            with self.assertRaises(SystemExit):
                asr.requested_engine(None)

    def test_engine_flag_beats_the_environment_which_beats_auto(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(asr.ASR_ENGINE_ENV, None)
            self.assertEqual(asr.requested_engine(None), "auto")
            os.environ[asr.ASR_ENGINE_ENV] = "parakeet.cpp"
            self.assertEqual(asr.requested_engine(None), "parakeet.cpp")
            self.assertEqual(asr.requested_engine("whisper.cpp"), "whisper.cpp")


class ParakeetEngineTests(MediaFixtures):
    """caption.py / silence.py drive fake Parakeet binaries on a PATH that holds only them and ffmpeg."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.bin = Path(tempfile.mkdtemp(prefix="ffskill_fakeasr_"))
        for tool in ("ffmpeg", "ffprobe", "fc-match", "fc-list"):
            if shutil.which(tool):
                os.symlink(shutil.which(tool), cls.bin / tool)
        mlx = """
            import json, os, sys
            a = sys.argv[1:]; out = a[a.index("--output-dir") + 1]; os.makedirs(out, exist_ok=True)
            json.dump(DOC, open(os.path.join(out, os.path.splitext(os.path.basename(a[0]))[0] + ".json"), "w"))
            """
        cpp = """
            import json, sys
            assert sys.argv[1] == "transcribe" and "--json" in sys.argv
            print(json.dumps(DOC))
            """
        for name, body, doc in (("parakeet-mlx", mlx, MLX_DOC), ("parakeet-cli", cpp, CPP_DOC)):
            p = cls.bin / name
            p.write_text(f"#!{sys.executable}\nDOC = {doc!r}\n" + textwrap.dedent(body))
            p.chmod(p.stat().st_mode | stat.S_IXUSR)
        cls.gguf = cls.bin / "tdt-0.6b-v2-f16.gguf"
        cls.gguf.write_bytes(b"GGUF")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.bin, ignore_errors=True)
        super().tearDownClass()

    def env(self, **extra):
        e = dict(os.environ, PATH=f"{self.bin}{os.pathsep}/usr/bin{os.pathsep}/bin", PARAKEET_CPP_MODEL=str(self.gguf))
        e.update(extra)
        return e

    def test_caption_auto_picks_parakeet_for_english_and_reports_it(self):
        doc = json.loads(script("caption.py", self.src, "--transcribe", "--language", "en", "--fast", "--json",
                                "-o", OUT / "pk_auto.mp4", env=self.env()).stdout)
        self.assertEqual(doc["transcription"]["engine"], "parakeet-mlx")
        self.assertEqual(doc["transcription"]["model"], asr.PARAKEET_MLX_DEFAULT_MODEL)
        self.assertIn("So um we start.", (OUT / "pk_auto.srt").read_text())

    def test_caption_engine_flag_picks_parakeet_cpp(self):
        """One end-to-end parakeet.cpp run; flag-over-env precedence is a unit test above."""
        doc = json.loads(script("caption.py", self.src, "--transcribe", "--engine", "parakeet.cpp", "--fast", "--json",
                                "-o", OUT / "pk_cpp.mp4", env=self.env()).stdout)
        self.assertEqual(doc["transcription"]["engine"], "parakeet.cpp")
        self.assertIn("So um we start.", (OUT / "pk_cpp.srt").read_text())

    def test_caption_mux_reports_the_transcription_too(self):
        """--mode mux wrote a soft subtitle track from the transcript but left `transcription` out of
        its result, so a caller could not tell which engine made it."""
        doc = json.loads(script("caption.py", self.src, "--transcribe", "--engine", "parakeet.cpp", "--mode", "mux",
                                "--json", "-o", OUT / "pk_mux.mp4", env=self.env()).stdout)
        self.assertEqual(doc["subtitle_tracks"], 1)
        self.assertEqual(doc["transcription"]["engine"], "parakeet.cpp")

    def test_caption_takes_the_engine_from_the_environment(self):
        """$FFMPEG_SKILL_ASR_ENGINE reaches caption.py through its real parser (no --engine given)."""
        doc = json.loads(script("caption.py", self.src, "--transcribe", "--fast", "--json", "-o", OUT / "pk_cpp_env.mp4",
                                env=self.env(FFMPEG_SKILL_ASR_ENGINE="parakeet.cpp")).stdout)
        self.assertEqual(doc["transcription"]["engine"], "parakeet.cpp")

    def _run_with_mlx_writing(self, body, tool, *args, expect_fail=False):
        """`tool` with a parakeet-mlx that exits 0 after writing `body` as its JSON."""
        fake = Path(tempfile.mkdtemp(prefix="ffskill_oddasr_"))
        try:
            for name in os.listdir(self.bin):
                if name != "parakeet-mlx":
                    os.symlink(self.bin / name, fake / name)
            mlx = fake / "parakeet-mlx"
            mlx.write_text(f"#!{sys.executable}\nimport os, sys\na = sys.argv[1:]; out = a[a.index('--output-dir') + 1]\n"
                           "os.makedirs(out, exist_ok=True)\n"
                           "open(os.path.join(out, os.path.splitext(os.path.basename(a[0]))[0] + '.json'), 'w')"
                           f".write({body!r})\n")
            mlx.chmod(0o755)
            proc = script(tool, self.src, *args, "--json", env=self.env(PATH=str(fake)), expect_fail=expect_fail)
        finally:
            shutil.rmtree(fake, ignore_errors=True)
        return json.loads(proc.stdout)

    def test_unreadable_engine_output_falls_through_instead_of_claiming_silence(self):
        """parakeet-mlx exited 0 but wrote something that is not a transcript: that is a failed
        run, so auto moves on to parakeet.cpp instead of reporting "no speech" in the video."""
        doc = self._run_with_mlx_writing('{"sentences": 5}', "caption.py", "--transcribe", "--fast", "-o", OUT / "pk_garbage.mp4")
        self.assertEqual(doc["transcription"]["engine"], "parakeet.cpp")

    def test_filler_words_fall_through_an_engine_with_sentences_but_no_word_times(self):
        """Sentences whose text and times read but whose tokens do not: cues for a caption, but no
        word timings, which is all silence.py --filler needs -- so the next engine is tried."""
        body = json.dumps({"text": "So um we start.", "sentences": [{"text": "So um we start.", "start": 0.2, "end": 1.6,
                                                                     "tokens": [{"text": " So"}, 5]}]})
        doc = self._run_with_mlx_writing(body, "silence.py", "--filler", "--transcribe", "--filler-list")
        self.assertEqual(doc["filler"]["source"], "parakeet:parakeet.cpp")
        self.assertEqual([r["word"] for r in doc["filler"]["removed"]], ["um"])

    def test_a_named_engine_with_no_word_times_is_refused_by_name(self):
        """--engine parakeet-mlx ran and gave no word timings: say that, not "install it"."""
        body = json.dumps({"text": "So um we start.", "sentences": [{"text": "So um we start.", "start": 0.2, "end": 1.6,
                                                                     "tokens": [{"text": " So"}, 5]}]})
        doc = self._run_with_mlx_writing(body, "silence.py", "--filler", "--transcribe", "--filler-list",
                                         "--engine", "parakeet-mlx", expect_fail=True)
        self.assertEqual(doc["error"]["kind"], "input")
        self.assertIn("parakeet-mlx ran but produced no word-level timings", doc["error"]["message"])

    def test_an_engine_that_heard_nothing_still_reports_no_speech(self):
        """What both real engines write for 3 s of silence (measured): an empty list. That is an
        answer, not a failure, so it is still the no-speech refusal and nothing else is tried."""
        doc = self._run_with_mlx_writing('{"text": "", "sentences": []}', "caption.py", "--transcribe", "--fast",
                                         "-o", OUT / "pk_silent.mp4", expect_fail=True)
        self.assertEqual((doc["error"]["kind"], doc.get("reason"), doc.get("engine")), ("input", "no_speech", "parakeet-mlx"))

    def test_auto_falls_through_a_failing_parakeet_mlx_to_parakeet_cpp(self):
        """parakeet-mlx is installed but crashes: auto moves on to the next Parakeet engine."""
        broken = Path(tempfile.mkdtemp(prefix="ffskill_brokenasr_"))
        try:
            for name in os.listdir(self.bin):
                if name != "parakeet-mlx":
                    os.symlink(self.bin / name, broken / name)
            ran = broken / "mlx-ran"
            mlx = broken / "parakeet-mlx"
            mlx.write_text(f"#!/bin/sh\n: > '{ran}'\necho 'Metal device lost' >&2\nexit 3\n")
            mlx.chmod(0o755)
            # only the fakes and ffmpeg on PATH: no host whisper can detect a language or take over,
            # so auto assumes English and the order is parakeet-mlx, then parakeet.cpp
            doc = json.loads(script("silence.py", self.src, "--filler", "--transcribe", "--filler-list", "--json",
                                    env=self.env(PATH=str(broken))).stdout)
            mlx_ran = ran.exists()
        finally:
            shutil.rmtree(broken, ignore_errors=True)
        self.assertTrue(mlx_ran, "the crashing parakeet-mlx was never run, so nothing fell through")
        self.assertEqual(doc["filler"]["source"], "parakeet:parakeet.cpp")
        self.assertEqual([r["word"] for r in doc["filler"]["removed"]], ["um"])

    def test_caption_another_language_skips_parakeet(self):
        proc = script("caption.py", self.src, "--transcribe", "--language", "fr", "--fast", "--json",
                      "-o", OUT / "pk_fr.mp4", env=self.env(), expect_fail=True)
        err = json.loads(proc.stdout)["error"]["message"]
        self.assertIn("no local speech-to-text engine", err)

    def test_silence_filler_words_from_parakeet(self):
        doc = json.loads(script("silence.py", self.src, "--filler", "--transcribe", "--filler-list", "--json",
                                "--engine", "parakeet.cpp", env=self.env()).stdout)
        self.assertEqual(doc["filler"]["source"], "parakeet:parakeet.cpp")
        self.assertEqual([r["word"] for r in doc["filler"]["removed"]], ["um"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
