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


def apply_snapshot(snapshot: dict) -> str:
    parts: list[str] = []

    output_id = snapshot.get("output_id") or ""
    input_id = snapshot.get("input_id") or ""

    if output_id:
        set_default_device(output_id)
        parts.append(f"Out: {_name_for_id(output_id, 'output')}")

    if input_id:
        set_default_device(input_id)
        parts.append(f"In: {_name_for_id(input_id, 'input')}")

    out_vol = snapshot.get("output_volume")
    if out_vol is not None:
        set_volume("output", int(out_vol))
        parts.append(f"OutVol: {int(out_vol)}%")

    in_vol = snapshot.get("input_volume")
    if in_vol is not None:
        set_volume("input", int(in_vol))
        parts.append(f"InVol: {int(in_vol)}%")

    label = snapshot.get("name") or "Snapshot"
    if not parts:
        return f"{label}: (empty)"
    return f"{label} — " + " | ".join(parts)


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
