# Pipeline da Desert Eagle — do modelo ao jogo

Este documento é a fonte de verdade operacional do mod. Cada passo indica a
ferramenta, o comando exato e a armadilha que custou descobrir. As regras da
REDengine 4 referenciadas aqui estão implementadas em
[`../src/blender/de_pipeline/`](../src/blender/de_pipeline/) e verificadas pelo
teste [`test_smoke.py`](../src/blender/tests/test_smoke.py).

## 0. Princípio

A REDengine 4 não aceita ativos 3D brutos. O fluxo é de mão dupla: **extrair um
ativo do jogo como molde → editar no Blender → injetar de volta**. A Tsunami Nue
(`Items.Preset_Nue_Default`) é o molde: herdam-se o esqueleto (`.rig`), o
conjunto de animações (`.anims`) e o grafo de estados (`.animgraph`).

> **Restrição do dono (em vigor):** *por enquanto nada é injetado no jogo.* Todo
> o pipeline — extração (read-only), Blender, montagem do `.archive` e pacotes —
> corre e guarda **na worktree**, de começo ao fim. Os passos §5–§7 (WolvenKit
> → `archive\pc\mod`, TweakXL em `r6\tweaks`, teste em jogo) ficam documentados
> mas **não executados** até autorização explícita.

## 1. Ferramentas

| Ferramenta | Papel |
| --- | --- |
| WolvenKit | extrair `.mesh`/`.rig`/`.anims`/`.app`/`.ent` do jogo, importar o `.glb`, empacotar o `.archive` |
| Blender 5.2 + Cyberpunk Blender Add-on | geometria, pesos, LODs, export `.glb` |
| REDmod Blender plugin | export `.re` das animações editadas (fase posterior) |
| BlenderMCP | controlo do Blender por linguagem natural (`execute_blender_code`) |
| TweakXL | registos do item (`r6/tweaks/*.yaml`) |
| ArchiveXL | item aditivo + variantes de aparência (`.xl`, `factory.csv`) |

## 2. Extrair o molde (WolvenKit)

1. Criar projeto WolvenKit apontado para o jogo instalado.
2. Procurar o `.app` da Nue (Asset Browser: `handgun nue`) e adicioná-lo ao
   projeto; o WolvenKit puxa as dependências. **Sempre que houver duplicados,
   preferir a versão `ep1`** (Phantom Liberty).
3. Extrair para `assets/extracted/`:
   - `w_handgun_nue.mesh` (com `LOD Filter` **desmarcado** — é preciso ver os LODs todos)
   - `w_handgun_nue.rig`
   - `w_handgun_nue.anims` (export com **Include Root Motion**)
   - o `.ent` e o `.app` do item
4. Exportar o `.glb` de referência (`WithMaterials` para texturas, depois
   `WithRig` para o esqueleto) — é o `base_template` do pipeline Blender.

O inventário exato de ficheiros extraídos fica registado em
[`TOOLCHAIN.md`](TOOLCHAIN.md) (versões e hashes).

## 3. Modelo da Desert Eagle

Requisitos do modelo de origem: licença que permita mods (CC0/CC-BY), geometria
limpa, escala aproximada de pistola, peças móveis separáveis (corrediça,
carregador, gatilho) para virarem submalhas. O caminho escolhido e a licença
ficam registados em [`TOOLCHAIN.md`](TOOLCHAIN.md).

## 4. Blender — etapas automatizadas

Comandos exatos em [`../src/blender/README.md`](../src/blender/README.md).
Resumo das regras implementadas:

1. **Alinhamento** (`align.py`) — escala uniforme pela diagonal da bounding box
   + translação para coincidir as âncoras (por omissão `bbox_min`). Nunca
   esticar por eixo: as hitboxes da REDengine 4 derivam das malhas de LOD
   inferior e um eixo esticado fica invisível no jogo.
2. **Limpeza** (`scene.py`) — `Merge by Distance` para soldar costuras.
3. **Submalhas** — peças com shaders distintos (miras emissivas, carregador,
   corpo metálico) ficam em objetos/submalhas separados (`submesh_00`, …).
4. **Rigging** (`rigging.py`) — um grupo de vértices por osso do `.rig`, com o
   nome **exato** do osso; peso `1.0` nas peças mecânicas; apagar grupos sem
   osso correspondente; máximo 8 influências por vértice + normalização.
5. **LODs** (`lods.py`) — a geometria final em **LOD 0 e LOD 1** (regra da
   hitbox: substituir só o LOD 0 deixa uma hitbox invisível desalinhada).
6. **Exportação** (`export.py`) — `.glb` via Cyberpunk Blender Add-on (ou glTF
   puro como fallback) para o WolvenKit importar sobre o `.mesh` base.

### Regra de ouro dos ossos

**Nunca alterar a posição de repouso dos ossos no `.rig`.** As matrizes
`boneRigMatrices` dentro do `.mesh` ficam dessincronizadas e a malha estica de
forma catastrófica. Toda a adaptação espacial é feita na malha (Edit Mode) ou
em keyframes. Se for absolutamente inevitável (ex.: *dangle bones*), é preciso
recalcular à mão as `boneRigMatrices` do osso no `.mesh`.

## 5. WolvenKit — injetar de volta

### Rota JSON↔CR2W (automática, descoberta e verificada)

O `wolvenkit-cli` faz **CR2W ⇄ JSON** nos dois sentidos (`convert serialize` /
`convert deserialize`), o que permite autorar os ficheiros do item **em código**:

| Ficheiro | Método | Estado |
| --- | --- | --- |
| `factory.csv` (entity factory) | JSON → `convert deserialize` | ✅ verificado (ida-e-volta) |
| `localization/*.json` | idem | ✅ método |
| `desert_eagle.app` | Nue `.app` → JSON → `scripts/build_app_json.py` → CR2W | ✅ **compilado** (5,7 KB) |
| `desert_eagle.ent` | Nue `.ent` → JSON → idem → CR2W | ✅ **compilado** (3,7 KB) |
| `.archive` | `wolvenkit-cli pack` sobre a pasta montada | pronto a correr |
| `.mesh` (geometria) | GLB → `.mesh` | ❌ requer GUI WolvenKit **ou** redMod |
| `.anims` | `.re` → `.anims` | ❌ requer GUI WolvenKit **ou** redMod |

O transformador `scripts/build_app_json.py` aplica as regras deste §5 sobre o
`.app`/`.ent` extraídos: mantém **1** aparência (`desert_eagle`, regra do
dry-run), tag `DesertEagleDefault`, `entSkinnedMeshComponent` do corpo apontado
para `desert_eagle\items\w_handgun_desert_eagle.mesh`, meshes de peças vanilla
removidas, `resolvedDependencies` limpo e `baseEntity` apontado para o nosso
`desert_eagle\items\desert_eagle.ent` (regra do Modo Fotografia).

**Armadilhas apanhadas:**
- `ResourcePath` **tem de ficar com `$storage: string`** — valores `uint64`
  (só hash) rebentam com `NotResolvableException` no `convert deserialize`.
- O `-o` do `convert` exige diretório **existente**.
- O `convert deserialize` só processa ficheiros `*.json` (o nome deve manter o
  sufixo original: `desert_eagle.app.json` → `desert_eagle.app`).
- O `baseEntity` da Nue vem **vazio** (`0`) — é o nosso `.app` que aponta para o
  `.ent` (o passo do Modo Fotografia).

### Formato das texturas (`.xbm`) — decodificado

As texturas seguem o mesmo padrão do mesh: metadados no CR2W + píxeis em
base64 (`textureData.Bytes`), com a cadeia de mips descrita por
`rendRenderTextureBlobHeader` (MemoryLayout `rowPitch/slicePitch` + Placement
`offset/size` por mip) e `rendRenderTextureBlobTextureInfo`/`SizeInfo`.

| Dado | Formato | Prova |
| --- | --- | --- |
| Compressão de píxeis | **BCn** (BC5 para normais, BC1/3 para albedo) | mip0 de 128×128: `rowPitch=512` = 128 texels × 16 B/bloco BC5; `slicePitch=16384` = 1 B/texel |
| Cadeia de mips | offsets contíguos (16384+4096+1024+256+…) = `textureDataSize` | bate certo |
| Metadados | `setup.compression` (`TCM_Normalmap`…), `group` (`TEXG_Generic_Normal`…), `rawFormat: TRF_TrueColor` | verificado |

O extrator `scripts/glb_textures.py` já tira as texturas PNG do modelo CS2
(3 mapas 4K: albedo/normal/roughness). **Trabalho seguinte**: codificador BCn
(BC1/BC3/BC5) + escritor `.xbm` (simétrico ao `mesh_write.py`) para colar as
texturas CS2 nos materiais do jogo — o último passo para a arma parecer uma
Desert Eagle a sério em vez de metal da Nue sobre as UVs do CS2.

### Formato do buffer de geometria (decodificado e verificado)

O `.mesh` guarda os vértices embutidos em base64 (`renderBuffer.Bytes`), com o
layout descrito por `quantizationOffset/Scale`, `vertexBufferSize`,
`indexBufferOffset/Size` e um `rendChunk` por submalha. O decodificador
`scripts/mesh_buffer.py` reconstrói a geometria (verificado: a Nue dá
0,041 × 0,245 × 0,157 m — pistola real — e todos os índices dentro do intervalo):

```text
renderBuffer.Bytes (base64)
├── região de vértices [0 .. vertexBufferSize)
│   por chunk, por stream (byteOffsets por stream):
│     stream 0 (16 B/vért): PS_Position PT_Short4N (xyzw int16)   ← posição
│                           PS_SkinIndices PT_UByte4              ← ossos
│                           PS_SkinWeights PT_UByte4N             ← pesos
│     stream 1  (4 B/vért): PS_TexCoord PT_Float16_2              ← UV0
│     stream 2  (8 B/vért): PS_Normal + PS_Tangent (PT_Dec4)      ← normais
│     stream 3  (8 B/vért): extra (cor/UV1)
└── região de índices [indexBufferOffset .. +indexBufferSize)
    uint16 por índice; cada chunk tem teOffset dentro desta região
    (3 chunks na Nue: 74892 + 5382 + 24 índices)

posição = (int16 / 32767) × quantizationScale + quantizationOffset   [metros]
```

**Consequência:** o passo GLB → `.mesh` é simétrico — escrever as streams com o
mesmo layout, os offsets dos chunks e os índices. É o trabalho seguinte (o
escritor de buffer), depois do qual **nenhum passo de GUI fica no caminho**.

### Escritor de buffer (feito) e a corrupção Oodle — RESOLVIDO

`scripts/mesh_write.py` é o inverso do decodificador: reescreve quantização,
streams, offsets e `renderBuffer.Bytes` a partir de um `geometry.json`
(`mesh_buffer.py --dump` produz esse formato). **Verificado ao nível JSON e ao
nível CR2W**: o roundtrip completo (write → `convert deserialize` →
`convert serialize` → decode) reproduz contagens (20.767/80.298), bboxes por
chunk e índices válidos — a geometria chega intacta ao `.mesh` compilado.

A corrupção do buffer (dados zerados após ~520.104 B) era do WolvenKit e está
**resolvida**: o CLI carrega o Oodle nativo **exclusivamente** de
`%LOCALAPPDATA%\oo2ext_7_win64.dll` (fonte: `WolvenKit.Core/Compression/Oodle.cs`
→ `Oodle.Load()` → `TryCopyOodleLib()`). Sem o ficheiro aí, cai em silêncio no
fallback `kraken.dll` — que perdia o fim do buffer na compressão.

**Correção (uma vez por máquina):**

```powershell
Copy-Item '<jogo>\bin\x64\oo2ext_7_win64.dll' "$env:LOCALAPPDATA\oo2ext_7_win64.dll"
```

Depois disso o ciclo `convert deserialize/serialize` é **sem perdas** (verificado
com o `.mesh` original da Nue e com o do nosso escritor). O mesmo fix desbloqueia
também a compressão Oodle do `pack` do `.archive`. Nota: o auto-copy do WolvenKit
(procura no `bin\x64` via registry) falha em silêncio em installs Steam — por
isso a cópia manual.

### Passos no WolvenKit GUI (quando autorizado)

1. Importar o `.glb` por cima do `.mesh` base (o `.mesh` é o contentor; o
   WolvenKit não cria `.mesh` do zero).
2. *Custompath* da entidade: copiar `mesh_entity.ent` para a pasta do projeto,
   renomear e apontar o `baseEntity` do `.app` para o `.ent` novo.
3. No `.app`, atualizar todos os `MeshComponents` com `depotPath` para os
   `.mesh` novos (e o `entAnimatedComponent` se houver `.anims` custom).
4. **Limpar `resolvedDependencies`** nas aparências modificadas: entradas com
   flags *Soft*/*Embedded* fazem o jogo carregar a arma original por cima.
5. Depois de tudo a funcionar, copiar a matriz `components` da aparência
   funcional do `.app` para dentro do `mesh_entity.ent` (senão a arma não
   aparece no Modo Fotografia).

## 6. TweakXL + ArchiveXL

`src/tweakxl/desert_eagle.yaml` (base: o `$base` está no `.app` da arma base):

```yaml
Items.DesertEagle:
  $base: Items.Preset_Nue_Default
  entityName: desert_eagle_factory
  visualTags: [DesertEagleDefault]
  displayName: mappin.desert_eagle_name
  quality: Quality.Legendary
  crosshair: Crosshairs.Tech_Round
  weaponAudio: wea_set_nue
  ikOffset: {x: 0, y: 0, z: 0}
```

`src/archivexl/` — `factory.csv` aponta para o `.app`, as variantes ligam-se por
`visualTags`, e a localização (en-us.json) entra via ArchiveXL.

**Dry run primeiro**: meter a `visualTag` só em **uma** aparência do `.app`,
manter as restantes intactas para comparação, empacotar, e testar com
`Game.AddToInventory("Items.DesertEagle", 1)`.

## 7. Calibração

- `CycleTimeBase` = razão entre o tempo do ciclo de recarga e o de disparo
  (valores menores → cadência maior); `ReloadTimeBase`/`EmptyReloadTime` para
  recargas; `RecoilKickMin/Max`, `RecoilTime`, `RecoilRecovery`, `RecoilDir`
  para a sensação de recuo.
- Fast refresh em desenvolvimento: jogo em Borderless + Red Hot Tools + Red CLI
  em modo `watch`; logs em `red4ext\plugins\ArchiveXL\ArchiveXL.log`,
  `red4ext\plugins\TweakXL\TweakXL.log`, `r6\logs\redscript_rCURRENT.log`.

## Matriz de diagnóstico

| Sintoma | Causa | Correção |
| --- | --- | --- |
| Visual da arma original | `resolvedDependencies` com flags Soft/Embedded | limpar o array no `.app` e reempacotar |
| Visível no inventário, invisível em FPP | `$base` incompatível ou componentes `.ent`/`.app` dessincronizados | testar `$base` alternativo ou copiar os componentes do `.ent` para o `.app` |
| Modelo padrão/invisível só no Modo Fotografia | `baseEntity` ainda aponta ao `.ent` original | custompath do `mesh_entity.ent` + sincronizar `components` |
| Peças flutuando/caídas | vértices sem pesos ou grupos sem osso correspondente | rigging: nomes exatos + peso 1.0 + normalizar |
| Retículo desalinhado do impacto | `ikOffset` herdado conflita com a geometria nova | `ikOffset: {x: 0, y: 0, z: 0}` no YAML |
| Hitbox invisível (melee) | substituído só o LOD 0 | geometria em LOD 0 **e** LOD 1 + `BaseStats.Range` |
| Não dispara projéteis/VFX | `entSlot`/`entEffectSpawnerComponent` alterados | repor os componentes no `.ent` |
