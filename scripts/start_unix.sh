#!/bin/bash
set -eu
dw_root=${1:?Project folder missing}
shift
cd "$dw_root"
dw_uv=$(command -v uv || true)
if [ -z "$dw_uv" ] && [ -x "$HOME/.local/bin/uv" ]; then
  dw_uv="$HOME/.local/bin/uv"
fi
if [ -z "$dw_uv" ]; then
  echo "Python kurulumunu yöneten uv henüz kurulu değil."
  echo "Resmi astral.sh yükleyicisi indirilecek; yönetici/sudo gerekmez."
  printf "uv kurulsun mu? [E/h]: "
  read -r dw_answer
  case "$dw_answer" in h|H|n|N) echo "Kurulum iptal edildi."; exit 1;; esac
  command -v curl >/dev/null 2>&1 || { echo "curl bulunamadı. docs/kurulum.md rehberine bakın."; exit 1; }
  dw_installer=$(mktemp "${TMPDIR:-/tmp}/deal-watcher-uv.XXXXXX")
  trap 'rm -f "$dw_installer"' EXIT
  curl -fsSL https://astral.sh/uv/install.sh -o "$dw_installer"
  UV_NO_MODIFY_PATH=1 sh "$dw_installer"
  dw_uv="$HOME/.local/bin/uv"
  [ -x "$dw_uv" ] || { echo "uv bulunamadı. docs/kurulum.md rehberini kontrol edin."; exit 1; }
fi
echo "Python ve uygulama bağımlılıkları hazırlanıyor (ilk açılış biraz sürebilir)..."
"$dw_uv" sync --locked --no-dev
if [ "${1:-}" = "--check" ]; then
  exec "$dw_root/.venv/bin/python" -m deal_watcher.cli validate-config
fi
exec "$dw_root/.venv/bin/python" -m deal_watcher.launcher
