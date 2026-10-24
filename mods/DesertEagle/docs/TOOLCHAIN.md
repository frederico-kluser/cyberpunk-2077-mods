# Toolchain — o que está instalado e onde

Registo verificado nesta máquina (Acer Predator, Windows). Ficheiros de trabalho
grandes ficam fora do git; aqui ficam os caminhos, versões e comandos exatos.

## Jogo

| Item | Valor |
| --- | --- |
| Cyberpunk 2077 (Steam) | `C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077` |
| Versão do jogo alvo | 2.5 (`3.0.88.x`) |
| `tools\redmod\bin\redMod.exe` | **ausente** nesta instalação (o jogo não o traz) |

## Blender + add-ons

| Item | Versão | Local |
| --- | --- | --- |
| Blender | 5.2.3 (ZIP oficial, SHA256 `723F08A4401502561EB763CDEACF8745B31E5F3F154D287D3830D97CF75DC2FB`) | `C:\Users\kluse\Tools\Blender\5.2\blender.exe` |
| Cyberpunk Blender Add-on (WolvenKit IO Suite) | 2.x | `C:\Users\kluse\Tools\Blender\addons\` + user addons do Blender 5.2 |
| BlenderMCP (add-on + servidor) | blender-mcp 2.0.0 → mcp-for-blender 2.2.3 | add-on em `C:\Users\kluse\Tools\Blender\addons\`; servidor via `uvx mcp-for-blender` |
| Rokoko Studio Live (retargeting) | 1.4.x | ver estado em baixo |
| REDmod Blender plugin (export `.re`) | — | ver estado em baixo |

Comandos:

```powershell
# Blender headless (pipeline e testes)
& 'C:\Users\kluse\Tools\Blender\5.2\blender.exe' --background --python <script.py>

# Servidor MCP do Blender (para vibe coding)
& 'C:\Users\kluse\AppData\Roaming\Python\Python312\Scripts\uvx.exe' mcp-for-blender
```

Estado dos add-ons (verificado por execução headless `ALL_ADDONS_VERIFIED`):

| Add-on | Módulo | Fonte | Estado |
| --- | --- | --- | --- |
| Cyberpunk IO Suite 2.0.0 | `i_scene_cp77_gltf` | `WolvenKit/Cyberpunk-Blender-add-on` release 2.0.0 (`Cyberpunk-Blender-Add-On-2.0.0.zip`) | ativo — arranca com "Cyberpunk IO Suite Has Started" |
| BlenderMCP | `blender_mcp` | `ahujasid/mcp-for-blender` (`addon.py`) | ativo — "BlenderMCP addon registered" |
| Rokoko Studio Live 1.4.3 | `rokoko` | source-tag `v1-4-3` repacotada (`rokoko-v1-4-3-install.zip`) | ativo mas **degradado** no Blender 5.2: `LZ4` e `boto3` em falta → live-streaming/cloud login não funcionam; retarget local OK. Se falhar em runtime, usar Blender 4.5 LTS (suporte oficial até 4.4) |
| REDmod Blender plugin (CDPR) | `blender_re_animations_plugin` | CDN oficial `https://cdn-l-cyberpunk.cdprojektred.com/redmod/REDmodPlugin_updated.zip` | ativo (exige `h5py`/`numpy` no Python do Blender — já instalados) |

Armadilhas de instalação registadas:
- O instalador do plugin REDmod trata **qualquer** saída em stderr do pip como
  falha (`h5py package installation failed!`) mesmo quando a instalação passou —
  resolver com `"<blender>\5.2\python\bin\python.exe" -m pip install --target "<blender>\5.2\python\Lib" h5py`.
- `gh release view <repo>` sem `-R` falha dentro de um repo git — usar sempre
  `gh ... -R <owner/repo>` (ou `gh api repos/<owner>/<repo>/releases/tags/<tag>`).
- O add-on do BlenderMCP toma o nome do módulo do nome do ficheiro: copiar
  `addon.py` para `blender_mcp.py` antes de instalar.

## WolvenKit

| Item | Versão | Local |
| --- | --- | --- |
| WolvenKit.App (GUI, self-contained) | 9.1.0 | `C:\Users\kluse\Tools\WolvenKit\9.1.0\WolvenKit.App\WolvenKit.exe` |
| WolvenKit.CLI | 9.1.0 | `C:\Users\kluse\Tools\WolvenKit\9.1.0\wolvenkit-cli.cmd` (wrapper; usa o .NET local) |
| .NET runtime | 10.0.13 (user-local, sem elevação) | `C:\Users\kluse\Tools\dotnet\dotnet.exe` |

Comandos verificados:

```powershell
# versão / ajuda
& 'C:\Users\kluse\Tools\WolvenKit\9.1.0\wolvenkit-cli.cmd' --version      # → 9.1.0

# extrair um .archive (smoke test real: basegame_2_mainmenu.archive → 53 ficheiros)
& 'C:\Users\kluse\Tools\WolvenKit\9.1.0\wolvenkit-cli.cmd' unbundle `
    "<jogo>\archive\pc\content\basegame_2_mainmenu.archive" -o <destino>

# extrair + converter para raw (uncook)
& 'C:\Users\kluse\Tools\WolvenKit\9.1.0\wolvenkit-cli.cmd' uncook `
    "<jogo>\archive\pc\content" -o <destino> -gp "<jogo>" --uext png
```

## Frameworks de runtime (na pasta do jogo)

| Framework | Versão | Local no jogo |
| --- | --- | --- |
| ArchiveXL | 1.27.5 | `red4ext\plugins\ArchiveXL\` (DLL + `Bundle\ArchiveXL.archive` + Scripts `.reds`) |
| TweakXL | 1.11.5 | `red4ext\plugins\TweakXL\` (DLL + `Data\` + `Scripts\TweakXL.reds`) |
| RED4ext | *(instalar — obrigatório para os dois acima carregarem)* | `bin\x64\winmm.dll` + `red4ext\red4ext.dll` |
| redscript | *(ver repo: os mods usam `>=0.5.32`)* | `r6\scripts\` |

Nota de layout: o TweakXL 1.11.5 já **não** instala `.reds` em `r6\scripts\TweakXL`;
tudo vive em `red4ext\plugins\TweakXL\Scripts\`.

## Python / MCP

| Item | Versão | Local |
| --- | --- | --- |
| Python | 3.12.10 | `python3` no PATH |
| uv / uvx | 0.13.5 | `C:\Users\kluse\AppData\Roaming\Python\Python312\Scripts\uvx.exe` |
| blender-mcp (servidor) | 2.0.0 → mcp-for-blender 2.2.3 | cacheado em `C:\Users\kluse\AppData\Local\uv\cache` (funciona offline) |

## Ativos extraídos do jogo (molde Tsunami Nue)

*(preenchido após a extração — ver `../assets/extracted/` e o relatório do pipeline)*

## Modelo 3D da Desert Eagle

Candidatos e licenças: [`../assets/sources.json`](../assets/sources.json).
A licença escolhida (e o crédito respetivo, se CC-BY) fica registada aqui.
