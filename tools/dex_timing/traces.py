"""Decode existing version-6 SameBoy captures without changing ROM instrumentation."""

import re

from .cpu import ModelError
from .model import LINE, FRAME


def span(start, end):
    tick0, ly0 = start
    tick1, ly1 = end
    if max(ly0, ly1) > 153:
        raise ModelError("Trace LY outside the display")
    ticks = (tick1-tick0) & 255
    elapsed = ticks*FRAME + (((ly1-144) % 154)-((ly0-144) % 154))*LINE
    if elapsed < 0 or elapsed > 127*FRAME:
        raise ModelError("Ambiguous/inconsistent trace clock; capture may be torn or from another schema")
    return {"nominal_t": elapsed, "min_t": max(0, elapsed-455), "max_t": elapsed+455,
            "note": "Scanline-resolution elapsed time; includes interrupts/waits, not just CPU work."}


def decode_trace(data):
    if len(data) != 139 or data[0:2] != bytes([0xD7, 6]):
        raise ModelError("Expected a complete version-6 139-byte Dex trace")
    head, count = data[23:25]
    if head >= 5 or count > 5:
        raise ModelError("Invalid trace ring head/count")
    result = []
    for i in range(count):
        position = (head-count+i) % 5
        raw = data[46+18*position:46+18*(position+1)]
        action, event, frame, deadline = raw[:4]
        stamps = [tuple(raw[i:i+2]) for i in range(4, 16, 2)]
        result.append({"action": action, "event": event, "frame": frame,
                       "deadline": deadline, "timestamps": stamps,
                       "loaded_tiles": raw[16], "upload_offset": raw[17],
                       "elapsed": span(stamps[0], stamps[-1]),
                       "phases": {name: span(stamps[i], stamps[i+1]) for i, name in enumerate(
                           ("stage", "dictionary", "gather", "hdma_entry", "hdma"))}})
    producer = [r for r in result if r["action"] < 128]
    gaps = []
    for first, second in zip(producer, producer[1:]):
        ticks = (second["timestamps"][0][0]-first["timestamps"][0][0]) & 255
        if ticks > 1:
            gaps.append({"after_event": first["event"], "counter_delta": ticks,
                         "missing_display_intervals": ticks-1,
                         "note": "Applies only to adjacent retained producer records."})
    return {"version": 6, "owner_id": data[2], "start_tick": data[3],
            "producer_calls": int.from_bytes(data[12:14], "little"),
            "start_loaded_tiles": data[19], "max_loaded_tiles": data[18],
            "schedule_address": int.from_bytes(data[136:138], "little"), "schedule_run": data[138],
            "records": result, "producer_gaps": gaps,
            "calibration_status": "UNBOUND_OBSERVATION"}


def read_captures(text, base=0xC758):
    captures, memory = [], {}
    for line in text.replace("&#x20;", " ").splitlines():
        match = re.match(r"\s*(?:[0-9A-Fa-f]{2}:)?([0-9A-Fa-f]{4}):\s+((?:[0-9A-Fa-f]{2}(?:\s+|$))+)", line)
        if not match:
            continue
        address = int(match[1], 16)
        values = bytes.fromhex(match[2])
        if address == base and base in memory:
            captures.append(_finish(memory, base))
            memory = {}
        for i, value in enumerate(values):
            if base <= address+i < base+139:
                memory[address+i] = value
    if memory:
        captures.append(_finish(memory, base))
    if not captures:
        raise ModelError(f"No version-6 capture at ${base:04x}")
    return captures


def _finish(memory, base):
    missing = [f"${base+i:04x}" for i in range(139) if base+i not in memory]
    if missing:
        raise ModelError(f"Incomplete trace: first missing address {missing[0]}")
    return decode_trace(bytes(memory[base+i] for i in range(139)))
