#!/usr/bin/env python3
"""Owner-review-required, single-host Release160 READ-ONLY Bot0 PersonSummary trial.

DO NOT RUN without explicit owner approval. This script is intentionally
noninteractive and aborts on uncertainty. Only the operator on the Dell can
execute it. There is no remote-production execution from GitHub Actions.

Allowed mutation after successful preflight: pull one pinned candidate image;
create/remove one private Bot0 maintenance marker; create/remove two temporary
Compose overrides; recreate ONLY the Bot0 service with the candidate, then
restore ONLY Bot0 from the exact original digest. No DB writes, cleanup actions,
fleet restarts, image tag updates, or output of raw bot console logs.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import signal
import sqlite3
import stat
import subprocess
import sys
import tempfile
import time

from personsummary_console_result import summarize

BOT = "mcgatewaybot-docker"
FLEET = [BOT] + [f"mcgatewaybot{i}-docker" for i in range(1, 16)]
REPOSITORY = "ghcr.io/jaxdoesit/mcgateway-broadcast"
ORIGINAL = REPOSITORY + "@sha256:1b6e1dad197b82a97546bf352cadb5426eb7537fee9a24eb9160e8b00f5a3e55"
CANDIDATE = REPOSITORY + "@sha256:8768767c73ce9d29e80e81beaf2c1e6d3cbdbd4590e056fb06d32b1dde136722"
REVISIONS = {
    "index.js": "aef6d58fc48d40892ed9a565396f9ece13a2a385",
    "lib/release160-bot0-restart-hold.js": "bff9d6dc80bcf8fc0cc3bb9466b832de73ee711d",
    "lib/release160-cleanup-gate.js": "fcf0c8c8491e112295e6297786e80581185c7b0d",
    "lib/docker-console-pty.py": "64c2b0d1803c5e75dd80b37cca2cba99de16ecc2",
    "lib/bounded_console_output.py": "7633fe7e4a434e42cbcbefa4cc41458c18661ee5",
}
MARKER_BYTES = b"RELEASE160_BOT0_RESTART_HOLD_V1\n"
MAX_OUTPUT = 1024 * 1024

# This diagnostic-only image disables automatic friend management and explicitly
# performs one read-only list GET if the local cache has no target. No warmup.
CANARY_OBSERVE_SECONDS = 14

class Unsafe(RuntimeError):
    pass

def require(value, message):
    if not value:
        raise Unsafe(message)

def cmd(argv, timeout=40):
    """Bound subprocess response; never surface stdout/stderr on failure."""
    try:
        p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise Unsafe("command unavailable or uncertain: " + argv[0]) from e
    require(len(p.stdout) <= MAX_OUTPUT and len(p.stderr) <= MAX_OUTPUT,
            "command output exceeded private capture limit")
    require(p.returncode == 0, "command failed: " + argv[0] + " " + argv[1])
    return p.stdout

def docker_inspect(kind, name):
    data = json.loads(cmd(["docker", "inspect", "--type=" + kind, name]))
    require(isinstance(data, list) and len(data) == 1, "inspect result ambiguous")
    return data[0]

def git_blob(path):
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def locate_control_bot():
    raw = cmd(["systemctl", "show", "mcgateway-control-bot.service",
               "--property=MainPID", "--value"])
    pid = int(raw.strip())
    require(pid > 0, "Control Bot must be active")
    cwd = (Path("/proc") / str(pid) / "cwd").resolve()
    arguments = (Path("/proc") / str(pid) / "cmdline").read_bytes().split(b"\0")
    candidates = [cwd / "index.js"]
    for arg in arguments:
        if arg.endswith(b"index.js"):
            path = Path(os.fsdecode(arg))
            candidates.append(path if path.is_absolute() else cwd / path)
    entry = next((p.resolve() for p in candidates if p.is_file()), None)
    require(entry is not None, "active Control Bot source unresolved")
    root = entry.parent
    for relative, expected in REVISIONS.items():
        file = root / relative
        require(file.is_file() and not file.is_symlink(), "Control Bot reviewed source missing")
        require(git_blob(file) == expected, "installed Control Bot source drift")
    return root, pid

def paused_cleanup(root):
    db = root / "data" / "mcgateway.sqlite"
    require(db.is_file() and not db.is_symlink(), "cleanup state DB missing")
    connection = None
    try:
        connection = sqlite3.connect(db.as_uri() + "?mode=ro", uri=True, timeout=2)
        connection.execute("PRAGMA query_only=ON")
        row = connection.execute(
            "SELECT value FROM v44_state WHERE key = ?", ("cleanup_paused",)
        ).fetchone()
        return row is not None and row[0] == "1"
    except (sqlite3.DatabaseError, OSError):
        return False
    finally:
        if connection is not None:
            connection.close()

def paused_updates(root):
    path = root / "data" / "mcxbox-update-state.json"
    require(path.is_file() and path.stat().st_size < MAX_OUTPUT, "update state unavailable")
    data = json.loads(path.read_text())
    require(isinstance(data, dict) and data.get("paused") is True,
            "updater is not paused")
    rollout = root / "data" / "mcxbox-staged-rollout-state.json"
    require(rollout.is_file() and rollout.stat().st_size < MAX_OUTPUT,
            "staged rollout state unavailable")
    r = json.loads(rollout.read_text())
    require(isinstance(r, dict) and r.get("stage") == "complete",
            "staged rollout not complete")

def fleet_snapshot():
    result = {}
    for name in FLEET:
        bot = docker_inspect("container", name)
        require(bot.get("State", {}).get("Running") is True and
                bot.get("State", {}).get("OOMKilled") is False,
                "fleet contains an unhealthy or stopped container")
        result[name] = {"id": bot["Id"], "image": bot["Image"]}
    return result

def other_bots_unchanged(before):
    for name in FLEET[1:]:
        current = docker_inspect("container", name)
        if not (current["Id"] == before[name]["id"] and
                current["Image"] == before[name]["image"] and
                current["State"]["Running"] is True):
            return False
    return True

def original_identity(bot):
    image = docker_inspect("image", bot["Image"])
    require(ORIGINAL in (image.get("RepoDigests") or []),
            "running Bot0 image does not match original registry digest")
    labels = image.get("Config", {}).get("Labels") or {}
    require(labels.get("io.mcgateway.overlay-variant") == "relay-audit-expiry-held-v2",
            "original image overlay variant mismatch")

def compose_context(bot):
    labels = bot.get("Config", {}).get("Labels") or {}
    project = labels.get("com.docker.compose.project", "")
    service = labels.get("com.docker.compose.service", "")
    home = labels.get("com.docker.compose.project.working_dir", "")
    files = labels.get("com.docker.compose.project.config_files", "").split(",")
    require(re.fullmatch(r"[A-Za-z0-9_.-]+", project or "") is not None,
            "invalid Compose project identity")
    require(service == BOT, "unexpected Bot0 Compose service")
    require(home and Path(home).is_dir(), "Compose workdir unavailable")
    require(len(files) == 1 and bool(files[0].strip()), "multiple or missing Compose files")
    source = Path(files[0].strip())
    require(source.is_file(), "Compose file missing")
    return project, service, str(Path(home).resolve()), str(source.resolve())

def compose_args(context, override=None):
    project, _, workdir, source = context
    args = ["docker", "compose", "--project-name", project,
            "--project-directory", workdir, "-f", source]
    if override:
        args.extend(["-f", str(override)])
    return args

def compose_config(context, override=None):
    return json.loads(cmd(compose_args(context, override) +
                          ["config", "--format", "json"]))

def validate_override(context, original_config, new_config, image):
    before, after = original_config.get("services"), new_config.get("services")
    require(isinstance(before, dict) and isinstance(after, dict), "Compose services missing")
    require(set(before) == set(after) and BOT in before, "Compose service set drift")
    require(before[BOT].get("container_name") == BOT, "container identity drift")
    require(after[BOT].get("image") == image, "candidate digest override ineffective")
    a = dict(before[BOT])
    b = dict(after[BOT])
    a.pop("image", None)
    b.pop("image", None)
    require(a == b, "Bot0 effective Compose fields changed beyond image")
    for name in before:
        if name != BOT:
            require(before[name] == after[name], "another service configuration changed")
    require(new_config.get("networks") == original_config.get("networks"),
            "Compose network definition drift")
    require(new_config.get("volumes") == original_config.get("volumes"),
            "Compose volume definition drift")

def write_override(directory, suffix, image):
    # Name is constant and owner-private; no user-controlled content.
    path = directory / (suffix + ".yml")
    data = f"services:\n  {BOT}:\n    image: {image}\n"
    with path.open("x", encoding="utf-8") as f:
        os.chmod(path, 0o600)
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    return path

def confirm_image(image_ref):
    image = docker_inspect("image", image_ref)
    require(image_ref in (image.get("RepoDigests") or []), "image digest not locally proven")
    cfg = image.get("Config", {}) or {}
    require(cfg.get("User") == "app:app", "candidate runtime user changed")
    require(cfg.get("WorkingDir") == "/opt/app/config",
            "candidate working directory changed")
    if image_ref == CANDIDATE:
        labels = cfg.get("Labels") or {}
        require(labels.get("org.opencontainers.image.revision") ==
                "c889f7e957be37e1e30d0cec014630d199ef7aa6",
                "candidate source proof revision drift")
        require(labels.get("io.mcgateway.overlay-variant") ==
                "relay-audit-expiry-held-v2-personsummary-readonly-cache-v2",
                "candidate overlay identity drift")
        require(labels.get("io.mcgateway.friend-mutations-disabled") == "true",
                "read-only diagnostic safeguard missing")
    return image["Id"]

def make_hold(marker):
    require(not marker.exists() and not marker.is_symlink(), "maintenance hold exists already")
    fd = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    try:
        os.write(fd, MARKER_BYTES)
        os.fsync(fd)
        identity = os.fstat(fd)
    finally:
        os.close(fd)
    require(marker.read_bytes() == MARKER_BYTES and
            (marker.stat().st_mode & 0o077) == 0, "maintenance hold incorrect")
    return (identity.st_dev, identity.st_ino)

def remove_own_hold(marker, identity):
    info = marker.lstat()
    require((info.st_dev, info.st_ino) == identity and
            stat.S_ISREG(info.st_mode) and marker.read_bytes() == MARKER_BYTES,
            "maintenance hold replaced; refusing to clear")
    marker.unlink()

def recreate(context, override):
    cmd(compose_args(context, override) + [
        "up", "--detach", "--no-deps", "--no-build", "--pull", "never",
        "--force-recreate", BOT
    ], timeout=180)

def verified_boot(expected_id, seconds=14):
    # Treat any container replacement or restart during observation as drift.
    first = docker_inspect("container", BOT)
    expected_container = first["Id"]
    expected_start = first.get("State", {}).get("StartedAt")
    expected_restarts = first.get("RestartCount")
    require(expected_start and expected_restarts == 0,
            "fresh Bot0 boot identity/restart count is unverified")
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        bot = docker_inspect("container", BOT)
        require(bot.get("Id") == expected_container and
                bot.get("RestartCount") == 0 and
                bot.get("State", {}).get("StartedAt") == expected_start and
                bot.get("Image") == expected_id and
                bot.get("State", {}).get("Running") is True and
                bot.get("State", {}).get("OOMKilled") is False,
                "Bot0 image, container identity or process unexpected")
        time.sleep(2)

def direct_one_shot(root):
    nonce = secrets.token_hex(16)
    raw = b""
    delivered = False
    try:
        # The owner-only route is intentionally outside Control Bot's held
        # console queue, and invokes the exact already-reviewed helper once.
        target = docker_inspect("container", BOT)["Id"]
        p = subprocess.run(
            [sys.executable, str(root / "lib" / "docker-console-pty.py"),
             target, "personsummaryprobe " + nonce, "16000", "28000"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=34
        )
        delivered = p.returncode == 0
        raw = p.stdout[:MAX_OUTPUT] if len(p.stdout) <= MAX_OUTPUT else b""
    except (OSError, subprocess.TimeoutExpired):
        pass
    # Do NOT print nonce or raw PTY output or helper stderr.
    return summarize(raw, nonce, delivered)

def main():
    require(os.geteuid() == 0, "operator must invoke this on Dell using sudo")
    require(sys.argv[1:] == ["--execute-authorized-bot0-only"],
            "missing explicit Bot0-only authorization argument")
    root, pid = locate_control_bot()
    marker = root / "data" / ".release160-bot0-maintenance-hold"
    require(not marker.exists() and not marker.is_symlink(),
            "existing maintenance marker; abort without touching it")
    require(paused_cleanup(root), "persistent friend cleanup is not paused")
    paused_updates(root)
    watchtower = docker_inspect("container", "watchtower")
    require(watchtower.get("State", {}).get("Running") is False,
            "Watchtower must remain stopped")
    fleet = fleet_snapshot()
    bot = docker_inspect("container", BOT)
    require(bot.get("Config", {}).get("Tty") is True and
            bot.get("Config", {}).get("OpenStdin") is True, "Bot0 TTY unavailable")
    original_identity(bot)
    baseline_id = bot["Image"]
    context = compose_context(bot)
    original_config = compose_config(context)
    require(original_config["services"][BOT].get("container_name") == BOT,
            "Compose target does not match existing Bot0")
    local_original_ref = original_config["services"][BOT].get("image", "")
    require(docker_inspect("image", local_original_ref)["Id"] == baseline_id,
            "original Compose image does not match Bot0")
    require(other_bots_unchanged(fleet), "another bot changed before staging")
    print("PREFLIGHT PASSED: cleanup paused, updater paused, 16/16 running, original image verified.", flush=True)

    # Pulling a new immutable image is the only Docker mutation before the
    # maintenance hold; it does not recreate or restart a running container.
    cmd(["docker", "pull", CANDIDATE], timeout=240)
    candidate_id = confirm_image(CANDIDATE)
    original_digest_id = confirm_image(ORIGINAL)
    require(original_digest_id == baseline_id, "original recovery image is not exact")
    require(candidate_id != baseline_id, "candidate equals original unexpectedly")
    print("CANDIDATE STAGED: exact digest verified; no containers changed.", flush=True)

    directory = Path(tempfile.mkdtemp(prefix="mcgateway-bot0-canary-"))
    os.chmod(directory, 0o700)
    success = False
    hold_identity = None
    deployment_attempted = False
    rollback_verified = False
    rollback_error = None
    output = "PERSONSUMMARY_DIAGNOSTIC result=UNVERIFIED can_authorize_removal=false"
    try:
        proposed = write_override(directory, "canary", CANDIDATE)
        recovery = write_override(directory, "recovery", ORIGINAL)
        validate_override(context, original_config, compose_config(context, proposed), CANDIDATE)
        validate_override(context, original_config, compose_config(context, recovery), ORIGINAL)
        require(paused_cleanup(root), "cleanup pause changed before deployment")
        paused_updates(root)
        require(docker_inspect("container", "watchtower")["State"]["Running"] is False,
                "Watchtower restarted")
        require(docker_inspect("container", BOT)["Image"] == baseline_id,
                "Bot0 image changed before maintenance")
        require(other_bots_unchanged(fleet), "another bot changed during staging")
        hold_identity = make_hold(marker)
        # The reviewed hold is checked synchronously by Control Bot on each
        # restart and console operation; no Control Bot restart is necessary.
        require(marker.read_bytes() == MARKER_BYTES, "Bot0 hold not active")
        require(paused_cleanup(root), "cleanup pause changed after hold")
        print("BOT0 HOLD ACTIVE: moving only Bot0 to candidate.", flush=True)
        deployment_attempted = True
        recreate(context, proposed)
        print("BOT0 CANDIDATE RECREATED: checking stable boot before GET-only diagnostic.", flush=True)
        # Candidate friend-management mutation paths are disabled by the
        # independently source-proven JAR. Do not run the obsolete 120s warmup.
        verified_boot(candidate_id, seconds=CANARY_OBSERVE_SECONDS)
        require(marker.exists() and not marker.is_symlink() and
                marker.read_bytes() == MARKER_BYTES,
                "Bot0 maintenance hold lost before diagnostic")
        require(paused_cleanup(root), "cleanup unpaused during canary warmup")
        paused_updates(root)
        require(docker_inspect("container", "watchtower")["State"]["Running"] is False,
                "Watchtower restarted during canary observation")
        require(other_bots_unchanged(fleet), "other fleet container drift detected")
        print("OBSERVATION VERIFIED: issuing exactly one read-only probe command.", flush=True)
        output = direct_one_shot(root)
        print(output, flush=True)
        success = True
    except (Exception, KeyboardInterrupt) as e:
        print("CANARY STOPPED:", type(e).__name__, "(details withheld)", flush=True)
    finally:
        if hold_identity is not None:
            if deployment_attempted:
                print("RESTORING BOT0 original immutable digest.", flush=True)
                try:
                    recreate(context, recovery)
                    verified_boot(baseline_id, seconds=14)
                    require(paused_cleanup(root), "cleanup unpaused during recovery")
                    paused_updates(root)
                    require(other_bots_unchanged(fleet), "other containers changed")
                    rollback_verified = True
                except (Exception, KeyboardInterrupt) as e:
                    rollback_error = type(e).__name__
            else:
                try:
                    require(docker_inspect("container", BOT)["Image"] == baseline_id,
                            "original Bot0 changed before deployment")
                    rollback_verified = True
                except Exception as e:
                    rollback_error = type(e).__name__
            if rollback_verified:
                try:
                    remove_own_hold(marker, hold_identity)
                    print("RECOVERY VERIFIED: Bot0 original image running; maintenance hold cleared.", flush=True)
                except Exception as e:
                    rollback_error = type(e).__name__
                    rollback_verified = False
            if not rollback_verified:
                print("RECOVERY NOT VERIFIED: maintenance hold intentionally left active.", flush=True)
                print("Do not rerun the test. Inspect and recover Bot0 before clearing the hold.", flush=True)
        # Retain private overrides only when recovery is uncertain.
        if rollback_verified or hold_identity is None:
            shutil.rmtree(directory, ignore_errors=True)
    return 0 if rollback_verified and success else 2

if __name__ == "__main__":
    try:
        code = main()
    except (Exception, KeyboardInterrupt) as e:
        print("PREFLIGHT/SETUP STOPPED:", type(e).__name__, "(details withheld)")
        code = 2
    raise SystemExit(code)
