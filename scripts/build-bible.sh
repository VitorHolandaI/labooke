#!/usr/bin/env bash
# Gera um binário standalone do bible CLI usando PyInstaller.
# Saída: dist/bible  (único arquivo, sem dependência de Python instalado)
#
# Uso:
#   ./scripts/build-bible.sh
#   ./scripts/build-bible.sh --output ~/bin   # copia para ~/bin depois
#
# Para instalar no PATH depois:
#   sudo cp dist/bible /usr/local/bin/bible

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR=""

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --output|-o) OUTPUT_DIR="$2"; shift 2 ;;
        *) echo "Uso: $0 [--output <dir>]"; exit 1 ;;
    esac
done

cd "$ROOT"

echo "==> Instalando PyInstaller no venv..."
uv pip install pyinstaller --quiet

echo "==> Localizando entry point do bible CLI..."
ENTRY="$ROOT/packages/bible/src/labooke_bible/cli.py"

# PyInstaller precisa de um __main__ wrapper para Typer
WRAPPER=$(mktemp /tmp/bible_main_XXXX.py)
cat > "$WRAPPER" <<'PYEOF'
from labooke_bible.cli import app
if __name__ == "__main__":
    app()
PYEOF

echo "==> Rodando PyInstaller..."
uv run pyinstaller \
    --onefile \
    --name bible \
    --distpath "$ROOT/dist" \
    --workpath "$ROOT/.pyinstaller-build" \
    --specpath "$ROOT/.pyinstaller-build" \
    --paths "$ROOT/packages/bible/src" \
    --paths "$ROOT/packages/core/src" \
    --hidden-import labooke_bible \
    --hidden-import labooke_bible.cli \
    --hidden-import labooke_bible._api_client \
    --hidden-import labooke_bible._history \
    --hidden-import labooke_bible._tui \
    --strip \
    "$WRAPPER"

rm -f "$WRAPPER"

BINARY="$ROOT/dist/bible"
echo ""
echo "==> Binário gerado: $BINARY"
echo "    Tamanho: $(du -sh "$BINARY" | cut -f1)"
echo ""

if [[ -n "$OUTPUT_DIR" ]]; then
    mkdir -p "$OUTPUT_DIR"
    cp "$BINARY" "$OUTPUT_DIR/bible"
    echo "==> Copiado para: $OUTPUT_DIR/bible"
    echo ""
fi

echo "Para instalar no PATH:"
echo "  sudo cp $BINARY /usr/local/bin/bible"
echo "  # ou"
echo "  cp $BINARY ~/.local/bin/bible"
