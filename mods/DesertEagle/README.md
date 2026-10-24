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
| Worktree + estrutura do projeto | feito (PR [#13](https://github.com/frederico-kluser/cyberpunk-2077-mods/pull/13) fundido) |
| Pipeline Blender (import/align/rig/lods/export) | feito, teste `SMOKE_TEST_OK` |
| Toolchain local (Blender 5.2.3 LTS + 4 add-ons + WolvenKit 9.1.0) | feito — ver [`docs/TOOLCHAIN.md`](docs/TOOLCHAIN.md) |
| Extração do molde Tsunami Nue (rig/anims/mesh/app/ent + GLB) | feito — 100 ficheiros + template GLB em [`assets/extracted/`](assets/extracted) |
| Ossos reais do `.rig` da Nue (11 ossos) | feito — [`assets/_inventory/nue_bones.txt`](assets/_inventory/nue_bones.txt), mapeados no config |
| **Modelo CS2 Desert Eagle** (escolha do dono) | feito — `desert_eagle_cs2.glb` (44 MB, 15k vértices, texturizado) |
| **Retarget CS2 → ossos da Nue** (estágio novo do pipeline) | feito — 6/6 ossos renomeados, pesos 100% preservados; inclui `clip` → `mag_slot` (carregador) |
| **Animações CS2** (50 actions: shoot/reload/draw/idle) | identificadas — 22 reais mapeadas para o CP2077 (ver [`src/blender/configs/desert_eagle_cs2.json`](src/blender/configs/desert_eagle_cs2.json)) |
| 1.º build real (align→retarget→rig→lods→export) | feito — `PIPELINE_OK`, artefactos em [`assets/work/`](assets/work) |
| Registos TweakXL/ArchiveXL + `.archive` final | **feito** — `scripts/pack_archive.ps1` → `assets/work/release/desert_eagle.archive` (6 entradas, unbundle 6/6 ✓) + loader `.xl` + TweakXL `.yaml` |
| **`.mesh` da Desert Eagle** | **feito** — construído por código (`export_geometry.py` → `mesh_write.py` → CR2W), bbox 0,146×0,038×0,253 m verificada |
| Injeção no jogo | **bloqueada por restrição do dono** — pacote pronto em `assets/work/release/`, nada vai para o jogo até autorização |

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

## Como o ativo é produzido

```text
modelo bruto (FBX/GLB, licença permissiva)
  → Blender: alinhamento sobre a Tsunami Nue (bounding box + âncoras)
  → Blender: rigging pelos nomes de ossos do .rig (Slide/Magazine/Trigger)
  → Blender: LOD 0 + LOD 1 (regra das hitboxes)
  → export .glb → WolvenKit: import sobre o .mesh base
  → .app/.ent sincronizados (baseEntity, components, resolvedDependencies limpos)
  → TweakXL (.yaml) + ArchiveXL (.xl/factory.csv) → .archive
```

Detalhe completo, comandos e armadilhas: [`docs/PIPELINE.md`](docs/PIPELINE.md).

## Limitações conhecidas

- Animações customizadas (`.re` via plugin REDmod) entram numa fase posterior;
  nesta fase usa-se a animação vanilla da Nue — é o passo recomendado para
  validar primeiro o pipeline de geometria.
- Mãos de V podem intersectar o corpo da arma (problema clássico destes mods);
  resolvem-se ajustando o alinhamento ou os `ikOffset`.

## Testado como

- `tests/test_smoke.py` do pipeline Blender: `SMOKE_TEST_OK`
- `pwsh -File tools/validate.ps1 -Static` do repositório
- em jogo: pendente (fases seguintes)

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
