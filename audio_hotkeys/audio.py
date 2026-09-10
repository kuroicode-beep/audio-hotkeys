from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from comtypes import CLSCTX_ALL, COMError, COMMETHOD, CoCreateInstance, GUID, HRESULT, IUnknown
from ctypes import POINTER, cast
from ctypes.wintypes import BOOL, DWORD, LPCWSTR
from pycaw.constants import EDataFlow
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume, IMMDeviceEnumerator

CLSID_MMDeviceEnumerator = GUID("{BCDE0395-E52F-467C-8E3D-C4579291692E}")
CLSID_PolicyConfigClient = GUID("{870af99c-171d-4f9e-af0d-e63df40c2bc9}")
IID_IPolicyConfig = GUID("{f8679f50-850a-41cf-9c72-430f290290c8}")


class IPolicyConfig(IUnknown):
    """Undocumented Windows PolicyConfig used to set default audio endpoints."""

    _iid_ = IID_IPolicyConfig
    _methods_ = (
        COMMETHOD([], HRESULT, "Unused1"),
        COMMETHOD([], HRESULT, "Unused2"),
        COMMETHOD([], HRESULT, "Unused3"),
        COMMETHOD([], HRESULT, "Unused4"),
        COMMETHOD([], HRESULT, "Unused5"),
        COMMETHOD([], HRESULT, "Unused6"),
        COMMETHOD([], HRESULT, "Unused7"),
        COMMETHOD([], HRESULT, "Unused8"),
        COMMETHOD([], HRESULT, "Unused9"),
        COMMETHOD([], HRESULT, "Unused10"),
        COMMETHOD(
            [],
            HRESULT,
            "SetDefaultEndpoint",
            (["in"], LPCWSTR, "deviceId"),
            (["in"], DWORD, "role"),
        ),
        COMMETHOD(
            [],
            HRESULT,
            "SetEndpointVisibility",
            (["in"], LPCWSTR, "deviceId"),
            (["in"], BOOL, "visible"),
        ),
    )


@dataclass(frozen=True)
class AudioDevice:
    id: str
    name: str
    flow: str  # "output" | "input"


def _enumerator() -> IMMDeviceEnumerator:
    return CoCreateInstance(CLSID_MMDeviceEnumerator, IMMDeviceEnumerator, CLSCTX_ALL)


def list_devices(flow: str) -> list[AudioDevice]:
    data_flow = EDataFlow.eRender.value if flow == "output" else EDataFlow.eCapture.value
    collection = _enumerator().EnumAudioEndpoints(data_flow, 1)  # DEVICE_STATE_ACTIVE
    devices: list[AudioDevice] = []
    for i in range(collection.GetCount()):
        device = collection.Item(i)
        device_id = device.GetId()
        wrapped = AudioUtilities.CreateDevice(device)
        name = getattr(wrapped, "FriendlyName", None) or device_id
        devices.append(AudioDevice(id=device_id, name=name, flow=flow))
    devices.sort(key=lambda d: d.name.lower())
    return devices


def get_default_device(flow: str) -> AudioDevice | None:
    try:
        raw = AudioUtilities.GetSpeakers() if flow == "output" else AudioUtilities.GetMicrophone()
    except Exception:
        return None
    if raw is None:
        return None
    # Some pycaw versions return a wrapped AudioDevice for speakers but a raw
    # IMMDevice pointer for microphone — normalize both.
    if not hasattr(raw, "id") or not hasattr(raw, "FriendlyName"):
        try:
            raw = AudioUtilities.CreateDevice(raw)
        except Exception:
            return None
    return AudioDevice(id=raw.id, name=raw.FriendlyName, flow=flow)


def set_default_device(device_id: str) -> None:
    if not device_id:
        return
    policy = CoCreateInstance(CLSID_PolicyConfigClient, IPolicyConfig, CLSCTX_ALL)
    for role in (0, 1, 2):  # console / multimedia / communications
        policy.SetDefaultEndpoint(device_id, role)


def get_volume(flow: str) -> int | None:
    volume = _endpoint_volume(flow)
    if volume is None:
        return None
    return int(round(float(volume.GetMasterVolumeLevelScalar()) * 100))


def set_volume(flow: str, percent: int | None) -> None:
    if percent is None:
        return
    volume = _endpoint_volume(flow)
    if volume is None:
        return
    clamped = max(0, min(100, int(percent)))
    volume.SetMasterVolumeLevelScalar(clamped / 100.0, None)
    if volume.GetMute():
        volume.SetMute(0, None)


FLOW_LABEL = {"output": "출력", "input": "입력"}


@dataclass
class ApplyResult:
    """Outcome of applying one snapshot. Never raises for a single bad field."""

    summary: str
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.warnings


def com_message(exc: Exception) -> str:
    """Readable text for a COMError, whose str() is a raw HRESULT tuple."""
    if isinstance(exc, COMError):
        return str(getattr(exc, "text", None) or exc.hresult)
    return str(exc)


def resolve_device(device_id: str, device_name: str, flow: str) -> tuple[str, str]:
    """Map a saved snapshot device to a live one.

    Device ids change on USB re-enumeration or driver reinstall, which used to
    make SetDefaultEndpoint raise and abort the whole snapshot. Fall back to
    matching the saved friendly name. Returns (live_id, warning).
    """
    if not device_id and not device_name:
        return "", ""
    label = FLOW_LABEL.get(flow, flow)
    try:
        devices = list_devices(flow)
    except Exception as exc:  # noqa: BLE001
        return "", f"{label} 장치 목록을 읽지 못했습니다: {com_message(exc)}"

    if device_id and any(d.id == device_id for d in devices):
        return device_id, ""
    if device_name:
        for device in devices:
            if device.name == device_name:
                return device.id, f"{label} 장치를 이름으로 재연결했습니다: {device_name}"
    # 장치 GUID는 사용자에게 아무 의미가 없다 — 이름을 아는 경우에만 밝힌다.
    if device_name:
        return "", f"{label} 장치를 찾을 수 없습니다: {device_name} (연결 해제됨)"
    return "", f"{label} 장치가 연결 해제되어 건너뛰었습니다 (다시 선택해 저장하세요)"


def pref_present(snapshot: dict) -> bool | None:
    """헤드셋 우선 장치가 지금 연결돼 있는지. 우선 장치를 정하지 않은 슬롯이면 None.

    출력 장치를 기준으로 본다(헤드셋은 출력·입력이 함께 붙었다 떨어진다).
    출력을 안 정했으면 입력으로 판단한다.
    """
    out_id = snapshot.get("pref_output_id") or ""
    out_name = snapshot.get("pref_output_name") or ""
    in_id = snapshot.get("pref_input_id") or ""
    in_name = snapshot.get("pref_input_name") or ""
    if not (out_id or out_name or in_id or in_name):
        return None
    if out_id or out_name:
        live, _ = resolve_device(out_id, out_name, "output")
        return bool(live)
    live, _ = resolve_device(in_id, in_name, "input")
    return bool(live)


def effective_snapshot(snapshot: dict) -> tuple[dict, bool]:
    """헤드셋 우선 장치가 연결돼 있으면 시스템·카카오톡 출력/입력을 그 장치로 바꾼 사본을 돌려준다.

    반환: (적용할 스냅샷, 우선 장치를 썼는지). 안 꽂혀 있으면 원본 그대로.
    """
    if not pref_present(snapshot):
        return snapshot, False
    snap = dict(snapshot)
    for src_id, src_name, targets in (
        ("pref_output_id", "pref_output_name",
         (("output_id", "output_name"), ("kakao_output_id", "kakao_output_name"))),
        ("pref_input_id", "pref_input_name",
         (("input_id", "input_name"), ("kakao_input_id", "kakao_input_name"))),
    ):
        if not (snapshot.get(src_id) or snapshot.get(src_name)):
            continue
        for id_field, name_field in targets:
            snap[id_field] = snapshot.get(src_id) or ""
            snap[name_field] = snapshot.get(src_name) or ""
    return snap, True


def capture_system() -> dict:
    """Live default devices + volumes as snapshot fields.

    Names are captured next to ids so the snapshot survives a later id change
    — see resolve_device().
    """
    fields: dict = {}
    for flow, id_field, name_field, vol_field in (
        ("output", "output_id", "output_name", "output_volume"),
        ("input", "input_id", "input_name", "input_volume"),
    ):
        device = get_default_device(flow)
        fields[id_field] = device.id if device else ""
        fields[name_field] = device.name if device else ""
        fields[vol_field] = get_volume(flow)
    return fields


def apply_snapshot(snapshot: dict) -> ApplyResult:
    from . import kakao

    parts: list[str] = []
    warnings: list[str] = []

    # 헤드셋 우선 장치가 꽂혀 있으면 그쪽으로 — 아니면 슬롯에 적힌 장치 그대로
    snapshot, used_pref = effective_snapshot(snapshot)
    if used_pref:
        parts.append("Headset")

    for flow, id_field, name_field, vol_field, tag in (
        ("output", "output_id", "output_name", "output_volume", "Out"),
        ("input", "input_id", "input_name", "input_volume", "In"),
    ):
        device_id, warning = resolve_device(
            snapshot.get(id_field) or "",
            snapshot.get(name_field) or "",
            flow,
        )
        if warning:
            warnings.append(warning)
        if device_id:
            try:
                set_default_device(device_id)
                parts.append(f"{tag}: {_name_for_id(device_id, flow)}")
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"{FLOW_LABEL[flow]} 장치 전환 실패: {com_message(exc)}")

        volume = snapshot.get(vol_field)
        if volume is not None:
            try:
                set_volume(flow, int(volume))
                parts.append(f"{tag}Vol: {int(volume)}%")
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"{FLOW_LABEL[flow]} 볼륨 설정 실패: {com_message(exc)}")

    kakao_parts, kakao_warnings = kakao.apply_kakao_snapshot(snapshot)
    parts.extend(kakao_parts)
    warnings.extend(kakao_warnings)

    # FLOW 8 믹서 본체 스냅샷 — 슬롯에 번호가 있을 때만 USB MIDI로 불러온다(실패해도 다른 항목은 유지)
    f8 = snapshot.get("flow8_snapshot")
    if f8:
        try:
            from flow8core import Flow8Controller

            Flow8Controller().load_snapshot(int(f8))
            parts.append(f"FLOW8: {int(f8)}")
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"FLOW 8 스냅샷 {f8} 불러오기 실패: {exc}")

    label = snapshot.get("name") or "Snapshot"
    if not parts:
        summary = f"{label}: (empty)" if not warnings else label
    else:
        summary = f"{label} — " + " | ".join(parts)
    return ApplyResult(summary=summary, warnings=warnings)


def volume_choices() -> list[str]:
    return ["(unchanged)"] + [str(v) for v in range(0, 101, 5)]


def device_choices(flow: str) -> list[tuple[str, str]]:
    items = [("(unchanged)", "")]
    for device in list_devices(flow):
        items.append((device.name, device.id))
    return items


def find_display(choices: Iterable[tuple[str, str]], device_id: str) -> str:
    for name, did in choices:
        if did == device_id:
            return name
    return "(unchanged)" if not device_id else device_id


def _endpoint_volume(flow: str):
    device = get_default_device(flow)
    if device is None:
        return None
    try:
        mm = _enumerator().GetDevice(device.id)
        interface = mm.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))
    except COMError:
        return None


def _name_for_id(device_id: str, flow: str) -> str:
    for device in list_devices(flow):
        if device.id == device_id:
            return device.name
    return device_id
