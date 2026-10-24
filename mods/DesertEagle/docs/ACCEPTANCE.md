# Aceitação em jogo — checklist da sessão de teste

Tudo o que é automatizável está construído e verificado por código. Este
checklist cobre o que só o jogo pode provar. **Nada é instalado sem autorização
explícita do dono** — o script de deploy recusa correr sem o flag
`-IAuthorizeTheGameInstall`.

## 1. Pré-requisitos (uma vez)

- Cyberpunk 2077 PC **2.5** (`3.0.88.x`)
- [redscript](https://github.com/jac3km4/redscript/releases) `>=0.5.32` na raiz do jogo
- [ArchiveXL](https://github.com/psiberx/cp2077-archive-xl) `>=1.18.0`
- [TweakXL](https://github.com/psiberx/cp2077-tweak-xl) `>=1.10.0`
- [Cyber Engine Tweaks](https://github.com/maximilionus/cyber-engine-tweaks) (atalho de spawn)

## 2. Deploy (autorizado pelo dono)

```powershell
pwsh -File mods/DesertEagle/scripts/deploy_release.ps1 -IAuthorizeTheGameInstall
```

Instala na raiz do jogo: `r6\scripts\DesertEagle\`, `r6\tweaks\desert_eagle.yaml`,
`archive\pc\mod\desert_eagle.archive` (+ `.xl`).

## 3. Sessão de teste

| # | Verificar | Comando / ação | Esperado |
|---|---|---|---|
| 1 | Spawn | CET: `Game.AddToInventory("Items.DesertEagle", 1)` | item "Desert Eagle" no inventário |
| 2 | Visual em 1.ª pessoa | equipar a arma | **Desert Eagle texturizada** (empunhadura em diamante, corrediça prateada) — NÃO o visual da Nue |
| 3 | Escala/empunhadura | olhar para baixo/lados | arma nas mãos sem atravessar, punho alinhado |
| 4 | Disparar | R2/click | recuo + fogacho; corrediça recua (animação CS2 `recoil_shoulder`) |
| 5 | Equipar (draw) | trocar de arma 2× | animação CS2 `first_equip` |
| 6 | Recarregar (vazio) | esvaziar carregador + recarregar | animação CS2 `empty_reload` — carregador desce/sobe |
| 7 | Modo Fotografia | abrir Photo Mode | arma visível e texturizada na mão |
| 8 | Estatísticas | disparar/observar | DPS ~380, carregador 7, recarregamento ~2,4 s (BaseStats .50 AE) |
| 9 | NPCs (opcional) | ver Nue de NPCs | Nue vanilla inalterada (o nosso mod é aditivo) |
| 10 | Remoção limpa | apagar `archive\pc\mod\desert_eagle.archive` + yaml | jogo volta ao normal, sem efeitos residuais |

## 4. Se algo falhar

Logs primeiro: `r6\logs\redscript_rCURRENT.log`,
`red4ext\plugins\ArchiveXL\ArchiveXL.log`, `red4ext\plugins\TweakXL\TweakXL.log`.

| Sintoma | Causa provável | Ação |
|---|---|---|
| Item não aparece no spawn | TweakXL não carregou o yaml / id divergente | ver log TweakXL; confirmar `Items.DesertEagle` |
| Arma com visual da Nue | refs vanilla no `.app` (ver matriz de diagnóstico em [PIPELINE.md](PIPELINE.md#matriz-de-diagnóstico)) | `verify_release.py` já assegura 0 refs — reportar se acontecer |
| Arma invisível | mesh falhou ao carregar (Oodle?) | confirmar `oo2ext_7_win64.dll` em `%LOCALAPPDATA%` (ver PIPELINE.md) |
| Animações vanilla (não CS2) | paths de anims não resolvem (hash) | verificar entradas `desert_eagle\animations\*.anims` no archive |
| Textura preta/errada | material/xmbs | verificar entradas `items\textures\*.xbm` no archive |
| Crash ao equipar | `.ent`/app inválido | log do jogo + reportar; o `verify_release.py` cobre a estrutura |

## 5. Notas

- O pacote é **aditivo**: não substitui ficheiros vanilla; a Nue original fica intacta.
- **Licença**: o modelo ativo é IP da Valve (CS2) — uso apenas em desenvolvimento,
  nunca distribuir publicamente (ver README §Licença). O fallback CC-BY 3.0 é
  `assets/raw/desert_eagle_poly.glb`.
- Ao terminar: registar o resultado na memória CoALA e atualizar o README §Estado.
