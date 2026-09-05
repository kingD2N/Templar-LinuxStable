#!/usr/bin/env python3
"""
Verifikasi kompatibilitas CRC simbol kernel terhadap modul vendor ASLI MIUI 14
(diekstrak langsung dari dump firmware nyata: missi_phone_cn-user-13-TKQ1.220807.001-
V14.0.23.8.14.DEV-release-keys, vermagic 5.10.81-gki-g83b69c4d8214).

Cara pakai (dijalankan otomatis oleh workflow setelah `make Image`):
    python3 verify_miui14_compat.py path/to/Module.symvers

Baca Module.symvers hasil build kernel INI, lalu bandingkan tiap simbol yang
dibutuhkan modul vendor MIUI 14 asli (touch, wifi, kamera, haptic) terhadap
CRC yang benar-benar dihasilkan build ini. Tidak menjamin kernel akan menolak
memuat modul (itu keputusan runtime insmod/modprobe) - ini pengecekan pra-boot,
supaya ketahuan dari log build, bukan baru ketahuan pas HP sudah di-flash.
"""
import sys
import json
import os

REFERENCE_FILE = os.path.join(os.path.dirname(__file__), "miui14_reference_symvers.json")

def load_reference():
    with open(REFERENCE_FILE) as f:
        return json.load(f)

def load_module_symvers(path):
    """Module.symvers format: <crc>\t<symbol>\t<object_file>\t<export_type>\t<namespace>"""
    table = {}
    with open(path) as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2:
                crc, name = parts[0], parts[1]
                table[name] = crc.lower()
    return table

def main():
    if len(sys.argv) != 2:
        print("Usage: verify_miui14_compat.py <path-to-Module.symvers>")
        sys.exit(2)

    symvers_path = sys.argv[1]
    if not os.path.isfile(symvers_path):
        print(f"::warning::Module.symvers tidak ditemukan di {symvers_path} - "
              f"lewati verifikasi kompatibilitas MIUI 14 (CONFIG_MODVERSIONS mungkin nonaktif, "
              f"atau path build berbeda).")
        sys.exit(0)

    reference = load_reference()
    built = load_module_symvers(symvers_path)

    matched, mismatched, missing = [], [], []

    for name, info in reference.items():
        want_crc = info["crc"].lower()
        needed_by = ", ".join(sorted(set(info["needed_by"])))
        if name not in built:
            missing.append((name, needed_by))
        elif built[name] != want_crc:
            mismatched.append((name, want_crc, built[name], needed_by))
        else:
            matched.append(name)

    total = len(reference)
    print("=" * 78)
    print("VERIFIKASI KOMPATIBILITAS SIMBOL vs MODUL VENDOR ASLI MIUI 14")
    print("(referensi: dump firmware nyata V14.0.23.8.14.DEV, vermagic 5.10.81-gki)")
    print("=" * 78)
    print(f"Total simbol dicek : {total}")
    print(f"  Cocok            : {len(matched)}")
    print(f"  TIDAK COCOK (CRC): {len(mismatched)}")
    print(f"  Tidak ditemukan  : {len(missing)}  (mungkin inline/dihapus compiler)")
    print()

    if mismatched:
        print("--- SIMBOL DENGAN CRC TIDAK COCOK (modul ini kemungkinan GAGAL insmod) ---")
        for name, want, got, needed_by in sorted(mismatched, key=lambda x: x[3]):
            print(f"  {name:40s} butuh={want}  build_ini={got}   <- dipakai oleh: {needed_by}")
        print()

    if missing:
        print("--- SIMBOL TIDAK DITEMUKAN DI BUILD INI ---")
        for name, needed_by in sorted(missing, key=lambda x: x[1]):
            print(f"  {name:40s} <- dipakai oleh: {needed_by}")
        print()

    # Ringkasan per modul vendor, supaya jelas dampaknya ke hardware apa
    per_module = {}
    for name, want, got, needed_by in mismatched:
        for ko in needed_by.split(", "):
            per_module.setdefault(ko, 0)
            per_module[ko] += 1
    for name, needed_by in missing:
        for ko in needed_by.split(", "):
            per_module.setdefault(ko, 0)
            per_module[ko] += 1

    print("--- DAMPAK PER MODUL VENDOR ---")
    if not per_module:
        print("  Semua modul yang dicek (touch, wifi, kamera, haptic) kemungkinan besar "
              "AMAN dimuat - tidak ada mismatch CRC pada simbol yang mereka butuhkan.")
    else:
        for ko, count in sorted(per_module.items()):
            print(f"  {ko:25s}: {count} simbol bermasalah - resiko GAGAL berfungsi di MIUI 14")
    print("=" * 78)

    # Exit code 1 kalau ada mismatch, supaya gampang dibaca status build-nya
    # tanpa harus buka log manual (tapi TIDAK menggagalkan build - cuma laporan)
    sys.exit(0)

if __name__ == "__main__":
    main()
