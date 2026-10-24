# Mods de Cyberpunk 2077

<p align="center">
  <a href="https://github.com/frederico-kluser/cyberpunk-2077-mods/actions/workflows/ci.yml"><img src="https://github.com/frederico-kluser/cyberpunk-2077-mods/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="Licença: MIT"></a>
  <a href="https://github.com/frederico-kluser/cyberpunk-2077-mods/releases"><img src="https://img.shields.io/github/v/release/frederico-kluser/cyberpunk-2077-mods" alt="Release"></a>
</p>

Mods open-source para **Cyberpunk 2077** no PC. Cada mod fica na sua própria
pasta em [`mods/`](mods/), é escrito em Redscript, é distribuído como um zip
simples que se extrai na pasta do jogo e passa pelo mesmo pipeline de build,
validação e release.

[English](README.md)

## Mods

| Mod | Versão | O que faz |
| --- | --- | --- |
| [**Lethal Headshots**](mods/LethalHeadshots) | 1.1.0 | Todo headshot mata na hora — qualquer NPC, sem exceções. Sem multiplicadores de dano e sem o teto dos bosses: o acerto chama o kill forçado do próprio jogo. Mostra ainda o rótulo vermelho «QUE OTA» com a mira sobre uma cabeça letal. |
| [**Desert Eagle**](mods/DesertEagle) | 0.1.0 | Pistola Desert Eagle .50 AE por cima do esqueleto e das animações da Tsunami Nue, produzida por um pipeline automatizado de Blender (alinhamento, rigging, LODs, exportação). |

## Requisitos

- Cyberpunk 2077 para PC, **patch 2.5** (versão do jogo `3.0.88.x`).
- [redscript](https://github.com/jac3km4/redscript/releases) **0.5.32 ou mais
  recente** (a 0.5.32 é a primeira versão com suporte ao bundle de scripts da 2.5).

> O redscript compila `r6/scripts/**/*.reds` quando o jogo arranca, e o próprio
> engine faz isso — **o RED4ext não é necessário** para estes mods. Não é preciso
> iniciar com `-modded`; essa flag é apenas para pacotes REDmod.

## Instalar um mod

1. Instale o redscript na pasta do Cyberpunk 2077 (extraia o zip do release na raiz do jogo).
2. Descarregue o zip do mod na [página de releases](https://github.com/frederico-kluser/cyberpunk-2077-mods/releases).
3. Extraia o zip na pasta do Cyberpunk 2077, aceitando a fusão de pastas. Os
   scripts ficam em `r6\scripts\<ModId>\`.
4. Inicie o jogo.

Para desinstalar, apague a pasta `r6\scripts\<ModId>\`.

## O gate do CET (comando especial de inicialização)

O Cyber Engine Tweaks — necessário ao mod de diagnóstico **LogSentry** — só
deve carregar **quando pedires explicitamente**. Um *wrapper* decide antes de o
jogo arrancar. Adiciona isto a **Steam → Cyberpunk 2077 → Propriedades → Geral
→ Opções de inicialização**:

```
"C:\Users\kluse\Tools\cet-gate.bat" %command% -modded
```

| Arranque | Resultado |
| --- | --- |
| **com** `-modded` | CET ligado — consola + logs do LogSentry |
| **sem** `-modded` | CET desligado — jogo vanilla |

O `%command%` faz a Steam entregar o comando real do jogo ao *gate*
([`tools/cet-gate.bat`](tools/cet-gate.bat), instalado em
`C:\Users\kluse\Tools\`), que renomeia `cyber_engine_tweaks.asi` ↔
`cyber_engine_tweaks.asi.off` e depois arranca o jogo com todos os argumentos
encaminhados. O `-modded` chega também ao jogo e força o pipeline REDmod
(mantenha a pasta vazia `r6\cache\modded`).

Sem a flag, o jogo corre exatamente como se o CET não estivesse instalado.

## Compilar a partir do código

Os scripts de build precisam apenas de PowerShell 7 (ou Windows PowerShell 5.1)
e, opcionalmente, de uma instalação local do jogo para validar os tipos contra o
bundle real da 2.5.

```powershell
git clone https://github.com/frederico-kluser/cyberpunk-2077-mods.git
cd cyberpunk-2077-mods

# Verificações estáticas (não precisa do jogo)
pwsh -File tools/validate.ps1 -Static

# Validação completa contra a tua instalação
pwsh -File tools/validate.ps1 -DownloadTools

# Gerar os zips em dist/
pwsh -File tools/build.ps1

# Copiar o mod para o jogo
pwsh -File tools/deploy.ps1
```

## Estrutura do repositório

```text
mods/
  LethalHeadshots/
    mod.json              metadados lidos pelos scripts de build/release
    src/reds/             código Redscript (o mod propriamente dito)
  DesertEagle/
    mod.json              metadados lidos pelos scripts de build/release
    src/reds/             helper Redscript (spawn/teste)
    src/blender/          pipeline 3D automatizado (etapas bpy + testes)
    src/tweakxl/          registos do item (TweakXL)
    src/archivexl/        entity factory + traduções (ArchiveXL)
    docs/                 documentação do pipeline e da toolchain
docs/
  ARCHITECTURE.md         como o pipeline de dano funciona e porque o mod o interceta
  TESTING.md              como validar uma alteração, dentro e fora do jogo
  RELEASING.md            versionamento e checklist de release
  ADDING_A_MOD.md         como adicionar o proximo mod a este monorepo
tools/
  validate.ps1            verificações estáticas + type-check de Redscript
  build.ps1               empacota todos os mods em dist/*.zip
  deploy.ps1              copia um mod para o jogo local
```

## Contribuir

Leia primeiro o [CONTRIBUTING.md](CONTRIBUTING.md). Em resumo: crie um ramo a
partir de `main` com o nome `<tipo>/<slug>`, use
[Commits Convencionais](https://www.conventionalcommits.org/pt-br/), abra um pull
request e deixe o CI correr. O ramo `main` é protegido; commits diretos são
recusados.

## Segurança

Não reporte problemas de segurança em público. Veja [SECURITY.md](SECURITY.md).

## Licença

MIT. Veja [LICENSE](LICENSE).



