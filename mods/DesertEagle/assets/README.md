# assets/ — ativos do pipeline

Nenhum binário é versionado (ver `.gitignore` acima). Este diretório organiza o
que o pipeline consome e produz:

```text
assets/
├── sources.json     manifesto de fontes do modelo 3D (URLs, licenças, estado)
├── raw/             modelo bruto descarregado (desert_eagle.fbx/.glb)
├── extracted/       molde extraído do jogo via WolvenKit (w_handgun_nue.*)
└── work/            saídas do pipeline Blender (.glb final, .blend, relatórios)
```

## Regras

1. **Licença primeiro**: nada entra em `raw/` sem a licença estar registada em
   `sources.json` (CC0/CC-BY/CC-BY-SA). CC-BY exige atribuição — o crédito vai
   no `README.md` do mod e no `INSTALL.txt` do pacote.
2. **`extracted/` é material do jogo**: serve só como molde de trabalho; o mod
   final distribui apenas os ficheiros derivados criados por nós.
3. Relatórios do pipeline (`work/pipeline_report.json`) são o registo do que foi
   feito a cada execução — guardam-se localmente, não se versionam.
