#!/usr/bin/env python3
"""Convert PCM WAV cries to packed 4-bit Game Boy wave-channel samples."""

from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import random
import wave
from dataclasses import dataclass
from typing import Any

PRISM_VOL = 3.2
MAX_PRISM_VOL = 3.2
EXPERIMENTAL_MAX_PRISM_VOL = 4.5
PRISM_RATE = 10485.76
PRISM_DITHER_SEED = 3490487757541254948
PRISM_NEG_LIMIT = 8.0 / 15.0
PRISM_POS_LIMIT = 7.0 / 15.0
BLOCK_SAMPLES = 32
SILENCE_NIBBLE = 8


@dataclass
class ConversionResult:
	source_path: pathlib.Path
	source_rate: int
	source_frames: int
	target_rate: float
	processed_samples: list[float]
	limited_samples: list[float]
	nibbles: list[int]
	padded_nibbles: list[int]
	packed: bytes
	metrics: dict[str, Any]


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser()
	parser.add_argument("input", type=pathlib.Path)
	parser.add_argument("output", type=pathlib.Path)
	parser.add_argument("--sample-rate", type=int, default=10512)
	parser.add_argument("--gain-db", type=float, default=0.0)
	parser.add_argument("--mode", choices=("linear", "prism"), default="linear")
	parser.add_argument("--compression", choices=("pcm4", "minmax2"), default="pcm4")
	parser.add_argument("--prism-vol", type=float, default=PRISM_VOL)
	parser.add_argument("--prism-rate", type=float, default=PRISM_RATE)
	parser.add_argument(
		"--mastering",
		choices=("baseline", "softclip", "compressor", "compressor-preemphasis"),
		default="baseline",
	)
	parser.add_argument("--profile-json", type=pathlib.Path)
	parser.add_argument("--profile")
	parser.add_argument("--preview-wav", type=pathlib.Path)
	parser.add_argument("--report-json", type=pathlib.Path)
	return parser.parse_args()


def db_to_linear(db_value: float) -> float:
	return 10 ** (db_value / 20.0)


def linear_to_db(value: float) -> float:
	return -120.0 if value <= 1e-12 else 20.0 * math.log10(value)


def rms(samples: list[float]) -> float:
	return math.sqrt(sum(sample * sample for sample in samples) / len(samples)) if samples else 0.0


def prism_vol_cap(config: dict[str, Any]) -> float:
	if config.get("allow_experimental_prism_vol", False):
		return float(config.get("max_prism_vol", EXPERIMENTAL_MAX_PRISM_VOL))
	return MAX_PRISM_VOL


def validate_prism_vol_config(config: dict[str, Any], label: str) -> None:
	cap = prism_vol_cap(config)
	prism_vol = float(config.get("prism_vol", PRISM_VOL))
	if prism_vol > cap:
		raise SystemExit(f"{label} prism_vol exceeds cap {cap:g}; got {prism_vol:g}")
	auto_gain = config.get("auto_gain") or {}
	if auto_gain:
		max_auto = float(auto_gain.get("max_prism_vol", prism_vol))
		if max_auto > cap:
			raise SystemExit(f"{label} auto_gain.max_prism_vol exceeds cap {cap:g}; got {max_auto:g}")


def read_wav_mono_float(path: pathlib.Path) -> tuple[list[float], int, int]:
	with wave.open(str(path), "rb") as wav:
		channels = wav.getnchannels()
		sample_width = wav.getsampwidth()
		sample_rate = wav.getframerate()
		compression = wav.getcomptype()
		frame_count = wav.getnframes()
		frames = wav.readframes(frame_count)

	if compression != "NONE":
		raise SystemExit(f"expected PCM WAV, got compression type {compression}")
	if channels < 1:
		raise SystemExit("expected at least one channel")
	if sample_width not in (1, 2, 3):
		raise SystemExit(f"expected 8, 16, or 24-bit PCM WAV, got {sample_width * 8}-bit samples")

	samples: list[float] = []
	frame_size = sample_width * channels
	for frame_offset in range(0, len(frames), frame_size):
		total = 0.0
		for channel in range(channels):
			offset = frame_offset + channel * sample_width
			chunk = frames[offset : offset + sample_width]
			if sample_width == 1:
				value = chunk[0] - 128
				total += value / 256.0
			elif sample_width == 2:
				value = int.from_bytes(chunk, "little", signed=True)
				total += value / 65536.0
			else:
				sign = b"\xff" if chunk[2] & 0x80 else b"\x00"
				value = int.from_bytes(chunk + sign, "little", signed=True)
				total += value / 16777216.0
		samples.append(total / channels)

	return samples, sample_rate, frame_count


def cubic_interpolate(samples: list[float], position: float) -> float:
	index = int(position)
	p0 = samples[index]
	p1 = samples[index + 1]
	m0 = (samples[index + 1] - samples[index - 1]) / 2
	m1 = (samples[index + 2] - samples[index]) / 2
	t1 = math.modf(position)[0]
	t2 = t1**2
	t3 = t1**3
	return (
		(2 * t3 - 3 * t2 + 1) * p0
		+ (t3 - 2 * t2 + t1) * m0
		+ (-2 * t3 + 3 * t2) * p1
		+ (t3 - t2) * m1
	)


def resample_prism(samples: list[float], source_rate: int, target_rate: float) -> list[float]:
	if not samples:
		return []
	if abs(source_rate - target_rate) / target_rate <= 0.05:
		return samples + [0.0, 0.0]

	guarded = samples + [0.0, 0.0]
	output_count = int(len(samples) * target_rate / source_rate)
	return [cubic_interpolate(guarded, i * source_rate / target_rate) for i in range(output_count)]


def remove_dc(samples: list[float]) -> list[float]:
	if not samples:
		return []
	mean = sum(samples) / len(samples)
	return [sample - mean for sample in samples]


def highpass_one_pole(samples: list[float], sample_rate: float, cutoff_hz: float) -> list[float]:
	if cutoff_hz <= 0 or not samples:
		return samples
	rc = 1.0 / (2.0 * math.pi * cutoff_hz)
	dt = 1.0 / sample_rate
	alpha = rc / (rc + dt)
	output: list[float] = []
	previous_input = samples[0]
	previous_output = 0.0
	for sample in samples:
		value = alpha * (previous_output + sample - previous_input)
		output.append(value)
		previous_input = sample
		previous_output = value
	return output


def lowpass_one_pole(samples: list[float], sample_rate: float, cutoff_hz: float) -> list[float]:
	if cutoff_hz <= 0 or not samples:
		return samples
	rc = 1.0 / (2.0 * math.pi * cutoff_hz)
	dt = 1.0 / sample_rate
	alpha = dt / (rc + dt)
	output: list[float] = []
	previous_output = samples[0]
	for sample in samples:
		previous_output = previous_output + alpha * (sample - previous_output)
		output.append(previous_output)
	return output


def apply_body_boost(samples: list[float], sample_rate: float, config: dict[str, Any] | None) -> list[float]:
	if not config:
		return samples
	gain_db = float(config.get("gain_db", 0.0))
	if gain_db == 0.0:
		return samples
	cutoff_hz = float(config.get("cutoff_hz", 650.0))
	low = lowpass_one_pole(samples, sample_rate, cutoff_hz)
	gain = db_to_linear(gain_db) - 1.0
	return [sample + low_sample * gain for sample, low_sample in zip(samples, low)]


def trim_active(samples: list[float], sample_rate: float, trim_config: dict[str, Any] | None) -> list[float]:
	if not trim_config or not trim_config.get("enabled", False) or not samples:
		return samples
	threshold = db_to_linear(float(trim_config.get("threshold_db", -48)))
	pad = int(sample_rate * float(trim_config.get("pad_ms", 0)) / 1000.0)
	active = [index for index, sample in enumerate(samples) if abs(sample) >= threshold]
	if not active:
		return samples
	start = max(0, active[0] - pad)
	end = min(len(samples), active[-1] + pad + 1)
	return samples[start:end]


def preemphasize(samples: list[float], config: dict[str, Any] | None) -> list[float]:
	if not config:
		return samples
	coeff = float(config.get("coeff", 0.0))
	gain = float(config.get("gain", 1.0))
	if coeff == 0.0 and gain == 1.0:
		return samples
	output: list[float] = []
	previous = 0.0
	for sample in samples:
		output.append((sample - coeff * previous) * gain)
		previous = sample
	return output


def compress(samples: list[float], sample_rate: float, config: dict[str, Any] | None) -> list[float]:
	if not config:
		return samples

	threshold_db = float(config.get("threshold_db", -24.0))
	ratio = max(1.0, float(config.get("ratio", 1.0)))
	knee_db = max(0.0, float(config.get("knee_db", 0.0)))
	attack_ms = max(0.01, float(config.get("attack_ms", 1.0)))
	release_ms = max(0.01, float(config.get("release_ms", 50.0)))
	makeup_db = float(config.get("makeup_db", 0.0))
	attack_coeff = math.exp(-1.0 / (sample_rate * attack_ms / 1000.0))
	release_coeff = math.exp(-1.0 / (sample_rate * release_ms / 1000.0))
	makeup = db_to_linear(makeup_db)

	def gain_reduction_db(level_db: float) -> float:
		over = level_db - threshold_db
		if knee_db <= 0:
			return max(0.0, over * (1.0 - 1.0 / ratio))
		if over <= -knee_db / 2:
			return 0.0
		if over >= knee_db / 2:
			return over * (1.0 - 1.0 / ratio)
		knee_position = over + knee_db / 2
		return (1.0 - 1.0 / ratio) * knee_position * knee_position / (2.0 * knee_db)

	envelope = 0.0
	output: list[float] = []
	for sample in samples:
		target = abs(sample)
		coeff = attack_coeff if target > envelope else release_coeff
		envelope = coeff * envelope + (1.0 - coeff) * target
		level_db = linear_to_db(envelope)
		reduction = gain_reduction_db(level_db)
		output.append(sample * db_to_linear(-reduction) * makeup)
	return output


def apply_tone_stack(samples: list[float], sample_rate: float, config: dict[str, Any]) -> list[float]:
	processed = highpass_one_pole(samples, sample_rate, float(config.get("highpass_hz") or 0))
	processed = apply_body_boost(processed, sample_rate, config.get("body_boost"))
	processed = preemphasize(processed, config.get("preemphasis"))
	return compress(processed, sample_rate, config.get("compressor"))


def limit_sample(sample: float, config: dict[str, Any] | None) -> tuple[float, bool]:
	config = config or {}
	drive = db_to_linear(float(config.get("drive_db", 0.0)))
	mode = config.get("mode", "hard")
	driven = sample * drive
	saturated = driven < -PRISM_NEG_LIMIT or driven > PRISM_POS_LIMIT
	if mode == "tanh":
		if driven >= 0.0:
			return PRISM_POS_LIMIT * math.tanh(driven / PRISM_POS_LIMIT), saturated
		return -PRISM_NEG_LIMIT * math.tanh(-driven / PRISM_NEG_LIMIT), saturated
	if mode == "softsign":
		if driven >= 0.0:
			return PRISM_POS_LIMIT * driven / (abs(driven) + PRISM_POS_LIMIT), saturated
		return PRISM_NEG_LIMIT * driven / (abs(driven) + PRISM_NEG_LIMIT), saturated
	if mode == "sine":
		if driven >= PRISM_POS_LIMIT:
			return PRISM_POS_LIMIT, True
		if driven <= -PRISM_NEG_LIMIT:
			return -PRISM_NEG_LIMIT, True
		if driven >= 0.0:
			return PRISM_POS_LIMIT * math.sin((driven / PRISM_POS_LIMIT) * math.pi / 2.0), saturated
		return -PRISM_NEG_LIMIT * math.sin((-driven / PRISM_NEG_LIMIT) * math.pi / 2.0), saturated
	if driven < -PRISM_NEG_LIMIT:
		return -PRISM_NEG_LIMIT, True
	if driven > PRISM_POS_LIMIT:
		return PRISM_POS_LIMIT, True
	return driven, saturated


def legacy_mastering_config(mastering: str, prism_vol: float, prism_rate: float) -> dict[str, Any]:
	if prism_vol > MAX_PRISM_VOL:
		raise SystemExit(f"prism_vol is capped at {MAX_PRISM_VOL:g}; got {prism_vol:g}")
	config: dict[str, Any] = {
		"target_rate": prism_rate,
		"prism_vol": prism_vol,
		"remove_dc": False,
		"highpass_hz": 0,
		"preemphasis": None,
		"compressor": None,
		"limiter": {"mode": "hard", "drive_db": 0},
		"quantizer": {"dither": "prism", "noise_shape": 0.0},
		"trim": {"enabled": False},
	}
	if mastering == "softclip":
		config["limiter"] = {"mode": "tanh", "drive_db": 0}
	elif mastering == "compressor":
		config["compressor"] = {
			"threshold_db": linear_to_db(0.08),
			"ratio": 4.0,
			"knee_db": 0,
			"attack_ms": 0.01,
			"release_ms": 0.01,
			"makeup_db": linear_to_db(1.8),
		}
		config["limiter"] = {"mode": "tanh", "drive_db": 0}
	elif mastering == "compressor-preemphasis":
		config["preemphasis"] = {"coeff": 0.3, "gain": 0.9}
		config["compressor"] = {
			"threshold_db": linear_to_db(0.08),
			"ratio": 4.0,
			"knee_db": 0,
			"attack_ms": 0.01,
			"release_ms": 0.01,
			"makeup_db": linear_to_db(1.8),
		}
		config["limiter"] = {"mode": "tanh", "drive_db": 0}
	return config


def load_profile(profile_json: pathlib.Path, profile_name: str) -> dict[str, Any]:
	data = json.loads(profile_json.read_text())
	profiles = data.get("profiles", {})
	if profile_name not in profiles:
		raise SystemExit(f"profile {profile_name!r} not found in {profile_json}")
	profile = dict(profiles[profile_name])
	profile.setdefault("name", profile_name)
	validate_prism_vol_config(profile, f"profile {profile_name!r}")
	return profile


def limit_samples(samples: list[float], prism_vol: float, limiter: dict[str, Any] | None) -> tuple[list[float], int]:
	limited: list[float] = []
	saturated_count = 0
	for sample in samples:
		value, saturated = limit_sample(sample * prism_vol, limiter)
		if saturated:
			saturated_count += 1
		limited.append(value)
	return limited, saturated_count


def choose_effective_prism_vol(samples: list[float], base_prism_vol: float, limiter: dict[str, Any] | None, config: dict[str, Any]) -> float:
	auto_gain = config.get("auto_gain") or {}
	if not auto_gain or not samples:
		return base_prism_vol
	min_vol = float(auto_gain.get("min_prism_vol", base_prism_vol))
	max_vol = float(auto_gain.get("max_prism_vol", base_prism_vol))
	target_rms_db = float(auto_gain.get("target_limited_rms_db", -14.5))
	max_saturation_rate = float(auto_gain.get("max_saturation_rate", 0.04))
	if max_vol <= min_vol:
		return min_vol

	best_vol = min_vol
	best_score = float("inf")
	steps = max(8, int(auto_gain.get("search_steps", 32)))
	for step in range(steps + 1):
		vol = min_vol + (max_vol - min_vol) * step / steps
		limited, saturated_count = limit_samples(samples, vol, limiter)
		limited_rms_db = linear_to_db(rms(limited))
		saturation_rate = saturated_count / len(samples)
		under_target = max(0.0, target_rms_db - limited_rms_db)
		over_target = max(0.0, limited_rms_db - target_rms_db)
		over_saturation = max(0.0, saturation_rate - max_saturation_rate)
		score = under_target * 2.0 + over_target * 0.75 + over_saturation * 150.0
		if score < best_score:
			best_score = score
			best_vol = vol
	return best_vol


def apply_mastering(samples: list[float], sample_rate: float, config: dict[str, Any]) -> tuple[list[float], list[float], int, float]:
	target_rate = float(config.get("target_rate", PRISM_RATE))
	prism_vol = float(config.get("prism_vol", PRISM_VOL))
	validate_prism_vol_config(config, "profile")
	processed = samples
	if config.get("remove_dc", True):
		processed = remove_dc(processed)
	if config.get("pre_resample_tone", False):
		processed = apply_tone_stack(processed, float(sample_rate), config)
	processed = resample_prism(processed, int(sample_rate), target_rate)
	processed = trim_active(processed, target_rate, config.get("trim"))
	if config.get("remove_dc_after_resample", False):
		processed = remove_dc(processed)
	if not config.get("pre_resample_tone", False):
		processed = apply_tone_stack(processed, target_rate, config)
	if config.get("post_highpass_hz") or config.get("post_preemphasis") or config.get("post_compressor"):
		post_config = {
			"highpass_hz": config.get("post_highpass_hz", 0),
			"preemphasis": config.get("post_preemphasis"),
			"compressor": config.get("post_compressor"),
		}
		processed = apply_tone_stack(processed, target_rate, post_config)

	effective_prism_vol = choose_effective_prism_vol(processed, prism_vol, config.get("limiter"), config)
	limited, saturated_count = limit_samples(processed, effective_prism_vol, config.get("limiter"))
	return processed, limited, saturated_count, effective_prism_vol


def quantize_limited(limited: list[float], config: dict[str, Any]) -> list[int]:
	quantizer = config.get("quantizer") or {}
	dither = quantizer.get("dither", "tpdf")
	noise_shape = float(quantizer.get("noise_shape", 0.0))
	rng = random.Random(int(quantizer.get("seed", PRISM_DITHER_SEED)))
	error_feedback = 0.0
	nibbles: list[int] = []
	for sample in limited:
		scaled = min(max(sample + PRISM_NEG_LIMIT + error_feedback * noise_shape, 0.0), 1.0)
		raw_value = scaled * 15.0
		if dither == "tpdf":
			raw_value += (rng.random() - rng.random()) * 0.5
		elif dither == "prism":
			value_floor = int(raw_value)
			error = raw_value - value_floor
			if error < 0.5:
				probability = 2.0 * error**2
			else:
				probability = 1.0 - (2.0 * (1.0 - error) ** 2)
			raw_value = value_floor + (1 if probability > rng.random() else 0)
		value = min(max(int(round(raw_value)), 0), 15)
		nibbles.append(value)
		decoded = value / 15.0 - PRISM_NEG_LIMIT
		error_feedback = sample - decoded
	return nibbles


def pack_nibbles(nibbles: list[int]) -> tuple[list[int], bytes]:
	block_count = math.ceil(len(nibbles) / BLOCK_SAMPLES) if nibbles else 0
	padded_count = block_count * BLOCK_SAMPLES
	padded = nibbles + [SILENCE_NIBBLE] * (padded_count - len(nibbles))
	packed = bytearray()
	for index in range(0, len(padded), 2):
		packed.append((padded[index] << 4) | padded[index + 1])
	return padded, bytes(packed)


def minmax2_levels(min_nibble: int, max_nibble: int) -> tuple[int, int, int, int]:
	range_value = max_nibble - min_nibble
	if range_value <= 0:
		return min_nibble, min_nibble, min_nibble, min_nibble
	return (
		min_nibble,
		min_nibble + ((range_value + 1) // 3),
		min_nibble + ((2 * range_value + 1) // 3),
		max_nibble,
	)


def encode_minmax2(padded_nibbles: list[int]) -> bytes:
	if len(padded_nibbles) % BLOCK_SAMPLES:
		raise ValueError("min/max 2-bit input must be padded to 32-sample blocks")
	payload = bytearray()
	for offset in range(0, len(padded_nibbles), BLOCK_SAMPLES):
		block = padded_nibbles[offset : offset + BLOCK_SAMPLES]
		min_nibble = min(block)
		max_nibble = max(block)
		levels = minmax2_levels(min_nibble, max_nibble)
		payload.append((min_nibble << 4) | max_nibble)
		for index in range(0, BLOCK_SAMPLES, 4):
			byte = 0
			for sample in block[index : index + 4]:
				quantized = min(range(4), key=lambda level_index: (abs(sample - levels[level_index]), level_index))
				byte = (byte << 2) | quantized
			payload.append(byte)
	return bytes(payload)


def optimized_minmax2_block(block: list[int]) -> tuple[int, int, list[int]]:
	best_error: int | None = None
	best_min = 0
	best_max = 0
	best_indices: list[int] = [0] * len(block)
	for min_nibble in range(16):
		for max_nibble in range(min_nibble, 16):
			levels = minmax2_levels(min_nibble, max_nibble)
			error = 0
			indices: list[int] = []
			for sample in block:
				level_index = min(range(4), key=lambda index: (abs(sample - levels[index]), index))
				indices.append(level_index)
				delta = sample - levels[level_index]
				error += delta * delta
			if best_error is None or error < best_error:
				best_error = error
				best_min = min_nibble
				best_max = max_nibble
				best_indices = indices
	return best_min, best_max, best_indices


def encode_minmax2_optimized(padded_nibbles: list[int]) -> bytes:
	if len(padded_nibbles) % BLOCK_SAMPLES:
		raise ValueError("optimized min/max 2-bit input must be padded to 32-sample blocks")
	payload = bytearray()
	for offset in range(0, len(padded_nibbles), BLOCK_SAMPLES):
		block = padded_nibbles[offset : offset + BLOCK_SAMPLES]
		min_nibble, max_nibble, indices = optimized_minmax2_block(block)
		payload.append((min_nibble << 4) | max_nibble)
		for index in range(0, BLOCK_SAMPLES, 4):
			byte = 0
			for quantized in indices[index : index + 4]:
				byte = (byte << 2) | quantized
			payload.append(byte)
	return bytes(payload)


def decode_minmax2(payload: bytes) -> list[int]:
	if len(payload) % 9:
		raise ValueError("min/max 2-bit payload must be a multiple of 9 bytes")
	nibbles: list[int] = []
	for offset in range(0, len(payload), 9):
		header = payload[offset]
		levels = minmax2_levels(header >> 4, header & 0x0F)
		for byte in payload[offset + 1 : offset + 9]:
			nibbles.extend(
				[
					levels[(byte >> 6) & 0x03],
					levels[(byte >> 4) & 0x03],
					levels[(byte >> 2) & 0x03],
					levels[byte & 0x03],
				]
			)
	return nibbles


def minmax2_metrics(raw_padded_nibbles: list[int], payload: bytes) -> dict[str, Any]:
	decoded = decode_minmax2(payload)
	count = min(len(raw_padded_nibbles), len(decoded))
	if count:
		errors = [raw_padded_nibbles[index] - decoded[index] for index in range(count)]
		error_rms = math.sqrt(sum(error * error for error in errors) / count)
		max_abs_error = max(abs(error) for error in errors)
	else:
		error_rms = 0.0
		max_abs_error = 0
	raw_bytes = len(raw_padded_nibbles) // 2
	return {
		"compression": "minmax2",
		"raw_packed_bytes": raw_bytes,
		"compressed_bytes": len(payload),
		"compression_ratio": len(payload) / raw_bytes if raw_bytes else 0.0,
		"minmax2_error_rms_nibbles": error_rms,
		"minmax2_max_abs_error_nibbles": max_abs_error,
		"minmax2_decoded_correlation": correlation(
			decode_nibbles_to_float(raw_padded_nibbles[:count]),
			decode_nibbles_to_float(decoded[:count]),
		),
	}


def codebook1_levels(block: list[int]) -> tuple[int, int, list[int]]:
	best_low = 0
	best_high = 0
	best_selectors: list[int] = [0] * len(block)
	best_error: int | None = None
	for low in range(16):
		for high in range(low, 16):
			error = 0
			selectors: list[int] = []
			for sample in block:
				low_error = (sample - low) * (sample - low)
				high_error = (sample - high) * (sample - high)
				if high_error < low_error:
					error += high_error
					selectors.append(1)
				else:
					error += low_error
					selectors.append(0)
			if (
				best_error is None
				or error < best_error
				or (
					error == best_error
					and (high - low, abs(low + high - 16), low, high)
					< (best_high - best_low, abs(best_low + best_high - 16), best_low, best_high)
				)
			):
				best_error = error
				best_low = low
				best_high = high
				best_selectors = selectors
	return best_low, best_high, best_selectors


def encode_codebook1(padded_nibbles: list[int]) -> bytes:
	if len(padded_nibbles) % BLOCK_SAMPLES:
		raise ValueError("codebook 1-bit input must be padded to 32-sample blocks")
	payload = bytearray()
	for offset in range(0, len(padded_nibbles), BLOCK_SAMPLES):
		block = padded_nibbles[offset : offset + BLOCK_SAMPLES]
		low, high, selectors = codebook1_levels(block)
		payload.append((low << 4) | high)
		for index in range(0, BLOCK_SAMPLES, 8):
			byte = 0
			for selector in selectors[index : index + 8]:
				byte = (byte << 1) | selector
			payload.append(byte)
	return bytes(payload)


def decode_codebook1(payload: bytes) -> list[int]:
	if len(payload) % 5:
		raise ValueError("codebook 1-bit payload must be a multiple of 5 bytes")
	nibbles: list[int] = []
	for offset in range(0, len(payload), 5):
		header = payload[offset]
		levels = (header >> 4, header & 0x0F)
		for byte in payload[offset + 1 : offset + 5]:
			for bit in range(7, -1, -1):
				nibbles.append(levels[(byte >> bit) & 0x01])
	return nibbles


def codebook1_metrics(raw_padded_nibbles: list[int], payload: bytes) -> dict[str, Any]:
	decoded = decode_codebook1(payload)
	count = min(len(raw_padded_nibbles), len(decoded))
	if count:
		errors = [raw_padded_nibbles[index] - decoded[index] for index in range(count)]
		error_rms = math.sqrt(sum(error * error for error in errors) / count)
		max_abs_error = max(abs(error) for error in errors)
	else:
		error_rms = 0.0
		max_abs_error = 0
	raw_bytes = len(raw_padded_nibbles) // 2
	return {
		"compression": "codebook1",
		"raw_packed_bytes": raw_bytes,
		"compressed_bytes": len(payload),
		"compression_ratio": len(payload) / raw_bytes if raw_bytes else 0.0,
		"codebook1_error_rms_nibbles": error_rms,
		"codebook1_max_abs_error_nibbles": max_abs_error,
		"codebook1_decoded_correlation": correlation(
			decode_nibbles_to_float(raw_padded_nibbles[:count]),
			decode_nibbles_to_float(decoded[:count]),
		),
	}


def decode_nibbles_to_float(nibbles: list[int]) -> list[float]:
	return [value / 15.0 - PRISM_NEG_LIMIT for value in nibbles]


def write_preview_wav(path: pathlib.Path, nibbles: list[int], sample_rate: float) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	decoded = decode_nibbles_to_float(nibbles)
	with wave.open(str(path), "wb") as wav:
		wav.setnchannels(1)
		wav.setsampwidth(2)
		wav.setframerate(round(sample_rate))
		frames = bytearray()
		for sample in decoded:
			value = max(-1.0, min(1.0, sample * 2.0))
			frames.extend(int(round(value * 32767)).to_bytes(2, "little", signed=True))
		wav.writeframes(bytes(frames))


def zero_crossing_rate(samples: list[float]) -> float:
	if len(samples) < 2:
		return 0.0
	crossings = 0
	previous = samples[0]
	for sample in samples[1:]:
		if (previous < 0 <= sample) or (previous >= 0 > sample):
			crossings += 1
		previous = sample
	return crossings / (len(samples) - 1)


def correlation(a: list[float], b: list[float]) -> float:
	count = min(len(a), len(b))
	if count == 0:
		return 0.0
	a = a[:count]
	b = b[:count]
	mean_a = sum(a) / count
	mean_b = sum(b) / count
	da = [value - mean_a for value in a]
	db = [value - mean_b for value in b]
	denom_a = math.sqrt(sum(value * value for value in da))
	denom_b = math.sqrt(sum(value * value for value in db))
	if denom_a == 0 or denom_b == 0:
		return 0.0
	return sum(x * y for x, y in zip(da, db)) / (denom_a * denom_b)


def compute_metrics(
	source_path: pathlib.Path,
	source_rate: int,
	source_frames: int,
	target_rate: float,
	processed: list[float],
	limited: list[float],
	nibbles: list[int],
	padded: list[int],
	saturated_count: int,
	packed: bytes,
	effective_prism_vol: float,
) -> dict[str, Any]:
	decoded = decode_nibbles_to_float(nibbles)
	peak = max((abs(sample) for sample in decoded), default=0.0)
	decoded_rms = rms(decoded)
	limited_peak = max((abs(sample) for sample in limited), default=0.0)
	limited_rms = rms(limited)
	rail_count = sum(1 for sample in nibbles if sample in (0, 15))
	error_count = min(len(limited), len(decoded))
	if error_count:
		errors = [limited[index] - decoded[index] for index in range(error_count)]
		quant_error_rms = math.sqrt(sum(error * error for error in errors) / error_count)
	else:
		quant_error_rms = 0.0
	return {
		"source": str(source_path),
		"source_rate": source_rate,
		"source_frames": source_frames,
		"source_duration_s": source_frames / source_rate,
		"target_rate": target_rate,
		"encoded_samples": len(nibbles),
		"encoded_duration_s": len(nibbles) / target_rate if target_rate else 0.0,
		"block_count": len(padded) // BLOCK_SAMPLES,
		"packed_bytes": len(packed),
		"peak": peak,
		"peak_db": linear_to_db(peak),
		"rms": decoded_rms,
		"rms_db": linear_to_db(decoded_rms),
		"crest_factor": peak / decoded_rms if decoded_rms else 0.0,
		"limited_peak": limited_peak,
		"limited_rms": limited_rms,
		"limited_rms_db": linear_to_db(limited_rms),
		"effective_prism_vol": effective_prism_vol,
		"rail_count": rail_count,
		"rail_rate": rail_count / len(nibbles) if nibbles else 0.0,
		"saturated_count": saturated_count,
		"saturation_rate": saturated_count / len(limited) if limited else 0.0,
		"zero_crossing_rate": zero_crossing_rate(decoded),
		"quantization_error_rms": quant_error_rms,
		"source_decoded_correlation": correlation(processed, decoded),
	}


def convert_wav_to_pcm4(
	input_path: pathlib.Path,
	output_path: pathlib.Path,
	config: dict[str, Any],
	preview_wav: pathlib.Path | None = None,
	report_json: pathlib.Path | None = None,
	compression: str = "pcm4",
) -> ConversionResult:
	source_samples, source_rate, source_frames = read_wav_mono_float(input_path)
	if config.get("linear_mode"):
		if source_rate != int(config.get("sample_rate", 10512)):
			raise SystemExit(f"expected {config.get('sample_rate', 10512)} Hz WAV, got {source_rate} Hz")
		gain = db_to_linear(float(config.get("gain_db", 0.0)))
		limited = [min(max(sample * gain, -PRISM_NEG_LIMIT), PRISM_POS_LIMIT) for sample in source_samples]
		processed = source_samples
		saturated_count = sum(1 for sample in source_samples if sample * gain < -PRISM_NEG_LIMIT or sample * gain > PRISM_POS_LIMIT)
		target_rate = float(source_rate)
		effective_prism_vol = gain
	else:
		target_rate = float(config.get("target_rate", PRISM_RATE))
		processed, limited, saturated_count, effective_prism_vol = apply_mastering(source_samples, source_rate, config)
	nibbles = quantize_limited(limited, config)
	padded, packed = pack_nibbles(nibbles)
	if compression == "minmax2":
		packed = encode_minmax2(padded)
	output_path.parent.mkdir(parents=True, exist_ok=True)
	output_path.write_bytes(packed)
	if preview_wav:
		write_preview_wav(preview_wav, nibbles, target_rate)
	metrics = compute_metrics(
		input_path,
		source_rate,
		source_frames,
		target_rate,
		processed,
		limited,
		nibbles,
		padded,
		saturated_count,
		packed,
		effective_prism_vol,
	)
	if compression == "minmax2":
		metrics.update(minmax2_metrics(padded, packed))
	else:
		metrics.update(
			{
				"compression": "pcm4",
				"raw_packed_bytes": len(padded) // 2,
				"compressed_bytes": len(packed),
				"compression_ratio": 1.0,
			}
		)
	metrics["profile"] = config.get("name", "")
	metrics["config"] = config
	if report_json:
		report_json.parent.mkdir(parents=True, exist_ok=True)
		report_json.write_text(json.dumps(metrics, indent=2) + "\n")
	return ConversionResult(
		source_path=input_path,
		source_rate=source_rate,
		source_frames=source_frames,
		target_rate=target_rate,
		processed_samples=processed,
		limited_samples=limited,
		nibbles=nibbles,
		padded_nibbles=padded,
		packed=packed,
		metrics=metrics,
	)


def write_metrics_csv(path: pathlib.Path, rows: list[dict[str, Any]]) -> None:
	if not rows:
		return
	path.parent.mkdir(parents=True, exist_ok=True)
	fields = [
		"species",
		"mapped_to",
		"variant",
		"profile",
		"source",
		"source_rate",
		"target_rate",
		"encoded_samples",
		"encoded_duration_s",
		"block_count",
		"packed_bytes",
		"compression",
		"raw_packed_bytes",
		"compressed_bytes",
		"compression_ratio",
		"effective_prism_vol",
		"peak_db",
		"rms_db",
		"limited_rms_db",
		"crest_factor",
		"rail_rate",
		"saturation_rate",
		"zero_crossing_rate",
		"quantization_error_rms",
		"source_decoded_correlation",
		"minmax2_error_rms_nibbles",
		"minmax2_max_abs_error_nibbles",
		"minmax2_decoded_correlation",
		"codebook1_error_rms_nibbles",
		"codebook1_max_abs_error_nibbles",
		"codebook1_decoded_correlation",
		"rom_path",
		"preview_wav",
		"pcm4_path",
		"payload_path",
		"report_json",
	]
	with path.open("w", newline="") as handle:
		writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
		writer.writeheader()
		writer.writerows(rows)


def main() -> None:
	args = parse_args()
	if args.profile_json and args.profile:
		config = load_profile(args.profile_json, args.profile)
		profile_mode = True
	else:
		config = legacy_mastering_config(args.mastering, args.prism_vol, args.prism_rate)
		profile_mode = False
	if not profile_mode and args.mode == "linear":
		config = {"linear_mode": True, "sample_rate": args.sample_rate, "gain_db": args.gain_db, "name": "linear"}
	result = convert_wav_to_pcm4(args.input, args.output, config, args.preview_wav, args.report_json, args.compression)
	print(
		f"{args.input} -> {args.output}: "
		f"{result.source_frames} input frames, {len(result.nibbles)} encoded samples, "
		f"{result.metrics['block_count']} blocks, {len(result.packed)} packed bytes, "
		f"profile={config.get('name', args.mastering)}, "
		f"clipped_or_saturated={result.metrics['saturated_count']}, "
		f"rails={result.metrics['rail_count']}"
	)


if __name__ == "__main__":
	main()
