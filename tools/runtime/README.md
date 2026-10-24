# `tools/runtime` — staging de runtimes de terceiros

`game-root/` é uma **staging que espelha o layout da raiz do jogo** (Cyberpunk 2077),
caminho a caminho: `red4ext/...`, `r6/...`, `bin/x64/...`, etc. Os ficheiros aqui
guardados usam exatamente os mesmos caminhos relativos que teriam na instalação do
jogo, para que qualquer movimento futuro seja um `Move-Item` 1:1 sem reorganização.

## O que guarda

Guarda os frameworks de runtime de terceiros — **RED4ext, ArchiveXL, TweakXL** e
ficheiros associados (`r6/tweaks/`, `r6/config/redsUserHints/...`) — retirados da
pasta do jogo e mantidos aqui **até o proprietário autorizar a instalação em jogo**.
Também serve de inventário comprovativo do que foi instalado pela automação: nada
destes componentes pode viver na instalação do jogo.

## O que não faz (regra do proprietário)

**Nada daqui é instalado no jogo por si só.** Esta pasta não tem qualquer efeito
automático sobre a instalação do jogo:

- nenhum build, hook, script de testes ou arranque do repositório copia ou desdobra
  estes ficheiros para a pasta do jogo;
- a colocação em jogo acontece apenas com **autorização explícita do proprietário**,
  através do passo de deploy dedicado (`tools/deploy.ps1`), e nunca implicitamente;
- enquanto não houver autorização, estes ficheiros permanecem apenas no worktree.

## Convenções

- Preservar sempre o caminho relativo à raiz do jogo ao mover ficheiros para dentro
  ou para fora de `game-root/`.
- As licenças de cada componente (`LICENSE`, `THIRD_PARTY_LICENSES`) acompanham o
  respetivo código; binários de terceiros nunca são reescritos.
- Ao desdobrar em jogo, o passo de deploy deve copiar (não mover) a partir daqui e
  registar o que foi instalado, para o staging continuar a ser a fonte de verdade.
- O staging inclui também byproducts de runtime do RED4ext (`red4ext/logs/`,
  `red4ext/config.ini`) preservados para diagnóstico das execuções de smoke-test.
- Os binários de terceiros **não são versionados**: `game-root/` está em
  `.gitignore` e só o conteúdo deste `README.md` entra no repositório.

## Recriar o staging (re-download dos binários)

Para reproduzir `game-root/` sem versionar binários, baixar as releases exatas
e extrair preservando os caminhos relativos à raiz do jogo (é assim que os
releases já vêm organizados):

```powershell
# RED4ext v1.30.0 — atenção: o match do nome do asset é case-sensitive
gh release download v1.30.0 -R WopsS/RED4ext -p "red4ext-1.30.0.zip" -D <downloads>

# ArchiveXL 1.27.5
gh release download 1.27.5 -R psiberx/cp2077-archive-xl -p "ArchiveXL-*.zip" -D <downloads>

# TweakXL 1.11.5
gh release download 1.11.5 -R psiberx/cp2077-tweak-xl -p "TweakXL-*.zip" -D <downloads>
```

Depois de extrair, mover cada subárvore para `game-root/` mantendo o layout
`red4ext/...`, `r6/...`, `bin/x64/...` da raiz do jogo.

## Lição: `CreationTime` vs `LastWriteTime` (Windows)

Ao extrair um zip no Windows, o `LastWriteTime` do ficheiro é o do arquivo —
pode ser antigo (ex.: `2026-03-09`, data de build do release) — enquanto o
`CreationTime` regista quando o ficheiro chegou ao disco (ex.: `2026-10-23
21:56:58`). Foi exatamente assim que se atribuíram à nossa automação o
`bin/x64/winmm.dll` e o núcleo do RED4ext: `LastWriteTime` antigo, mas
`CreationTime` de hoje, todos no mesmo segundo da mesma extração.

Regras de atribuição usadas neste projeto:

- **`CreationTime` é o critério primário** ("foi colocado aqui por nós nesta
  sessão?"); ficheiros extraídos no mesmo segundo = mesma operação nossa;
- um `LastWriteTime` **antigo não prova** que o ficheiro é pré-existente
  (a extração de zip preserva a data do arquivo);
- um `LastWriteTime` **recente não prova** que é nosso (o jogo também escreve
  nos seus próprios ficheiros);
- o vanilla de Cyberpunk 2077 não traz `winmm.dll` nem `RED4ext.dll` — a
  presença destes ficheiros é sempre obra de uma instalação de runtime;
- em caso de dúvida: **não tocar**, registar no relatório e escalar.
