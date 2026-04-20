from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from scipy.signal import resample_poly


OBS_NAME = "Knacksat2_13753740"

HEX_FRAMES = [
    "90 A6 60 82 96 40 76 90 A6 60 96 40 40 61 03 90 00 C6 69 00 00 01 01 00 61 00 00 00 00 66 00 00 00 00 00 00 18 80 31 00 3F 35 5E 3F 89 2B 89 3E 00 00 00 00 EC 51 B8 3C CD CC 1C 3F 00 00 00 00 00 00 00 00 9A 99 83 40 CD CC AC 3F 00 00 00 00 00 00 00 3E 00 00 A4 40 00 00 00 00 00 00 00 00 9A 99 97 40 71 3D 97 40 71 3D 9D 40 52 B8 A8 40 7B 94 05 41 00 00 67 00 01 C6 00 00 00 23 41 00 00 36 41 00 00 33 41 00 00 32 41 0A 57 05 41 DB F9 9E BE CD 4C 05 41 B6 F3 9D 3E EE 78 00 03 58 06 00 42 43 4E",
    "90 A6 60 82 96 40 76 90 A6 60 96 40 40 61 03 F0 00 00 69 00 00 01 01 00 61 00 00 00 00 66 00 00 00 00 00 00 00 00 00 00 3F 35 5E 3F 91 AB B8 3E 00 00 00 00 EC 51 B8 3C CD CC 1C 3F 00 00 00 00 00 00 00 00 9A 99 83 40 CD CC AC 3F 00 00 00 00 00 00 00 3E 00 00 A4 40 00 00 00 00 00 00 00 00 9A 99 97 40 71 3D 97 40 71 3D 9D 40 52 B8 A8 40 7B 94 05 41 00 00 67 00 01 C6 00 00 00 33 41 00 00 36 C1 00 00 33 41 00 00 32 41 0A 57 05 41 DB F9 9E BE CD 4C 05 41 B6 F3 9D 3E EE 78 00 03 58 06 00 42 43 4E",
    "90 A6 60 82 96 40 76 90 A6 60 96 40 40 61 03 F0 00 00 69 00 00 01 01 00 61 00 00 00 00 66 00 00 00 00 00 00 00 03 30 06 7F 5A 5C 0C 75 BA CE 7C 00 00 00 00 FE D4 78 79 C6 4B 37 7E 00 00 00 00 00 00 00 00 9A 99 15 81 00 00 10 7F 00 00 00 00 00 00 00 7C CC CC 44 81 00 00 00 00 00 00 00 00 48 E1 2C 81 86 EB 2B 81 E2 7A 36 81 34 33 4F 81 34 33 0B 82 00 00 CE 00 02 8C 01 00 01 66 82 00 00 6C 82 00 00 66 82 00 00 64 82 52 B8 0A 82 A2 45 36 7D 9B 99 0A 82 A2 45 36 7D DC F1 00 00 D0 00 00 84 86 1C F8",
    "90 A6 60 82 96 40 76 90 A6 60 96 40 40 61 03 F0 00 00 69 00 00 01 01 00 61 00 00 00 00 66 00 00 00 00 00 00 00 00 00 00 7F 6A 6C 3F 8B 6C 67 3E 00 00 00 00 7F 6A BC 3C E3 A5 1B 3F 00 00 00 00 00 00 00 00 CD CC 8A 40 00 00 88 3F 00 00 00 00 00 00 00 3E 66 66 A2 40 00 00 00 00 00 00 00 00 A4 70 96 40 C3 F5 95 40 71 3D 9B 40 9A 99 A7 40 9A 99 05 41 00 00 67 00 01 C6 00 00 00 33 41 00 00 36 41 00 00 33 41 00 00 32 41 29 5C 05 41 D1 22 9B BE CD 4C 05 41 D1 22 9B 3E EE 78 00 00 68 00 00 42 43 4E"
]

SAMPLE_RATE = 78125.0
FS_OUT_I = int(round(SAMPLE_RATE))

MOD_SAMPLE_RATE = 76800.0
FS_IN_I = int(round(MOD_SAMPLE_RATE))
BAUD_RATE = 9600.0
FREQ_DEV_HZ = 3500.0
AMPLITUDE = 0.8

PREAMBLE_LEN = 16
POSTAMBLE_LEN = 64

FINAL_ZERO_TAIL_SEC = 0.065

SYNC_FLAG = 0x7E

MOD_SPS = int(round(MOD_SAMPLE_RATE / BAUD_RATE))
GCD_FS = math.gcd(FS_IN_I, FS_OUT_I)
RESAMPLE_UP = FS_OUT_I // GCD_FS
RESAMPLE_DOWN = FS_IN_I // GCD_FS

out_dir = Path(f"{OBS_NAME}_replayed_iq_out")
out_dir.mkdir(exist_ok=True)


def parity(x):
    return x.bit_count() & 1


class GNUradioLFSR:
    def __init__(self, mask: int, seed: int, reg_len: int):
        self.mask = mask
        self.state = seed
        self.reg_len = reg_len

    def next_bit_scramble(self, input_bit: int) -> int:
        output = self.state & 1
        newbit = parity(self.state & self.mask) ^ (input_bit & 1)
        self.state = ((self.state >> 1) | (newbit << self.reg_len))
        return output


def crc16_hdlc(data):
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0x8408
            else:
                crc >>= 1
    return (~crc) & 0xFFFF


def append_fcs_lsb_first(data):
    crc = crc16_hdlc(data)
    return data + crc.to_bytes(2, "little")


def exact_satnogs_serial_bytes_and_valid_bits(body_with_fcs, preamble_len, postamble_len):
    bits = []

    # Preamble flags
    for _ in range(preamble_len):
        for j in range(8):
            bits.append((SYNC_FLAG >> (7 - j)) & 0x1)

    # Body + FCS, serialized LSB-first per byte, with HDLC bit stuffing
    ones_run = 0
    for byte in body_with_fcs:
        for j in range(8):
            bit = (byte >> j) & 0x1
            bits.append(bit)

            if bit:
                ones_run += 1
                if ones_run == 5:
                    bits.append(0)
                    ones_run = 0
            else:
                ones_run = 0

    # Postamble flags
    for _ in range(postamble_len):
        for j in range(8):
            bits.append((SYNC_FLAG >> (7 - j)) & 0x1)

    bits = np.asarray(bits, dtype=np.uint8)
    return bits, int(bits.size)


def g3ruh_scramble_exact_satnogs(bits):
    bits = np.asarray(bits, dtype=np.uint8) & 1
    lfsr = GNUradioLFSR(mask=0x21, seed=0x0, reg_len=16)

    out = np.empty(bits.size, dtype=np.uint8)
    for i, bit in enumerate(bits):
        out[i] = lfsr.next_bit_scramble(int(bit))

    return out


def nrzi_encode_exact_satnogs(bits):
    bits = np.asarray(bits, dtype=np.uint8) & 1

    prev = 0
    out = np.empty(bits.size, dtype=np.uint8)

    for i, bit in enumerate(bits):
        if bit == 0:
            prev ^= 1
        out[i] = prev

    return out


def build_one_frame_bits(frame_hex):
    body = bytes.fromhex(frame_hex)
    body_with_fcs = append_fcs_lsb_first(body)

    tx_bits, valid_bits = exact_satnogs_serial_bytes_and_valid_bits(
        body_with_fcs,
        preamble_len=PREAMBLE_LEN,
        postamble_len=POSTAMBLE_LEN,
    )
    tx_bits = g3ruh_scramble_exact_satnogs(tx_bits)
    tx_bits = nrzi_encode_exact_satnogs(tx_bits)

    return tx_bits[:valid_bits]

def resample_complex_polyphase(x):
    y = resample_poly(x.astype(np.complex128, copy=False), RESAMPLE_UP, RESAMPLE_DOWN)
    return y.astype(np.complex64, copy=False)


def make_iq_from_bits(tx_bits):
    bits = np.asarray(tx_bits, dtype=np.uint8) & 1
    if bits.size == 0:
        raise ValueError("tx_bits is empty")

    nrz = np.where(bits == 0, 1.0, -1.0).astype(np.float64, copy=False)
    drive = np.repeat(nrz, MOD_SPS)

    sensitivity = 2.0 * math.pi * FREQ_DEV_HZ / MOD_SAMPLE_RATE
    phase = np.cumsum(sensitivity * drive, dtype=np.float64)
    phase -= phase[0]

    iq_mod = (AMPLITUDE * np.exp(1j * phase)).astype(np.complex64)
    iq = resample_complex_polyphase(iq_mod)

    zero_tail_len = int(round(FINAL_ZERO_TAIL_SEC * SAMPLE_RATE))
    if zero_tail_len > 0:
        iq = np.concatenate([iq, np.zeros(zero_tail_len, dtype=np.complex64)])

    return iq


frame_bit_arrays = [build_one_frame_bits(frame_hex) for frame_hex in HEX_FRAMES]
all_tx_bits = np.concatenate(frame_bit_arrays) if frame_bit_arrays else np.empty(0, dtype=np.uint8)

bits_file = out_dir / f"{OBS_NAME}_tx_bits_u8.bin"
all_tx_bits.tofile(bits_file)

all_iq = make_iq_from_bits(all_tx_bits)
combined_file = out_dir / f"{OBS_NAME}_replayed_cf32.raw"
all_iq.tofile(combined_file)

print("Done")
print("Bits file:", bits_file)
print("Combined IQ file:", combined_file)
print("Output folder:", out_dir)