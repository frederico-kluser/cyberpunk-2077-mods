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
| Worktree + estrutura do projeto | feito |
| Pipeline Blender (import/align/rig/lods/export) | feito, teste `SMOKE_TEST_OK` |
| Toolchain local (Blender 5.2.3 LTS + 4 add-ons + WolvenKit 9.1.0) | feito — ver [`docs/TOOLCHAIN.md`](docs/TOOLCHAIN.md) |
| Frameworks de runtime (RED4ext + ArchiveXL 1.27.5 + TweakXL 1.11.5) | ArchiveXL/TweakXL instalados; RED4ext em instalação |
| Extração do molde Tsunami Nue (`.mesh`/`.rig`/`.anims`) | em curso |
| Modelo 3D da Desert Eagle (licença permissiva) | candidatos registados em [`assets/sources.json`](assets/sources.json) |
| Registos TweakXL/ArchiveXL + `.archive` final | templates prontos em [`src/tweakxl`](src/tweakxl) e [`src/archivexl`](src/archivexl) |

## Requisitos

- Cyberpunk 2077 para PC, versão **2.5** (`3.0.88.x`)
- [redscript](https://github.com/jac3km4/redscript/releases) `>=0.5.32`
- [ArchiveXL](https://github.com/psiberx/cp2077-archive-xl) `>=1.18.0`
- [TweakXL](https://github.com/psiberx/cp2077-tweak-xl) `>=1.10.0`
- [Cyber Engine Tweaks](https://github.com/maximilionus/cyber-engine-tweaks) (só para o atalho de teste)

## Instalação

1. Instale redscript, ArchiveXL e TweakXL na raiz do jogo.
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

MIT — ver [LICENSE](../../LICENSE). O modelo 3D de origem tem a sua própria
licença, registada em `docs/TOOLCHAIN.md`.
