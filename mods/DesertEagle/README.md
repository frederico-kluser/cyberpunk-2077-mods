# Desert Eagle

Uma **Desert Eagle .50 AE** para *Cyberpunk 2077*: malha 3D nova por cima do
esqueleto e das animações da **Tsunami Nue**, adicionada de forma **aditiva**
(nenhum ficheiro vanilla é substituído) via ArchiveXL + TweakXL.

O pipeline que produz o ativo é automatizado com Blender + Python (`bpy`) e
corre em modo `--background`, portanto cada etapa é testável e reproduzível —
ver [`src/blender/README.md`](src/blender/README.md).

## Estado

| Etapa | Estado |
| --- | --- |
| Toolchain local (Blender 5.2.3 LTS + 4 add-ons + WolvenKit 9.1.0) | feito — ver [`docs/TOOLCHAIN.md`](docs/TOOLCHAIN.md) |
| Molde Tsunami Nue (rig/anims/mesh/app/ent extraídos) | feito — [`assets/extracted/`](assets/extracted) |
| **Modelo CS2 Desert Eagle** (escolha do dono) | feito — `desert_eagle_cs2.glb` (44 MB, 15k vértices) |
| **Retarget CS2 → ossos da Nue** | feito — 6/6 ossos, pesos 100% preservados (inclui `clip` → `mag_slot`) |
| **`.mesh` próprio** (escritor de buffer, sem GUI) | feito — bbox 0,146×0,038×0,253 m, 2 LODs, skinning verificado |
| **Texturas CS2** (`.xbm` writer: RGBA + BC5) | feito — albedo + normais 4K, roundtrip CR2W verificado |
| **Materiais** (`metal_base` + nossos mapas) | feito — a renderizar com o visual CS2 (ver renders em `docs/renders/`) |
| **Animações CS2** (13 clips → `.anims`, sem redMod) | feito — codecs Simd + Compressed, roundtrip CR2W, integração malha×animação verificada |
| **Pacote final** (archive 10 entradas + `.xl` + yaml) | feito — `verify_release.py` (35+ checks) `RELEASE_VERIFY_OK` |
| **Build de 1 comando** | feito — `scripts/build_release.ps1` (geometria → anims → archive → verify) |
| Injeção no jogo | **bloqueada por restrição do dono** — ver [`docs/ACCEPTANCE.md`](docs/ACCEPTANCE.md) |

## Requisitos

- Cyberpunk 2077 para PC, versão **2.5** (`3.0.88.x`)
- [redscript](https://github.com/jac3km4/redscript/releases) `>=0.5.32`
- [ArchiveXL](https://github.com/psiberx/cp2077-archive-xl) `>=1.18.0`
- [TweakXL](https://github.com/psiberx/cp2077-tweak-xl) `>=1.10.0`
- [Cyber Engine Tweaks](https://github.com/maximilionus/cyber-engine-tweaks) (só para o atalho de teste)

## Instalação

> **Restrição do dono (em vigor):** nada é injetado no jogo por enquanto — todo o
> trabalho, do modelo ao `.archive`, vive **na worktree** (`mods/DesertEagle/`,
> com os artefactos em `assets/work/`). A instalação no jogo só acontece quando o
> dono autorizar.

1. Instale redscript, ArchiveXL e TweakXL na raiz do jogo. *(quando autorizado)*
2. Extraia o zip do release para a raiz do jogo, fundindo pastas:
   - `r6\scripts\DesertEagle\` — helper Redscript de teste
   - `r6\tweaks\desert_eagle.yaml` — registo do item (TweakXL)
   - `archive\pc\mod\desert_eagle.archive` — malha/entidade/aparências (ArchiveXL)
3. Inicie o jogo.

## Teste rápido em jogo

Com o Cyber Engine Tweaks:

```
Game.AddToInventory("Items.DesertEagle", 1)
```

ou, a partir de Redscript: `DesertEagleInventory.Give();`

Confirme: item no inventário, arma nas mãos em primeira pessoa e no Modo
Fotografia. Se a arma aparecer com o visual da Nue, veja a
[matriz de diagnóstico](docs/PIPELINE.md#matriz-de-diagnóstico).

## Configuração

Os atributos de gameplay (dano, cadência, carregador, recuo) vivem em
`src/tweakxl/desert_eagle.yaml`; a estética e as variantes de cor em
`src/archivexl/`. Os ficheiros `.reds` só expõem o helper de spawn.

## Construir (1 comando)

```powershell
pwsh -File scripts/build_release.ps1
```

Reconstrói o mod do zero — geometria CS2 → material → `.mesh` → `.app/.ent` →
texturas → animações CS2 → factory → `.archive` — e **recusa terminar sem
`RELEASE_VERIFY_OK`**. Saída em `assets/work/release/`.

## Como o ativo é produzido

```text
modelo CS2 (GLB) + texturas CS2 (4K)
  → Blender: retarget de ossos + fit à bbox da Nue + skinning (top-4)
  → escritor de buffer .mesh (streams PT_Short4N/…) → CR2W
  → escritor .xbm (albedo RGBA + normais BC5, green flip DirectX)
  → material metal_base.mt com os nossos mapas
  → .app/.ent transformados do molde (refs vanilla limpos, anims repontadas)
  → 13 clips CS2 amostrados → codecs .anims (Simd/Compressed) → CR2W
  → TweakXL (.yaml) + ArchiveXL (.xl/factory.csv) → .archive
```

Tudo em código (sem GUI), com verificação numérica em cada codec.
Detalhe, comandos e armadilhas: [`docs/PIPELINE.md`](docs/PIPELINE.md).

## Limitações conhecidas

- As mãos de V podem intersectar ligeiramente o corpo da arma (problema clássico
  destes mods) — a sessão de teste em jogo ([`docs/ACCEPTANCE.md`](docs/ACCEPTANCE.md))
  é onde se calibra; o ajuste é a rotação A do grip (`assets/work/de_align.json`
  → root das animações, ver [`docs/ANIMS.md`](docs/ANIMS.md)).
- As variantes NPC/dual-wield mantêm as animações vanilla da Nue (escolha
  deliberada — só o conjunto de primeira-pessoa foi substituído).

## Testado como

- `scripts/run_tests.py` (6 verificações: codecs BCn + animação, pacote,
  conteúdo do mesh, 13 clips, alinhamento do grip): `RUN_TESTS_OK (6/6)`
- conteúdo de texturas (`scripts/verify_xbm_content.py`): cor exata (0,000/255),
  normais BC5 0,87/255, green-flip DirectX provado
- skinning semântico (`scripts/verify_skin_mapping.py`): trigger 1,5 cm ·
  slide 1,6 cm · hammer 2,4 cm dos seus ossos
- renders de integração: recarga com o carregador a sair (`docs/renders/`)
- `pwsh -File tools/validate.ps1 -Static` do repositório
- em jogo: pendente da autorização do dono (`docs/ACCEPTANCE.md`)

## Licença

MIT — ver [LICENSE](../../LICENSE).

**Atenção ao modelo 3D em uso:** o modelo ativo (`assets/raw/desert_eagle_cs2.glb`)
é um asset de terceiros derivado do Counter-Strike 2 (Valve), fornecido pelo
dono do projeto para desenvolvimento — **não distribuir publicamente** sem
resolver a questão de licença (ver [`assets/sources.json`](assets/sources.json)).

O modelo de referência anterior mantém-se no projeto para renders de estúdio,
com atribuição CC-BY 3.0:

> "Rigged Desert Eagle" by PuKkBuMXDD (Артур Мигранов) —
> [poly.pizza/m/e9k4dwOzCX](https://poly.pizza/m/e9k4dwOzCX) — licensed under
> [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/).
