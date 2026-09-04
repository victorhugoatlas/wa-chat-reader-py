# WA Chat Reader by VH
- Este projeto permite a remontagem de conversas exportadas do WhatsApp em iOS/iPhone.
- O WhatsApp exporta um arquivo compactado com um `.txt` guia e mídias separadas. Esta ferramenta organiza tudo em uma interface HTML intuitiva, semelhante ao layout do próprio aplicativo.

## Funcionalidades
- **Organização Cronológica:** Une texto e mídias no fluxo correto da conversa.
- **Suporte Multimídia:** Visualização direta de fotos, vídeos e player de áudio.
- **Interface Moderna:** Desenvolvido em Python com CustomTkinter.

## Como usar?
1. Baixe o arquivo compactado da conversa exportada no seu computador e extraia-o completamente.
2. Abra o `WA Chat Reader` (por enquanto é necessário usar um editor de código, recomendo o VS Code)
3. Clique no botão **"Procurar Pasta"** e selecione a pasta que contém os arquivos.
4. Clique em **"Processar"**. O programa gerará um arquivo `.html` na mesma pasta.
5. Abra o arquivo `.html` gerado em qualquer navegador.