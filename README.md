# 🚀 PixelDust-Bot

**PixelDust-Bot** é um hub de inteligência artificial multimodal operado via Telegram. O projeto é focado em **privacidade e soberania de dados**, rodando inteiramente de forma local através de integrações com **LM Studio**, **llama.cpp** e **Stable Diffusion (Forge/Neo)**.

Ele transforma seu Telegram em uma central de comando para conversas, pesquisas na web, análise de documentos e geração de arte.

---

## ✨ Funcionalidades Principais

*   **🤖 Chat Inteligente (Local LLM):** Integração com APIs compatíveis com o padrão OpenAI (LM Studio, llama.cpp, Ollama). Possui memória de contexto baseada em notas salvas no banco de dados SQLite.
*   **🖼️ Geração de Imagens:** Interface direta com Stable Diffusion (A1111/Forge/comfyui) via API, com suporte a prompts negativos automáticos, filtros de qualidade e seleção de modelos.
*   **👾 Pixel Art Engine:** Gera ativos 64x64 via IA e os converte instantaneamente em **Stickers do Telegram** (PNG 512x512) usando a biblioteca CairoSVG.
*   **👁️ Visão Computacional & OCR:** Transcreve imagens e analisa arquivos PDF (mesmo PDFs escaneados, convertendo-os em imagens para que a IA possa "enxergar").
*   **🌐 Inteligência de Pesquisa:** 
    *   Busca notícias em tempo real via RSS (Google News).
    *   Web Scraping direto de links para resumos automáticos via LLM.
*   **📝 Gerenciador de Notas:** Sistema robusto de anotações para armazenamento de informações e base de conhecimento dinâmica para o chat.
*   **🛡️ Segurança Multi-usuário:** Sistema de permissões (Admin/User) para controle de quem pode utilizar os recursos do seu hardware.

---

## ⚠️ Requisito Crítico: GTK Runtime (Windows)

A geração de stickers e o processamento de imagens SVG exigem a biblioteca **CairoSVG**. No Windows, ela depende de arquivos binários (`.dll`) externos. **O bot não iniciará sem o GTK Runtime.**

1.  Baixe o instalador `.exe` (versão win64) em: [GTK for Windows Runtime Releases](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases).
2.  Instale e certifique-se de marcar a opção **"Add to PATH"** durante o processo.
3.  Reinicie o seu terminal após a instalação.

---

##  🛠️ Detalhes Técnicos e Customização

1. Compatibilidade de API (OpenAI Standard)
O bot foi construído sobre o padrão de comunicação da OpenAI. Isso permite que você substitua o LM Studio pelo llama.cpp server ou qualquer outra solução que suporte o endpoint /v1/chat/completions. Basta ajustar a URL e o nome do modelo no arquivo keys.env.

2. User-Agent e Web Scraping
Para evitar bloqueios (Erro 403) ao acessar sites para resumo, você pode customizar o User-Agent do navegador simulado dentro do arquivo pesquisa.py, alterando a variável HEADERS.

3. Limite de Caracteres do Telegram
O Telegram possui um limite rígido de 4096 caracteres por mensagem. Este bot possui lógica interna para truncar textos muito longos (como resumos extensos de sites ou listagens de banco de dados) para garantir que a mensagem seja entregue sem erros.

4. Geração de Imagem (Forge/Neo)
Certifique-se de que o seu Stable Diffusion esteja rodando com a flag --api ativada. A URL padrão configurada no código é http://localhost:7860/sdapi/v1/txt2img.

##  🚀 Como Executar

O projeto inclui scripts que gerenciam automaticamente o ambiente virtual (venv) e as dependências (req.txt).

No Windows:
Execute o arquivo: start.bat

No Linux:
Execute os comandos:
chmod +x start.sh
./start.sh

---

##  📂 Organização do Projeto

• bot.py: Ponto de entrada, handlers de comandos e segurança.
• chat.py: Interface de conversação e Visão Computacional.
• imagem_ia.py: Conexão com a API do Stable Diffusion.
• pesquisa.py: Motor de Scraping e busca de notícias RSS.
• pixelart_svg.py: Gerador de código vetorial e lógica de ativos.
• anotador.py: Gerenciamento do banco de dados SQLite e autorizações.
• pdf_helper.py: Processamento de documentos e conversão PDF-para-Imagem.

Este projeto está sob a licença MIT. Sinta-se livre para usar, modificar e distribuir conforme necessário.

---

## ⚙️ Configuração do Ambiente

1.  Crie um arquivo chamado **`keys.env`** na raiz do projeto.
2.  Preencha com as seguintes variáveis:

```env
TOKEN="SEU_TOKEN_DO_TELEGRAM"
MEU_ID="SEU_ID_TELEGRAM_PARA_ADMIN"

# URL da API de texto (Padrão OpenAI)
# Pode ser LM Studio, llama.cpp ou servidor Ollama
LM_STUDIO_GLOBAL="http://localhost:1234/v1/chat/completions"

# Nome exato do modelo que está carregado no seu servidor de IA
MODEL_NAMEGLOBAL="nome-do-seu-modelo"

---


