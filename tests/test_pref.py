# tests/test_pref.py — 헤드셋 우선 장치·자동 전환 (v1.8.0) 단위 테스트. 실제 장치 없이 list_devices를 가짜로 바꿔 검증한다.
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from audio_hotkeys import audio, config, i18n  # noqa: E402

RAZER_OUT = audio.AudioDevice(id="{0.0.0}.{razer-out}", name="스피커(Razer Barracuda X 2.4)", flow="output")
RAZER_IN = audio.AudioDevice(id="{0.0.1}.{razer-in}", name="마이크(Razer Barracuda X 2.4)", flow="input")
FLOW_OUT = audio.AudioDevice(id="{0.0.0}.{flow8-out}", name="USB Out 1/2(BEHRINGER FLOW 8)", flow="output")
RODE_IN = audio.AudioDevice(id="{0.0.1}.{rode-in}", name="마이크(RØDE NT-USB Mini)", flow="input")


def _slot0() -> dict:
    snap = dict(config.EMPTY_SNAPSHOT)
    snap.update({
        "name": "평소", "output_id": FLOW_OUT.id, "output_name": FLOW_OUT.name,
        "input_id": RODE_IN.id, "input_name": RODE_IN.name,
        "kakao_output_id": FLOW_OUT.id, "kakao_output_name": FLOW_OUT.name,
        "pref_output_id": RAZER_OUT.id, "pref_output_name": RAZER_OUT.name,
        "pref_input_id": RAZER_IN.id, "pref_input_name": RAZER_IN.name, "pref_auto": True,
    })
    return snap


def _fake_devices(monkeypatch, outputs, inputs):
    monkeypatch.setattr(audio, "list_devices", lambda flow: list(outputs if flow == "output" else inputs))


MIRACLE_OUT = audio.AudioDevice(id="{0.0.0}.{miracle}", name="헤드폰(miracle)", flow="output")


def _slot0_with_speaker() -> dict:
    snap = _slot0()
    snap.update({"pref2_output_id": MIRACLE_OUT.id, "pref2_output_name": MIRACLE_OUT.name})
    return snap


# 2순위 스피커: 헤드셋 없고 스피커만 있으면 출력·카카오톡 출력만 바뀌고 입력은 그대로
def test_speaker_tier_output_only(monkeypatch):
    _fake_devices(monkeypatch, [FLOW_OUT, MIRACLE_OUT], [RODE_IN])
    snap, tier = audio.effective_snapshot(_slot0_with_speaker())
    assert tier == "speaker"
    assert snap["output_id"] == MIRACLE_OUT.id and snap["kakao_output_id"] == MIRACLE_OUT.id
    assert snap["input_id"] == RODE_IN.id and snap["kakao_input_id"] == ""
    assert audio.presence_key(_slot0_with_speaker()) == (False, True)


# 헤드셋과 스피커가 둘 다 있으면 헤드셋이 이긴다
def test_headset_beats_speaker(monkeypatch):
    _fake_devices(monkeypatch, [FLOW_OUT, MIRACLE_OUT, RAZER_OUT], [RODE_IN, RAZER_IN])
    snap, tier = audio.effective_snapshot(_slot0_with_speaker())
    assert tier == "headset" and snap["output_id"] == RAZER_OUT.id
    assert audio.presence_key(_slot0_with_speaker()) == (True, True)


# 둘 다 없으면 원본, presence_key는 (False, False); 아무것도 안 정한 슬롯은 None
def test_speaker_tier_absent(monkeypatch):
    _fake_devices(monkeypatch, [FLOW_OUT], [RODE_IN])
    snap, tier = audio.effective_snapshot(_slot0_with_speaker())
    assert tier == "" and snap["output_id"] == FLOW_OUT.id
    assert audio.presence_key(_slot0_with_speaker()) == (False, False)
    assert audio.presence_key(dict(config.EMPTY_SNAPSHOT)) is None


# 헤드셋이 꽂혀 있으면 시스템·카카오톡 출력/입력이 전부 헤드셋으로 바뀐다
def test_pref_present_overrides_all(monkeypatch):
    _fake_devices(monkeypatch, [FLOW_OUT, RAZER_OUT], [RODE_IN, RAZER_IN])
    snap, used = audio.effective_snapshot(_slot0())
    assert used == "headset"
    assert snap["output_id"] == RAZER_OUT.id and snap["input_id"] == RAZER_IN.id
    assert snap["kakao_output_id"] == RAZER_OUT.id and snap["kakao_input_id"] == RAZER_IN.id
    assert snap["kakao_output_name"] == RAZER_OUT.name


# 헤드셋이 없으면 원본 그대로
def test_pref_absent_keeps_base(monkeypatch):
    _fake_devices(monkeypatch, [FLOW_OUT], [RODE_IN])
    base = _slot0()
    snap, used = audio.effective_snapshot(base)
    assert used == "" and snap is base
    assert audio.pref_present(base) is False


# ID가 바뀌어도 이름으로 헤드셋을 찾는다(USB 재열거 대비)
def test_pref_matches_by_name(monkeypatch):
    renamed = audio.AudioDevice(id="{0.0.0}.{new-id}", name=RAZER_OUT.name, flow="output")
    _fake_devices(monkeypatch, [FLOW_OUT, renamed], [RODE_IN])
    snap, used = audio.effective_snapshot(_slot0())
    assert used == "headset" and snap["output_id"] == RAZER_OUT.id  # 저장된 id를 넘기고 apply 단계에서 이름 재매칭


# 우선 장치를 안 정한 슬롯은 None(감시 대상 아님)
def test_pref_none_when_unset(monkeypatch):
    _fake_devices(monkeypatch, [FLOW_OUT], [RODE_IN])
    snap = dict(config.EMPTY_SNAPSHOT)
    assert audio.pref_present(snap) is None
    assert audio.effective_snapshot(snap)[1] == ""


# 설정 정규화: pref 필드가 살아남고 pref_auto는 bool
def test_config_normalizes_pref_fields():
    data = config._normalize({"snapshots": {"0": {"name": "x", "pref_output_id": "a", "pref_output_name": "A", "pref_auto": 1}}})
    s = data["snapshots"]["0"]
    assert s["pref_output_id"] == "a" and s["pref_output_name"] == "A" and s["pref_auto"] is True
    assert data["snapshots"]["1"]["pref_auto"] is False


# 5개 언어가 같은 키 집합을 가진다
def test_i18n_key_parity():
    keys = {lang: set(table) for lang, table in i18n.STRINGS.items()}
    ko = keys["ko"]
    for lang, ks in keys.items():
        assert ks == ko, f"{lang}: {ks ^ ko}"
    for k in ("field_pref_out", "field_pref_in", "pref_auto", "pref_hint", "offline", "auto_switched_on", "auto_switched_off",
              "field_pref2_out", "auto_spk_on", "auto_spk_off"):
        assert k in ko


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
