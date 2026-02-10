# 🚀 PixelDust-Bot

**PixelDust-Bot** é um hub de inteligência artificial multimodal operado via Telegram. O projeto é focado em **privacidade e soberania de dados**, rodando inteiramente de forma local através de integrações com **LM Studio**, **llama.cpp** e **Stable Diffusion (Forge/Neo)**.

Ele transforma seu Telegram em uma central de comando para conversas, pesquisas na web, análise de documentos e geração de arte.

---

## ✨ Funcionalidades Principais

*   **🤖 Chat Inteligente (Local LLM):** Integração com APIs compatíveis com o padrão OpenAI (LM Studio, llama.cpp, Ollama). Possui memória de contexto baseada em notas salvas no banco de dados SQLite.
*   **🖼️ Geração de Imagens:** Interface direta com Stable Diffusion (A1111/Forge) via API, com suporte a prompts negativos automáticos, filtros de qualidade e seleção de modelos.
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


