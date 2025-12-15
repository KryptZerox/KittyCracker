#!/usr/bin/env python3

MIT License

Copyright (c) 2025 KZ

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


import sys
from math import gcd
from typing import List, Optional, Tuple

# ===================== TERMINAL COLORS =====================
class Color:
    RESET = "\033[0m"
    BOLD  = "\033[1m"
    RED   = "\033[31m"
    GREEN = "\033[32m"
    YEL   = "\033[33m"
    BLUE  = "\033[34m"
    CYAN  = "\033[36m"
    WHITE = "\033[37m"

# ===================== UI HELPERS =====================
def banner() -> None:
    print(Color.BOLD + """
============================================================
                       kittycracker
------------------------------------------------------------
 Linear OTP & RNG Forensics Framework
------------------------------------------------------------
analysis of reversible linear OTP schemes
============================================================
""" + Color.RESET)

def section(title: str, lines: List[str], color: str = Color.WHITE) -> None:
    print(color + "+" + "-" * 58)
    print("| " + title)
    print("+" + "-" * 58)
    for line in lines:
        print("| " + line)
    print("+" + "-" * 58 + Color.RESET)

def ask_yes_no(prompt: str) -> bool:
    while True:
        resp = input(Color.YEL + prompt + " [y/n]: " + Color.RESET).strip().lower()
        if resp in ("y", "n"):
            return resp == "y"

def get_three_otps() -> List[int]:
    while True:
        raw = input(Color.YEL + "Enter exactly 3 OTPs (space or comma separated): " + Color.RESET)
        parts = [p.strip() for p in raw.replace(',', ' ').split()]
        try:
            otps = [int(p) for p in parts if p]
            if len(otps) != 3:
                print(Color.RED + "You must enter exactly 3 OTPs." + Color.RESET)
                continue
            return otps
        except ValueError:
            print(Color.RED + "Invalid input: all OTPs must be integers." + Color.RESET)

# ===================== MATH UTILITIES =====================
def modinv(a: int, m: int) -> Optional[int]:
    if gcd(a, m) != 1:
        return None
    return pow(a, -1, m)

# ===================== MODEL DETECTION =====================
def detect_lcg(otps: List[int]) -> Optional[Tuple]:
    if len(otps) != 3:
        return None
    digits = len(str(otps[0]))
    trunc_mod = 10 ** digits
    modulus_candidates = [2**31, 2**32]

    o1, o2, o3 = otps

    for m in modulus_candidates:
        max_k = min(m // trunc_mod, 500)
        for k1 in range(max_k):
            s1 = o1 + k1 * trunc_mod
            for k2 in range(max_k):
                s2 = o2 + k2 * trunc_mod
                diff = (s2 - s1) % m
                inv = modinv(diff, m)
                if inv is None:
                    continue
                for k3 in range(max_k):
                    s3 = o3 + k3 * trunc_mod
                    a = ((s3 - s2) * inv) % m
                    c = (s2 - a * s1) % m
                    if (a * s2 + c) % m == s3:
                        return ("LCG", a, c, m, trunc_mod, s3)
    return None

def detect_affine_counter(otps: List[int]) -> Optional[Tuple]:
    if len(otps) != 3:
        return None
    d = 10 ** len(str(otps[0]))
    delta1 = otps[1] - otps[0]
    delta2 = otps[2] - otps[1]
    if delta1 != delta2:
        return None
    a = delta1
    b = (otps[0] - a) % d
    return ("Affine Counter", a, b, d, otps[2])

# ===================== FUTURE OTPS =====================
def generate_lcg_future(a: int, c: int, m: int, trunc_mod: int, last_state: int, count: int) -> List[int]:
    otps = []
    state = last_state
    for _ in range(count):
        state = (a * state + c) % m
        otps.append(state % trunc_mod)
    return otps

def generate_affine_future(a: int, b: int, d: int, last_otp: int, count: int) -> List[int]:
    # Compute difference
    next_otps = []
    for i in range(1, count + 1):
        val = (a * (3 + i) + b) % d  # starting from 3rd position
        next_otps.append(val)
    return next_otps

# ===================== MAIN =====================
def main() -> None:
    banner()
    otps = get_three_otps()

    proceed = ask_yes_no("Proceed with analysis of these OTPs?")
    if not proceed:
        print(Color.RED + "Exiting." + Color.RESET)
        sys.exit(0)

    section("MODEL ANALYSIS", ["Evaluating linear generator hypotheses..."], Color.BLUE)

    detectors = [detect_lcg, detect_affine_counter]
    results = []
    for detector in detectors:
        res = detector(otps)
        if res:
            results.append(res)

    if not results:
        section("ANALYSIS RESULT", ["No reversible linear model identified."], Color.RED)
        sys.exit(0)

    for model in results:
        section(
            "REVERSIBLE MODEL IDENTIFIED",
            [
                f"Model type       : {model[0]}",
                "Reversibility    : confirmed",
                "Assessment       : linear construction"
            ],
            Color.GREEN
        )

        if ask_yes_no("Generate 10 future OTPs?"):
            if model[0] == "LCG":
                a, c, m, trunc_mod, last_state = model[1:]
                future_otps = generate_lcg_future(a, c, m, trunc_mod, last_state, 10)
            elif model[0] == "Affine Counter":
                a, b, d, last_otp = model[1:]
                future_otps = generate_affine_future(a, b, d, last_otp, 10)
            else:
                future_otps = []

            print(Color.CYAN + "\nFuture OTPs:" + Color.RESET)
            for i, otp in enumerate(future_otps, 1):
                print(f"OTP +{i}: {otp}")

if __name__ == "__main__":
    main()

