# Leitor

→ [overview.md](overview.md) | [api.md](api.md)

## Formatos suportados

| Formato | Viewer     | Notas                        |
|---------|------------|------------------------------|
| PDF     | pdf.js     | Escala ao container, rápido  |
| EPUB    | epub.js    | Fluxo de texto reflowable    |
| TXT/MD  | próprio    | Paginação por linhas         |

## Controles do leitor PDF

Barra de controles (topo):

| Botão           | Ação                                      |
|-----------------|-------------------------------------------|
| ← Prev / Next → | Página anterior / próxima                |
| contador        | `12 / 300` ou `12–13 / 300` (2 páginas)  |
| ☆ Marcar        | Adiciona bookmark na página atual         |
| ⊟ 2 pág.        | Alterna entre 1 e 2 páginas lado a lado   |
| ⛶ Tela cheia    | Cobre o viewport inteiro (esconde navbar) |

**Teclas:** ← → ↑ ↓ navegam. `Esc` sai da tela cheia.

## Tela cheia

O leitor usa `position: fixed; inset: 0` — a topbar e o sidebar  
somem por baixo. O PDF ocupa 100 % da janela do browser.  
Sair: botão **⊠ Sair** ou `Esc`.

## 2 páginas

Renderiza dois canvases lado a lado, cada um escalado para metade  
da largura. Avanço de 2 em 2. Contador mostra o intervalo `N–N+1`.

## Bookmarks

- **Sidebar** (BookmarkDrawer): lista, adiciona com label + nota, navega
- **Controles do viewer**: botão ☆ Marcar para acesso direto em tela cheia
- Página já marcada mostra ★ Marcado (desabilitado)

## Progresso de leitura

A página atual é salva automaticamente (debounced). Ao reabrir  
o livro, o leitor retoma da última página.
