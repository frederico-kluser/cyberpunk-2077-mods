# Lições aprendidas — diário de engenharia do LethalHeadshots

Tudo o que esta equipa aprendeu a arrancar de tentativas reais (PRs #11, #14,
#15, #19), do dossiê de pesquisa profunda
[`docs/research/dossie-hud-inktext.md`](../../../docs/research/dossie-hud-inktext.md)
e do código descompilado do jogo 2.5. Cada entrada diz **o que falhou, porquê,
e o que usar no lugar**. Quando algo aqui mudar de estado, atualizar a entrada.

> Estado atual: o rótulo «QUE OTA» **ainda não foi confirmado em jogo**. Os
> quatro canais diagnósticos estão instalados; falta a leitura do teste (ver
> §5) para fechar a causa por eliminação.

---

## 1. O que está DERRUBADO — nunca voltar a fazer

| Tentativa | Porquê que falhou | Evidência |
| --- | --- | --- |
| Sinal do rótulo via `gameHitEvent.projectionPipeline` | O pipeline de projeção **nunca dispara de forma fiel** enquanto se mira; o jogo só o corre em transições de alvo/partes (`CheckProjectionPipelineTargetConditions`) e depende de internals do aim-assist. Foi a razão de as versões v1–v2 do rótulo nunca aparecerem. | dossiê Q4–Q5; código descompilado `damageSystem.script` |
| Capturar o root da HUD **uma vez** em `OnInitialize` via `GetPlayer()` e guardar no `PlayerPuppet` | O HUD inicializa **antes de o jogador existir** e é recriado em ecrãs de carregamento (com um `PlayerPuppet` novo) — a captura falha em silêncio e o widget nunca é criado. | PR #14 (correção), leitura do `crosshairContainerController.script` |
| Tratar o **TweakDB** como inventário de fontes | `tweakdb.bin` só lista caminhos usados por *records* de gameplay (`arame`, `blender`); **não** é o inventário de recursos. O `orbitron.inkfontfamily` existe nos archives. Conclusão falsa quase guiou a correção errada. | dossiê Q2 (NativeDB + inventário de ficheiros do jogo) |
| «Os setters têm de vir todos antes do `Reparent`, que tem de ser a última chamada» | **Refutado** pela verificação adversarial: a própria UI Basics Part 4 faz `SetText` **depois** do `Reparent`, e setters funcionam após *attach*. Não é requisito. | dossiê A10 (verificação 1-2) |
| Confiar no lint contra o `final.redscripts` **instalado** | Esse bundle já contém o build anterior do mod → falsos erros «field/type/method already defined». Validar sempre contra o bundle **pristine** (`final.redscripts.bk`). | PR #19 (`tools/validate.ps1` corrigido) |

## 2. Armadilhas REAIS de um `inkText` que não desenha

Se o texto não aparece mas a lógica corre, percorrer esta lista por ordem:

1. **Área de desenho zero** — sem `SetFitToContent(true)` (ou `SetSize`
   explícito) o widget pode não ter tamanho útil. Setup documentado que
   funciona: `SetMargin(0,0,0,0)` + `SetWrapping(true, 700.0)` +
   `SetFitToContent(true)` **antes** do `Reparent` (wiki «Custom Popups»).
2. **`opacity` a 0** — `SetVisible(true)` **não** repõe opacidade (0 =
   transparente, 1 = opaco); animações `inkAnimTransparency` do controlador
   podem deixar o pai a 0 (o root do crosshair tem fades de interação/estado).
3. **Redraw não forçado** — `SetFontStyle` **não redesenha** sozinho; é preciso
   `SetText`/`SetFontSize` depois (NativeDB `inkTextWidget`; a nota aplica-se a
   **estilo**, não a `SetFontFamily`).
4. **Geometria/âncora** — `anchor` (onde no pai) + `anchorPoint` (ponto do
   widget) + `margin` mal combinados empurram o texto para fora dos limites do
   pai; offsets grandes (ex. -240 px) correm mais risco de sair de um contentor
   pequeno. Manter perto do centro.
5. **Pai controlado pelo jogo** — a UI está «sempre carregada, apenas inativa»;
   o jogo força visibilidade/opacidade por cima (fade, `SetVisible` em estados
   de cena, visão/scanner). Um filho do root da mira herda tudo isso.
6. **Clipping do pai** — filhos fora dos limites do contentor podem ser
   cortados (sem API de `SetUseClipping` em redscript puro).
7. **Família de fonte errada** → **zero glifos**: o texto fica **totalmente
   invisível, sem erro nem fallback** (caso observado: mod Trauma Team, com
   `blender` → invisível; com `raj` → visível).

## 3. Padrões que FUNCIONAM (documentados e/ou verificados)

- **Receita de HUD em redscript puro**: enganchar o ciclo de vida
  (`OnInitialize`/`OnPlayerAttach`) do controlador dono da área → obter o pai
  **dentro do callback** com `this.GetRootCompoundWidget()` → `new inkText()` +
  setters → `Reparent`. Exemplo oficial: `MinimapContainerController` +
  `OnPlayerAttach` (wiki UI Basics Part 4).
- **Fontes reais do jogo** (inventário de ficheiros, 18 caminhos):
  `base\gameplay\gui\fonts\{arame,arial,blender,digital_readout,industry,orbitron,raj}\…`
  + `foreign\…` + `engine\ink\fonts\arial.inkfontfamily`. Padrão documentado de
  HUD: **`raj` + `n"Medium"`** (raj é a fonte dominante do jogo).
- **Ticker periódico**: `DelayCallback` dispara **Uma única vez**; re-agendar
  dentro de `Call()`, guardar o `DelayID` e fazer `CancelCallback` antes
  (padrão do mod público Addicted). `inkGameController` **não** tem `OnUpdate`.
- **Mensagem HUD sem frameworks**: `SimpleScreenMessage` no blackboard
  `UI_Notifications.WarningMessage` — o mesmo que `player.SetWarningMessage`
  usa no código nativo; renderiza pelo `WarningMessageGameController` vanilla.
- **Verdade de terreno**: `redscript-cli decompile -i <jogo>\r6\cache\final.redscripts -o .cache/decompiled -f -m code`
  → fontes nativas reais; o bundle instalado já inclui os mods (os `@wrapMethod`
  aparecem como `wrapper$NNNNN`). O lint do `redscript-cli` é **estrito**
  (rejeita métodos inexistentes — provado com sonda de API falsa).
- **Type-check honesto**: `tools/validate.ps1` usa o `final.redscripts.bk`
  (pristine) — o cache modded dá falsos conflitos com o próprio mod.

## 4. O que NÃO usar nesta instalação

- **`GameInstance.GetInkSystem()` / `inkHUDLayer` virtual window**: exige
  **Codeware**; não é vanilla. O padrão «canónico» da Codeware está fora.
- **RED4ext + ArchiveXL + TweakXL**: desativados — a atualização 2.5
  «Edgerunners II» (exe `3.0.88.46235`) quebra **todos** os plugins RED4ext
  (crash 0xc0000005 ao carregar; bug upstream
  [wopss/RED4ext#153](https://github.com/wopss/RED4ext/issues/153)). Reinstalar
  só quando houver RED4ext corrigido.
- **CET/Lua**: indisponível; overlays ImGui de mods de mira (ex. Crosshair
  Ready) são outra via, não comparável.
- **`textWrappingInfo`/`SetWrappingInfo`**: não utilizáveis em redscript puro
  (jac3km4/redscript#70) — usar `SetWrapping(true, largura)`.

## 5. Diagnóstico do rótulo — os quatro canais (PR #19)

Com `DebugProbes = true` (predefinição), ao mirar uma cabeça devem aparecer os
quatro. A leitura fecha a causa **por eliminação**:

| O que vês | Causa | Ação |
| --- | --- | --- |
| Nada, nem com inimigo sob a mira | ticker não corre / `GetLookAtObject` devolve nulo | camada de ticker/targeting |
| Mira fica **laranja**, nunca vermelha | ticker ok; teste da cabeça falha | slot `Head` / limiar de distância |
| Tudo aparece (tint + barras + texto + mensagem) | **resolvido** | pôr `DebugProbes = false` |
| Tint + barras + mensagem, **sem texto** | widgets renderizam mas o `inkText` sem glifos | fonte (`raj`+`Medium`) / redraw |
| Tint + mensagem, **sem barras nem texto** | widgets custom não desenham sob o root da mira (pai/clip) | mudar de pai (§3 receita) ou aceitar a mensagem vanilla |
| Nenhuma das barras/tint, mas a **mensagem HUD aparece** | lógica ok; widgets do crosshair mortos | mudar de pai |

## 6. Referências

- Dossiê de pesquisa profunda (27 fontes, verificação adversarial, lint 0 erros):
  [`docs/research/dossie-hud-inktext.md`](../../../docs/research/dossie-hud-inktext.md)
- Arquitetura do kill + do rótulo: [`docs/ARCHITECTURE.md`](../../../docs/ARCHITECTURE.md)
- Matriz de testes: [`docs/TESTING.md`](../../../docs/TESTING.md)
- Bug upstream do RED4ext na 2.5: <https://github.com/wopss/RED4ext/issues/153>
- Wiki REDmodding (UI Basics 1–4, InkWidgets, NativeDB, DelaySystem) e wiki da
  Codeware: ver secção Fontes do dossiê para os URLs exatos.
