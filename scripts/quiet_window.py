"""조용한 시간(quiet window): quiet_windows.json에 적힌 구간 동안 Claude(API)를 쓰는 윈도우 예약 작업을 멈췄다가 되살린다.

2026-11-26 도입 — 사장님이 토 11/28 11~14시 검사 때문에 Claude를 꺼 둬야 해서. 그날 켜져 있을 본가 데스크톱이
따로 손대지 않아도 알아서 멈추게 하려고 run_queue.py(08~12시 30분마다, 맨 앞에서 git pull)에 붙였다.

동작(컴퓨터마다 따로):
- run_queue.py가 돌 때마다 ensure()를 부른다 → 구간 시작·끝 시각에 한 번 도는 윈도우 작업
  QuietWindow_<id>_start / _end 를 등록(이미 있으면 그대로).
- 시작 때 멈춘 작업 이름을 temp/quiet_window_state.json(git 제외)에 적고, 끝날 때 그 작업만 되살린다.
- 이미 구간 안에서 켜졌으면 ensure()가 바로 멈춘다. 끝 작업이 못 돌았으면(컴퓨터 꺼짐 등) 다음 ensure()가 되살린다.
- ShortsAutoQueue는 멈추지 않는다(Claude 안 씀 + 되살리기 안전망).

수동: python scripts/quiet_window.py status | ensure | start <id> | end <id>
"""
import json
import os
import subprocess
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = os.path.join(BASE, "scripts", "quiet_windows.json")
STATE = os.path.join(BASE, "temp", "quiet_window_state.json")
NEVER_PAUSE = {"ShortsAutoQueue"}


def _print(msg):
    print(msg)


def ps(cmd):
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()


def _load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def _save_state(st):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=1)


def windows():
    return _load(CFG, {}).get("windows", [])


def _find(wid):
    for w in windows():
        if w["id"] == wid:
            return w
    raise SystemExit(f"없는 구간: {wid}")


def _span(w):
    return datetime.fromisoformat(w["start"]), datetime.fromisoformat(w["end"])


def _enabled_tasks(patterns):
    names = set()
    for p in patterns:
        _, out = ps(f"Get-ScheduledTask -TaskName '{p}' -ErrorAction SilentlyContinue | "
                    "Where-Object { $_.State -ne 'Disabled' } | ForEach-Object { $_.TaskName }")
        names.update(line.strip() for line in out.splitlines() if line.strip())
    return sorted(n for n in names if n not in NEVER_PAUSE and not n.startswith("QuietWindow_"))


def start(w, log=_print):
    s, e = _span(w)
    if datetime.now() >= e:
        log(f"조용한 시간 {w['id']}: 이미 끝난 구간이라 멈추지 않음")
        return
    st = _load(STATE, {})
    rec = st.get(w["id"], {})
    if rec.get("started"):
        return
    paused = []
    for n in _enabled_tasks(w["tasks"]):
        code, out = ps(f"Disable-ScheduledTask -TaskName '{n}' | Out-Null")
        if code == 0:
            paused.append(n)
        else:
            log(f"조용한 시간 {w['id']}: {n} 멈추기 실패 — {out[:200]}")
    st[w["id"]] = {"started": datetime.now().isoformat(timespec="seconds"), "paused": paused}
    _save_state(st)
    log(f"조용한 시간 {w['id']} 시작: {len(paused)}개 멈춤 {paused}")


def end(w, log=_print):
    st = _load(STATE, {})
    rec = st.get(w["id"])
    if not rec or not rec.get("started") or rec.get("ended"):
        return
    failed = []
    for n in rec.get("paused", []):
        code, out = ps(f"Enable-ScheduledTask -TaskName '{n}' | Out-Null")
        if code != 0:
            failed.append(n)
            log(f"조용한 시간 {w['id']}: {n} 되살리기 실패 — {out[:200]}")
    if failed:
        rec["paused"] = failed  # 다음 ensure()에서 다시 시도
    else:
        rec["ended"] = datetime.now().isoformat(timespec="seconds")
    _save_state(st)
    log(f"조용한 시간 {w['id']} 끝: 되살림 {'일부 실패 ' + str(failed) if failed else '완료'}")


def _register(w, which, at):
    name = f"QuietWindow_{w['id']}_{which}"
    code, _ = ps(f"Get-ScheduledTask -TaskName '{name}' -ErrorAction Stop | Out-Null")
    if code == 0:
        return False
    script = os.path.abspath(__file__)
    cmd = (f"$a = New-ScheduledTaskAction -Execute '{sys.executable}' -Argument '\"{script}\" {which} {w['id']}' "
           f"-WorkingDirectory '{BASE}'; "
           f"$t = New-ScheduledTaskTrigger -Once -At ([datetime]'{at.isoformat()}'); "
           "$s = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries "
           "-ExecutionTimeLimit (New-TimeSpan -Minutes 10); "
           f"Register-ScheduledTask -TaskName '{name}' -Action $a -Trigger $t -Settings $s -Force | Out-Null")
    code, out = ps(cmd)
    if code != 0:
        raise RuntimeError(f"{name} 등록 실패: {out[:300]}")
    return True


def ensure(log=_print):
    now = datetime.now()
    for w in windows():
        s, e = _span(w)
        if now >= e:
            end(w, log)
            continue
        if s <= now:
            start(w, log)
        new = []
        if s > now and _register(w, "start", s):
            new.append(f"{s:%m/%d %H:%M} 멈춤")
        if _register(w, "end", e):
            new.append(f"{e:%m/%d %H:%M} 되살림")
        if new:
            log(f"조용한 시간 {w['id']} 예약 등록: {', '.join(new)} (대상 {w['tasks']})")


def status():
    st = _load(STATE, {})
    for w in windows():
        _, out = ps(f"Get-ScheduledTask -TaskName 'QuietWindow_{w['id']}_*' -ErrorAction SilentlyContinue | "
                    "ForEach-Object { $_.TaskName + ' ' + $_.State + ' ' + $_.Triggers[0].StartBoundary }")
        print(w["id"], w["start"], "~", w["end"], w["tasks"])
        print("  예약:", out or "없음")
        print("  상태:", st.get(w["id"], "아직 시작 안 함"))
        print("  지금 켜진 대상:", _enabled_tasks(w["tasks"]))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:] or ["status"]
    if args[0] == "ensure":
        ensure()
    elif args[0] == "start":
        start(_find(args[1]))
    elif args[0] == "end":
        end(_find(args[1]))
    else:
        status()
