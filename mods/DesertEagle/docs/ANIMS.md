# Calibração de animações — CS2 → Cyberpunk 2077 (Tsunami Nue)

O modelo CS2 traz 50 animações primeiro-pessoa prontas; o jogo espera um
conjunto FIXO de animações internas nos `.anims` da Nue, com durações
exatas. **Calibrar** = reaproveitar o movimento CS2 dentro dos nomes, contagens
de frames e durações que a REDengine 4 já conhece.

## Alvos reais (extraídos dos `.anims` da Nue via `wolvenkit-cli convert serialize`)

`w_handgun__tsunami_nue__base1.anims` (11 ossos):

| Animação interna | Duração | Frames | Papel |
| --- | --- | --- | --- |
| `weapon_empty` | 0,033 s | 2 | stub de repouso |
| `first_equip` | 2,967 s | 90 | empunhar/desenhar |
| `empty_reload` | 3,333 s | 101 | recarga com arma vazia |
| `empty_reload_01` | 3,333 s | 101 | variante |
| `empty_reload_02` | 3,333 s | 101 | variante |
| `recoil_shoulder` | 0,333 s | 11 | recuo de disparo |

`w_handgun__tsunami_nue__mag_std.anims` (carregador):

| Animação interna | Duração | Frames | Papel |
| --- | --- | --- | --- |
| `first_equip` | 3,567 s | 108 | empunhar (com carregador) |
| `reload` / `reload_01` / `reload_02` | 2,667 s | 81 | recarga tática |
| `empty_reload` / `_01` / `_02` | 3,333 s | 101 | recarga a partir de vazio |

## Fontes CS2 (ações do `desert_eagle_cs2.glb`)

| Ação CS2 | Frames | Movimento |
| --- | --- | --- |
| `firstperson_shoot1` (+`_additive`, shoot2/3) | 0–16 | gatilho → martelo → corrediça recua → recuo |
| `firstperson_reload` | 0–52 | inclinação → carregador sai/entra → corrediça |
| `firstperson_draw` | 0–24 | empunhar |
| `firstperson_idle` | 0 | repouso |
| `sh_pstl_firing` | 0–9 | disparo curto (variante) |
| `sh_pstl_stand_reload` | 0–61 | recarga longa (variante) |

## Mapa de calibração (decisão)

| Alvo Nue | Fonte CS2 | Regra de re-timing |
| --- | --- | --- |
| `recoil_shoulder` (11 f) | `firstperson_shoot1` (17 f) | comprimir para 11 frames — o recuo tem de caber no `RecoilTime` do TweakXL |
| `first_equip` (90 f) | `firstperson_draw` (25 f) | esticar para 90 frames (movimento suavizado, sem alterar a trajetória) |
| `empty_reload`/`_01`/`_02` (101 f) | `firstperson_reload` (53 f) | esticar para 101 frames; as 3 variantes podem receber sub-variações (shoot2/3 ou offsets de 2–3 frames) |
| `reload`/`_01`/`_02` (81 f, mag) | `firstperson_reload` (53 f) | esticar para 81 frames (recarga tática = mais curta) |
| `weapon_empty` (2 f) | `firstperson_idle` | copiar pose |
| `mag_std` (carregador) | `v_weapon_deagle_clip_2` do `firstperson_reload` | extrair só a curva do clip e aplicar no `.anims` do mag |

### Regras de ouro

1. **Nomes mandam:** o `.re` exportado tem de se chamar EXATAMENTE como a
   animação interna (`recoil_shoulder.re`, `empty_reload.re`, …) — o compilador
   grava sempre com o nome do ficheiro.
2. **Durações mandam:** o jogo sincroniza `ReloadTimeBase`, `CycleTimeBase` e
   `RecoilTime` com estas durações; re-time por interpolação (mesma trajetória,
   novo eixo temporal), nunca cortando curvas.
3. **Repor o resto:** as curvas dos ossos que a animação CS2 não mexe ficam na
   pose de repouso — **nunca** alterar a posição de repouso no `.rig`
   (`boneRigMatrices` ficam dessincronizadas).
4. **Movimento da raiz:** exportar com *Include Root Motion*; o recuo lateral da
   arma CS2 (`weapon_hand_r_4` → `barrel`) vira movimento dos ossos, não da raiz
   da entidade.
5. **30 fps dos dois lados** — CS2 e Nue usam 30 fps; o re-time é só reamostragem
   de keyframes.

## Pipeline de exportação (tudo na worktree)

```text
desert_eagle_cs2.glb (ações CS2)
  → retarget (ossos renomeados: slide/weapon_trigger/mag_slot/hammer/barrel)
  → re-time para os frames/duração de cada alvo
  → REDmod Blender plugin: export .re por animação (nome = alvo)
  → wolvenkit-cli import: injetar .re nos .anims extraídos (worktree)
  → .anims resultantes entram no .archive (sem tocar no jogo)
```

O `redMod.exe` não existe nesta instalação do jogo e nada é deployado ao jogo
(restricao do dono) — a injeção nos `.anims` faz-se pelo WolvenKit CLI sobre as
cópias extraídas em `assets/extracted/`, e o resultado fica em `assets/work/`.

## Estado

| Passo | Estado |
| --- | --- |
| Nomes/durações reais extraídos (2 conjuntos, 13 animações) | feito |
| Mapa de calibração decidido | feito (tabela acima) |
| Re-time + export `.re` | próximo passo |
| Injeção nos `.anims` + validação | pendente |
