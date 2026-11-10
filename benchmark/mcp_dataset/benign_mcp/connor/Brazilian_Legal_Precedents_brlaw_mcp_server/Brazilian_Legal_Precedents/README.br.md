# Servidor MCP de Pesquisa em Direito Brasileiro

[🇺🇸 Read in English](README.md)

Um servidor MCP (Model Context Protocol) para pesquisa sobre direito brasileiro movida por agentes 
de IA usando fontes oficiais.

## Prefácio
Este servidor capacita modelos com capacidades de scraping, facilitando assim a pesquisa para 
qualquer pessoa legitimamente interessada em questões jurídicas brasileiras.

Esta facilidade vem com um preço: o risco de sobrecarregar os servidores das fontes oficiais se 
mal utilizada. Por favor, mantenha a carga nas fontes em uma quantidade razoável.

## Requisitos

- git
- uv (recomendado) ou Python >= 3.12
- Google Chrome

## Como usar

1. Clone o repositório:
```bash
git clone https://github.com/pdmtt/brlaw_mcp_server.git
```

2. Instale as dependências
```bash
uv run patchright install
```

3. Configure seu cliente MCP (ex: Claude Desktop):
```json
{
  "mcpServers": {
    "brlaw_mcp_server": {
      "command": "uv",
      "args": [
        "--directory",
        "/<caminho>/brlaw_mcp_server",
        "run",
        "serve"
      ]
    }
  }
}
```

### Ferramentas Disponíveis

- `StjLegalPrecedentsRequest`: Pesquisa precedentes judiciais feitos pelo Superior Tribunal de 
  Justiça (STJ) que atendam aos critérios especificados.
- `TstLegalPrecedentsRequest`: Pesquisa precedentes judiciais feitos pelo Tribunal Superior do 
  Trabalho (TST) que atendam aos critérios especificados.
- `StfLegalPrecedentsRequest`: Pesquisa precedentes judiciais feitos pelo Supremo Tribunal Federal 
  (STF) que atendam aos critérios especificados.

## Desenvolvimento

### Ferramentas

O projeto utiliza:
- Ruff para linting e formatação.
- BasedPyright para verificação de tipos.
- Pytest para testes.

### Idioma

Recursos, ferramentas e materiais relacionados a prompts devem ser escritos em português, pois este 
projeto tem como objetivo ser utilizado por pessoas que não são desenvolvedoras, como advogados e 
estudantes de direito.

O vocabulário técnico jurídico é altamente dependente da tradição legal de um país e sua tradução 
não é uma tarefa trivial.

Materiais relacionados ao desenvolvimento devem permanecer em inglês, conforme convencional, como o 
código-fonte.

## Licença

Este projeto está licenciado sob a Licença MIT - consulte o arquivo LICENSE para obter detalhes. 