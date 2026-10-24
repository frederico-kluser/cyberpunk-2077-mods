# ArchiveXL — estrutura do mod

O ArchiveXL não altera ficheiros do jogo: funde os recursos do `.archive` do mod
com os originais em tempo de execução. Os ficheiros aqui são os *source* que vão
para dentro do `desert_eagle.archive` (montado no WolvenKit).

```text
desert_eagle.archive
├── desert_eagle\factories\weapons.csv        <- este diretório (entity factory)
├── desert_eagle\localization\en-us.json      <- este diretório (traduções)
├── desert_eagle\localization\pt-br.json
├── desert_eagle\items\desert_eagle.app       <- gerado pelo WolvenKit (fase 5 do pipeline)
└── desert_eagle\items\mesh_entity.ent        <- gerado pelo WolvenKit (custompath)
desert_eagle.archive.xl                       <- loader config (fica ao lado do .archive)
```

## Como os ficheiros se ligam

| Ficheiro | Papel |
| --- | --- |
| `desert_eagle.archive.xl` | diz ao ArchiveXL que `factories/weapons.csv` e as localizações entram na fusão |
| `factories/weapons.csv` | entity factory: `desert_eagle_factory` → `desert_eagle\items\desert_eagle.app`. Para **armas**, o factory aponta direto para o `.app` (não para um `root_entity.ent`) |
| `localization/*.json` | `secondaryKey` usados pelo `displayName`/`localizedDescription` do TweakXL |
| `../tweakxl/desert_eagle.yaml` | o registo `Items.DesertEagle` (TweakXL): `$base`, `entityName`, `appearanceName`, stats |

O `entityName` do YAML (`desert_eagle_factory`) tem de coincidir com a primeira
coluna do `weapons.csv`; o `appearanceName` (`desert_eagle`) com o nome da
aparência definida no `.app` (conta até ao primeiro sufixo).

## Montagem do .archive

Com o WolvenKit: projeto com os ficheiros extraídos/editados → *Pack project*
(ou `wolvenkit.cli pack`) → copiar `desert_eagle.archive` + `desert_eagle.archive.xl`
para `archive\pc\mod\` na raiz do jogo. O passo a passo detalhado está em
[`../../docs/PIPELINE.md`](../../docs/PIPELINE.md) §5.

## Variantes de cor

Definem-se por `visualTags` no `.app` (uma por variante) e repetem-se entradas no
YAML do TweakXL (`Items.DesertEagle_Black`, …) mudando `appearanceName`. O
dry-run inicial usa **uma única** aparência, para isolar problemas (ver PIPELINE.md §6).
