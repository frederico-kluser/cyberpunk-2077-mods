# Desert Eagle — pipeline de Blender

Automação completa do ativo 3D da Desert Eagle: importação, alinhamento sobre a
arma base (Tsunami Nue), rigging por nomes de ossos do `.rig`, LODs e exportação
`.glb` para o WolvenKit. Tudo corre também em `blender --background`, portanto é
testável e reproduzível sem GUI.

## Requisitos

- Blender 4.1+ (instalado em `C:\Users\kluse\Tools\Blender\5.2\` nesta máquina)
- Add-on **Cyberpunk Blender Add-on (WolvenKit IO Suite)** — usado na exportação
  final para o `.mesh`; sem ele o pipeline exporta glTF puro (também importável
  no WolvenKit)

## Como correr

```powershell
# pipeline completo, a partir de mods/DesertEagle/src/blender
& 'C:\Users\kluse\Tools\Blender\5.2\blender.exe' --background --python run_pipeline.py -- `
    --config configs/desert_eagle.json --stage all

# só algumas etapas
& 'C:\Users\kluse\Tools\Blender\5.2\blender.exe' --background --python run_pipeline.py -- `
    --config configs/desert_eagle.json --stage rig --stage export
```

Etapas, sempre nesta ordem: `import -> align -> rig -> lods -> export -> report`.
A saída imprime `STAGE <nome> OK` por etapa e termina com `PIPELINE_OK`
(ou `PIPELINE_FAIL` + exit code 1).

## Teste de ponta a ponta

```powershell
& 'C:\Users\kluse\Tools\Blender\5.2\blender.exe' --background --python tests/test_smoke.py
```

O teste constrói uma arma sintética (slide, carregador, gatilho) e um template,
corre o pipeline REAL por cima e verifica os contratos que a REDengine 4 exige:
escala uniforme + âncoras coincidentes, grupos de vértices com os nomes dos
ossos e peso 1.0, máximo 8 influências, LOD 0 e LOD 1 ambos povoados (regra da
hitbox) e `.glb` + relatório JSON escritos. Termina com `SMOKE_TEST_OK`.

## Regras da REDengine 4 implementadas aqui

| Regra | Onde |
| --- | --- |
| Grupos de vértices com o nome EXATO do osso do `.rig` | `de_pipeline/rigging.py` |
| Peso 1.0 em peças mecânicas (Slide, Magazine, Trigger) | `de_pipeline/rigging.py` |
| Máximo de 8 influências por vértice + normalização | `limit_influences` / `normalize_weights` |
| Grupos herdados sem osso correspondente são apagados | `drop_unknown_groups` |
| Geometria em LOD 0 **e** LOD 1 (hitboxes) | `de_pipeline/lods.py` |
| Escala uniforme (nunca esticar por eixo) | `de_pipeline/align.py` |
| NUNCA mexer na posição de repouso dos ossos do `.rig` | política do projeto — mexe-se só em keyframes/malha |

## Configuração

`configs/desert_eagle.json` — ver os comentários em `de_pipeline/config.py`.
Pontos que dependem de dados extraídos do jogo (`bones`, tokens de objetos)
são preenchidos na etapa de extração (ver `../../docs/PIPELINE.md`).
