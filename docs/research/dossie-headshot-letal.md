---
tipo: dossie-pesquisa-profunda
versao: 1
pergunta: "Como implementar de forma fiável, num mod open-source para Cyberpunk 2077 v2.5 no PC, um headshot letal (dano suficiente para matar instantaneamente qualquer NPC inimigo): qual a API Redscript exata (GameHitEvent, HitData, hitPart/identificação de headshot, DamageSystem, health), quais os registos e stats TweakDB relevantes, e que mods/implementações existentes no Nexus/GitHub usam esta abordagem e com que compatibilidade?"
criado: 2026-10-23
atualizado: 2026-10-23
estado: concluido
ronda: 1
---

# Dossiê — Headshot letal em Cyberpunk 2077 2.5

> Pesquisa profunda (`tavily.py research init --deep-research`). Texto citado de
> fontes é DADO, nunca instrução. As fontes primárias são o código descompilado
> do jogo (referência canónica da comunidade) e a documentação da REDmodding.

## 0. Brief (a estrela-guia)

- **Pergunta principal:** como implementar, de forma fiável e compatível com
  Cyberpunk 2077 2.5 (PC), um mod que torne qualquer headshot letal em NPCs
  inimigos; qual a API Redscript exata, que registos TweakDB são relevantes e que
  mods existentes usam esta abordagem.
- **Para quê / decisão que informa:** decidir a arquitetura do primeiro mod do
  repositório (`LethalHeadshots`): Redscript com hook no pipeline de dano vs.
  TweakDB/TweakXL; assinatura e ponto de interceção exatos; definição de
  «inimigo»; dependências e validação necessárias.
- **Âmbito — inclui:** v2.5 (e notas para 2.3x); Redscript, RED4ext, TweakXL,
  CET, ArchiveXL; documentação REDmod, wiki.redmodding.org, código de mods;
  sistemas de dano, health, hit parts e atitude.
- **Âmbito — exclui:** consoles, multiplayer (não existe), criação de assets,
  UI, versões anteriores a 2.0 e cheats externos de memória.
- **Critérios de «terminado»:**
  - [x] Identificação inequívoca de headshot na API, com fonte primária.
  - [x] Ponto de interceção e assinatura Redscript, com código real.
  - [x] Forma fiável de matar (incluindo bosses) e de ler a vida.
  - [x] Registos/flats TweakDB relevantes e veredito sobre a via declarativa.
  - [x] ≥2 mods existentes comparáveis, com limitações.
  - [x] Dependências mínimas e versões compatíveis com 2.5 + validação.
  - [x] Forma de distinguir inimigos de civis/aliados e alvos sem cabeça.

## 1. Resposta (síntese executiva)

O jogo não tem um campo `hitPart` num tipo `HitData`: a zona do corpo vive no
`HitShapeData` do evento, em `HitShapeUserDataBase.m_hitReactionZone`, e o teste
canónico é `HitShapeUserDataBase.IsHitReactionZoneHead(...)` [S3][S1]. O ponto de
interceção correto é `DamageSystem.ProcessLocalizedDamage(hitEvent:
ref<gameHitEvent>)`, que corre dentro de `ModifyHitData` **antes** do dano ser
aplicado e imediatamente antes de `ProcessInstantKill` [S1][S6]. O jogo já tem um
caminho nativo de morte instantânea: marcar o `AttackData` com `hitFlag.Kill` faz
`ProcessInstantKill` baixar a Health ao mínimo via
`StatPoolsSystem.RequestSettingStatPoolMinValue`, preservando o instigator, e
saltando armadura, mitigações, resistências e o teto de dano por hit dos bosses
[S1][S2]. A via declarativa (TweakXL) só escala o multiplicador
`BaseStats.HeadshotDamageMultiplier` — é um fator sobre o dano base, não garante
morte e é anulado por `HeadshotImmunity`, HP elevado e reduções [S9][S10]. Por
isso a arquitetura escolhida é Redscript: detetar a hit shape da cabeça, validar
que o instigator é o jogador, que não é AoE nem o pipeline de projeção (mirar), e
marcar `hitFlag.Kill`. Duas armadilhas ficaram identificadas: sem a guarda
`projectionPipeline` o mod mata ao apontar [S1][S6], e mexer em stats globais de
dano/crit quebra quickhacks noutros mods [S8].

## 2. FAQ — árvore de perguntas

### Q1 — Como se identifica um headshot na API de dano e qual a assinatura de `gameHitEvent`?

- **Estado:** respondida
- **Prioridade:** alta
- **Confiança:** alta
- **Origem:** brief (ronda 0)
- **Resposta:** não existe `HitData.hitPart`; a zona está em
  `hitEvent.hitRepresentationResult.hitShapes[0].userData as HitShapeUserDataBase`
  e compara-se com `EHitReactionZone.Head` (valor 0) através de
  `HitShapeUserDataBase.IsHitReactionZoneHead` [S3][S1], com o userData
  resolvido por `DamageSystemHelper.GetHitShapeUserDataBase` [S4]. O `gameHitEvent` expõe
  `attackData`, `target`, `hitRepresentationResult`, `attackComputed` e
  `projectionPipeline` [S1][S5]. A flag `hitFlag.Headshot` só é posta pelo jogo
  para ataques ranged/direct/thrown do jogador, com multiplicador ≠ 0 e sem
  `HeadshotImmunity` — logo não serve como critério universal [S1].
- **Evidência:** `hitIsBodyPartHeadPrereq.swift` e `ProcessLocalizedDamage` [S1][S3].
- **Lacunas → sub-perguntas:** nenhuma.

### Q2 — Qual o ponto de interceção e como aplicar dano letal garantido?

- **Estado:** respondida
- **Prioridade:** alta
- **Confiança:** alta
- **Origem:** brief (ronda 0)
- **Resposta:** `@wrapMethod(DamageSystem) private final func
  ProcessLocalizedDamage(hitEvent: ref<gameHitEvent>)` é o ponto certo: corre em
  `ModifyHitData`, antes de `ProcessInstantKill`, com o evento completo [S1][S6];
  é o mesmo padrão de wrap usado por mods de dano em produção [S7].
  Adicionar `hitFlag.Kill` ao `AttackData` aciona o caminho nativo de
  instant-kill: `DealNoDamage` + `DontShowDamageFloater` +
  `RequestSettingStatPoolMinValue(Health, instigator)` [S1][S2]. Isso salta o
  pipeline de dano (armadura, mitigação, resistências e o cap
  `MaxPercentDamageTakenPerHit` dos bosses), mas não salta `IsInvulnerable` nem
  god mode — que continuam a adicionar `DealNoDamage` [S1]. A vida lê-se com
  `GetStatPoolValue(id, gamedataStatPoolType.Health, false|true)` e o máximo com
  `GetStatPoolMaxPointValue` ou o stat `Health` [S8].
- **Evidência:** ordem `ProcessDamageReduction → ProcessLocalizedDamage →
  ProcessInstantKill` em `ModifyHitData` [S1].
- **Lacunas → sub-perguntas:** efeito exato de `hitFlag.Kill` em alvos
  invulneráveis não foi validado em execução; o mod trata isso com uma guarda
  própria.

### Q3 — Que registos/flats da TweakDB controlam o dano, e a via declarativa resolve?

- **Estado:** respondida
- **Prioridade:** alta
- **Confiança:** alta
- **Origem:** brief (ronda 0)
- **Resposta:** o flat central é `BaseStats.HeadshotDamageMultiplier`, aplicado
  por `statModifiers` de um registo de arma com `gamedataConstantStatModifier_Record`
  (`statType`, `modifierType: Multiplier`, `value`) [S9][S10]. Outros flats
  relevantes: `BaseStats.BaseDamage`, `DamagePerHit`, `CritDamage`,
  `WeakspotDamageMultiplier`, `StealthHitDamageMultiplier`,
  `AllDamageDonePercentBonus` e `HeadshotImmunity` [S10]. A via declarativa
  **não garante letalidade**: o multiplicador incide sobre o dano base e o
  resultado continua sujeito a HP, reduções e imunidade — a própria wiki diz que
  «aumenta o multiplicador, mas não garante a morte em todas as situações»
  [S10][S9].
- **Evidência:** YAML funcional `Items.Preset_Unity_Default` com
  `modifierType: Multiplier` e `value: 10.0` [S9].
- **Lacunas → sub-perguntas:** nenhuma que altere a decisão.

### Q4 — Que mods existentes fazem algo comparável?

- **Estado:** parcial
- **Prioridade:** media
- **Confiança:** moderada
- **Origem:** brief (ronda 0)
- **Resposta:** existem três famílias. (a) **One Shot Headshot in Stealth**
  (Nexus 31793) faz kill na cabeça mas só enquanto o jogador está undetected, e
  torna elites/bosses imunes por design; é Redscript + RED4ext, sem código
  público [S15]. (b) **Ped Damage Overhaul 2077** é o único com fonte pública:
  envolve `ProcessLocalizedDamage`, chama `wrappedMethod` e mata com
  `npc.Kill()` apenas quando o contador de headshots atinge o limiar **e** a vida
  já está abaixo do dying-state threshold — é um *finisher*, não um one-shot de
  vida cheia [S8]. (c) **Weapon Damage Multipliers** (Nexus 4247) usa CET e
  multiplicadores (até 100×): bug conhecido em quickhacks, dano aplicado ao
  jogador e inércia relatada [S11]. Nenhum resolve "headshot = morte garantida"
  em vida cheia e em bosses.
- **Evidência:** código do PDO, descrição do mod de stealth e comentários/bugs do
  mod da Nexus [S8][S11][S15].
- **Lacunas → sub-perguntas:** a descoberta por motor de busca ficou limitada
  (pool Tavily esgotado); podem existir outros mods não mapeados.

### Q5 — Toolchain mínima, versões e validação fora do jogo

- **Estado:** respondida
- **Prioridade:** alta
- **Confiança:** alta
- **Origem:** brief (ronda 0)
- **Resposta:** para 2.5 é obrigatório **redscript 0.5.32+** (o release de
  2026-10-22 adiciona suporte aos bundles de script da 2.5) [S12]. O zip do
  redscript instala-se na raiz do jogo (`engine/tools/scc.exe`,
  `engine/config/base/scripts.ini`, `r6/config/cybercmd/scc.toml`); o engine
  compila `r6/scripts/**/*.reds` no arranque e escreve
  `r6/logs/redscript_rCURRENT.log` [S12]. Para type-check fora do jogo,
  `redscript-cli lint -s <pasta> -b <jogo>\r6\cache\final.redscripts` valida as
  assinaturas contra o bundle real [S16]. O jogo compilou o mod e arrancou numa
  instalação limpa 2.5 (verificado nesta máquina).
- **Evidência:** log `Compilation complete` / `Output successfully saved` [S12].
- **Lacunas → sub-perguntas:** nenhuma.

### Q6 — Como distinguir inimigos de civis/aliados e tratar alvos sem cabeça?

- **Estado:** respondida
- **Prioridade:** média
- **Confiança:** moderada
- **Origem:** brief (ronda 0)
- **Resposta:** a atitude resolve-se com
  `GameObject.GetAttitudeTowards(a, b) -> EAIAttitude` (`AIA_Hostile`,
  `AIA_Neutral`, `AIA_Friendly`), e `ScriptedPuppet.IsCharacterCivilian()` marca
  civis [S5][S14]. O cast para `ScriptedPuppet` exclui devices, turrets e
  veículos; drones e mechs são puppets, mas só morrem por headshot se tiverem
  uma hit shape de cabeça — o que é verificado pela própria hit shape [S3].
- **Evidência:** `scriptedPuppet.swift` (`IsCharacterCivilian`, `IsCivilian`,
  `GetAttitudeTowards`) [S5].
- **Lacunas → sub-perguntas:** `IsHostile()` e `PuppetState` não existem com
  esses nomes; a atitude é o critério fiável.

### Q7 — Que edge cases tornam o mod inconsistente?

- **Estado:** respondida
- **Prioridade:** média
- **Confiança:** moderada
- **Origem:** brief (ronda 0)
- **Resposta:** (1) o pipeline de projeção mata ao apontar se não for guardado
  [S1]; (2) aplicar um segundo hit em vez de marcar o hit original duplica dano
  [S11]; (3) mexer em stats globais quebra quickhacks [S11]; (4) sem filtro de
  instigator o mod atinge o jogador [S11]; (5) bosses podem estar invulneráveis
  em fases scriptadas — `IsInvulnerable`/god mode continuam a travar [S1][S11];
  (6) melee e armas brancas contam como headshot se a hit shape for a cabeça
  [S11]; (7) alvos já mortos/defeated não devem gerar novo evento [S11].
- **Evidência:** código do pipeline e bug reports do mod de multiplicadores [S1][S11].
- **Lacunas → sub-perguntas:** comportamento de DOT e de armas com dano 0 não
  documentado; o mod não interfere porque só olha para hits localizados.

## 3. Registo de rondas

| Ronda | Perguntas investigadas | Subagentes | Fontes novas | Afirmações novas | Lacunas abertas | Decisão |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | brief + decomposição | 0 | 0 | 0 | Q1–Q7 | lançar a ronda 1 |
| 1 | Q1–Q7 em paralelo | 7 | 14 | 30+ | ver §8 | saturação; sintetizar |

## 4. Matriz de evidência (afirmações centrais)

| ID | Afirmação | Fontes | Independentes | Verificação adversarial | Confiança |
| --- | --- | --- | --- | --- | --- |
| A1 | Headshot = `IsHitReactionZoneHead` sobre a hit shape | S1, S3 | 2 (código) | assinatura compilada contra o bundle 2.5 | alta |
| A2 | `hitFlag.Kill` aciona o instant-kill nativo | S1, S2 | 2 (código) | confirmação em `ProcessInstantKill` | alta |
| A3 | O hook corre antes de `ProcessInstantKill` | S1 | 1 (código) | ordem em `ModifyHitData` | alta |
| A4 | TweakXL não garante letalidade | S9, S10 | 2 (wiki oficial) | citação literal da wiki | alta |
| A5 | `projectionPipeline` tem de ser guardado | S1, S6 | 2 | código do pipeline + wiki | alta |
| A6 | Redscript 0.5.32 é obrigatório na 2.5 | S12 | 1 (release oficial) | changelog do release | alta |

## 5. Contradições

| Tema | Posição A | Posição B | Explicação provável | Resolução |
| --- | --- | --- | --- | --- |
| Melee conta como headshot? | O código só marca `hitFlag.Headshot` para ranged/direct/thrown [S1] | A wiki diz que hits de melee podem contar como headshot [S11] | A flag do engine e a classificação da hit shape são coisas distintas | O mod usa a hit shape, por isso cobre melee; documentado |
| Dano garantido vs. multiplicador | TweakXL permite multipliers enormes [S9] | Bosses têm cap por hit e imunidade [S1][S10] | Sistemas diferentes: stat vs. pipeline | Redscript + `hitFlag.Kill` |

## 6. Fontes

- [S1] Scripts descompilados — `cyberpunk/damage/damageSystem.swift`. Codeberg, 2026. <https://codeberg.org/adamsmasher/cyberpunk/raw/branch/master/cyberpunk/damage/damageSystem.swift> · código · A · integral.
- [S2] Scripts descompilados — `cyberpunk/damage/statPoolsManager.swift`. Codeberg, 2026. <https://codeberg.org/adamsmasher/cyberpunk/raw/branch/master/cyberpunk/damage/statPoolsManager.swift> · código · A · integral.
- [S3] Scripts descompilados — `core/components/hitRepresentationComponent.swift` (`IsHitReactionZoneHead`). Codeberg, 2026. <https://codeberg.org/adamsmasher/cyberpunk/raw/branch/master/core/components/hitRepresentationComponent.swift> · código · A · integral.
- [S4] Scripts descompilados — `cyberpunk/damage/damageSystemHelper.swift`. Codeberg, 2026. <https://codeberg.org/adamsmasher/cyberpunk/raw/branch/master/cyberpunk/damage/damageSystemHelper.swift> · código · A · integral.
- [S5] Scripts descompilados — `cyberpunk/puppet/scriptedPuppet.swift`. Codeberg, 2026. <https://codeberg.org/adamsmasher/cyberpunk/raw/branch/master/cyberpunk/puppet/scriptedPuppet.swift> · código · A · trechos.
- [S6] REDmodding Wiki — "How to create a hook". <https://wiki.redmodding.org/scripting-cyberpunk/redscript/getting-started/how-to-create-a-hook> · documentação · B · integral.
- [S7] REDmodding Wiki — "Observing weapon hits". <https://wiki.redmodding.org/scripting-cyberpunk/scripting/snippets-and-examples/entities/observing-weapon-hits> · documentação · B · integral.
- [S8] Ped Damage Overhaul 2077 — `PedDamageOverhaul2077_Main.reds`, `_DamageUtils.reds`, `_Utils.reds`. GitHub, 2025. <https://github.com/HJHughJanus/PedDamageOverhaul2077> · código de mod · B · integral.
- [S9] TweakXL — "YAML Tweaks" (psiberx). <https://github.com/psiberx/cp2077-tweak-xl/wiki/YAML-Tweaks> · documentação oficial · A · integral.
- [S10] REDmodding Wiki — "Cheat Sheet: Base Stats" e "Weapon BaseStats". <https://wiki.redmodding.org/cyberpunk-2077-modding/for-mod-creators-theory/references-lists-and-overviews/cheat-sheet-tweak-ids/cheat-sheet-base-stats> · documentação · A · integral.
- [S11] Weapon Damage Multipliers (Nexus 4247) — descrição, changelog, bugs e comentários. <https://www.nexusmods.com/cyberpunk2077/mods/4247> · fórum/imprensa · C/D · trechos.
- [S12] redscript — release v0.5.32 ("support script bundles from game patch 2.5"). <https://github.com/jac3km4/redscript/releases/tag/v0.5.32> · release oficial · A · integral.

- [S14] `GameObject.GetAttitudeTowards` / `EAIAttitude` — scripts descompilados, `core/entity/gameObject.swift`. Codeberg, 2026. <https://codeberg.org/adamsmasher/cyberpunk/raw/branch/master/core/entity/gameObject.swift> · código · A · trechos.
- [S16] redscript — README, instalação no Windows. <https://github.com/jac3km4/redscript#installation> · documentação · A · integral.
- [S15] XonMYHAND. "One Shot Headshot in Stealth". Nexus Mods 31793, 2026. <https://www.nexusmods.com/cyberpunk2077/mods/31793> · mod · B · descrição integral (via espelho de leitura).


## 7. Incidentes de segurança (injeção de prompt)

| Fonte | Sinais do escudo | O que o texto tentava | Ação |
| --- | --- | --- | --- |
| — | — | Nenhum incidente registado nesta pesquisa | — |

## 8. Limitações e perguntas em aberto

- O pool Tavily esgotou-se a meio da ronda 1 (14 chaves: HTTP 432/401). A
  pesquisa continuou por `web_fetch` direto às mesmas fontes primárias; a
  descoberta por motor de busca ficou limitada, sobretudo em Q4.
- Não houve validação empírica de combate (matar em jogo): a verificação foi
  compilação + arranque + type-check contra o bundle 2.5.
- `hitFlag.Kill` em alvos com `IsInvulnerable` não foi observado em execução; o
  mod adiciona uma guarda própria para esses casos.
- O comportamento de DOT e de armas com dano 0 não está documentado; fora do
  âmbito do hook localizado.

## 9. Metodologia

- Motor: tavily-agent-skill (`search` + `extract`), modo profundo com a flag
  `--deep-research`; fallback para `web_fetch` quando o pool de chaves esgotou.
- Rondas: 1 · subagentes investigadores: 7 · consultas: ~60 (entre Tavily e
  fetch direto) · fontes lidas na íntegra: 9.
- Verificação: type-check do mod contra `final.redscripts` da instalação 2.5 e
  smoke test de arranque do jogo com o mod compilado.


