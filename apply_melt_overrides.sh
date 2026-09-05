#!/bin/bash

set -e

CONFIG_FILE="${1:-arch/arm64/configs/vendor/ingres_GKI.config}"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "::error::File tidak ditemukan: $CONFIG_FILE"
    exit 1
fi

echo "Menerapkan override melt-MIX ke: $CONFIG_FILE"
BEFORE_HASH=$(md5sum "$CONFIG_FILE" | cut -d' ' -f1)

sed -i 's/^CONFIG_ARCH_CAPE=y$/# CONFIG_ARCH_CAPE is not set/' "$CONFIG_FILE"
sed -i 's/^CONFIG_ARCH_DIWALI=y$/# CONFIG_ARCH_DIWALI is not set/' "$CONFIG_FILE"

grep -q "CONFIG_ARCH_CAPE" "$CONFIG_FILE" || echo "# CONFIG_ARCH_CAPE is not set" >> "$CONFIG_FILE"
grep -q "CONFIG_ARCH_DIWALI" "$CONFIG_FILE" || echo "# CONFIG_ARCH_DIWALI is not set" >> "$CONFIG_FILE"

if ! grep -qx "CONFIG_MI_CHARGER_M81=y" "$CONFIG_FILE"; then
    echo "CONFIG_MI_CHARGER_M81=y" >> "$CONFIG_FILE"
    echo "  + CONFIG_MI_CHARGER_M81=y ditambahkan"
else
    echo "  = CONFIG_MI_CHARGER_M81 sudah ada, dilewati"
fi

AFTER_HASH=$(md5sum "$CONFIG_FILE" | cut -d' ' -f1)

echo ""
echo "--- Status akhir 3 baris kunci ---"
grep -n "CONFIG_MI_CHARGER_M81\|CONFIG_ARCH_CAPE\|CONFIG_ARCH_DIWALI" "$CONFIG_FILE"

if [ "$BEFORE_HASH" = "$AFTER_HASH" ]; then
    echo ""
    echo "Tidak ada perubahan -- file sudah benar sebelum script ini jalan."
else
    echo ""
    echo "File diperbarui."
fi
