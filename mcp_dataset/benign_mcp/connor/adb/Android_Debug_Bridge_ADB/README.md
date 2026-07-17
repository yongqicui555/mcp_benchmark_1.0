# ADB MCP Server (Python)

Um servidor MCP (Model Context Protocol) em Python que permite ao Claude comunicar diretamente com dispositivos Android através do Android Debug Bridge (ADB).

## 🚀 Funcionalidades

- **Gerenciamento de Dispositivos**: Listar dispositivos conectados
- **Execução de Comandos**: Executar comandos shell no Android
- **Instalação/Desinstalação**: Gerenciar apps no dispositivo
- **Captura de Logs**: Acessar logcat do Android
- **Screenshots**: Capturar tela do dispositivo
- **Transferência de Arquivos**: Push/pull de arquivos
- **Simulação de Entrada**: Toques, swipes, digitação
- **Listagem de Apps**: Ver apps instalados
- **Informações do Sistema**: Bateria, versão, modelo, memória

## 📋 Pré-requisitos

1. **Python 3.10+**
2. **uv** (gerenciador de pacotes Python)
3. **ADB (Android Debug Bridge)** instalado em `C:\Users\Cristiano\Programação\ADB\`
4. **Dispositivo Android** com depuração USB habilitada
5. **Claude Desktop** com suporte a MCP

## 🛠️ Instalação

### 1. Instalar uv (se não tiver)
```bash
# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex

# Ou baixar do site oficial: https://github.com/astral-sh/uv
```

### 2. Criar e configurar o projeto
```bash
# Criar diretório
mkdir adb-mcp-server
cd adb-mcp-server

# Salvar os arquivos (main.py e pyproject.toml)
# Depois executar:

# Instalar dependências
uv sync

# Testar se funciona
uv run python main.py
```

### 3. Estrutura de arquivos
```
adb-mcp-server/
├── main.py              # Código principal do servidor
├── pyproject.toml        # Configurações do projeto
├── README.md            # Este arquivo
└── .venv/              # Ambiente virtual (criado pelo uv)
```

## ⚙️ Configuração no Claude Desktop

Adicione esta configuração ao arquivo de configuração do Claude Desktop:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "adb": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\caminho\\para\\adb-mcp-server",
        "run",
        "python",
        "main.py"
      ]
    }
  }
}
```

**Exemplo com caminho real:**
```json
{
  "mcpServers": {
    "adb": {
      "command": "uv",
      "args": [
        "--directory", 
        "C:\\Users\\Cristiano\\Documents\\adb-mcp-server",
        "run",
        "python", 
        "main.py"
      ]
    }
  }
}
```

## 📱 Preparando o Dispositivo Android

1. **Habilitar Opções do Desenvolvedor:**
   - Vá em Configurações > Sobre o telefone
   - Toque 7 vezes em "Número da versão"

2. **Habilitar Depuração USB:**
   - Configurações > Opções do desenvolvedor
   - Ative "Depuração USB"

3. **Conectar via USB:**
   - Conecte o dispositivo ao PC
   - Aceite o prompt de autorização no Android

4. **Testar conexão:**
```bash
# No seu diretório do ADB
cd "C:\Users\Cristiano\Programação\ADB"
.\adb.exe devices
```

## 🎯 Exemplos de Uso com Claude

### Comandos Básicos
```
"Liste os dispositivos Android conectados"
"Quais apps estão instalados no meu telefone?"
"Tire uma screenshot e salve em C:\Screenshots\tela.png"
"Mostre informações da bateria do meu telefone"
```

### Automação e Controle
```
"Toque na coordenada 500, 800 do meu telefone"
"Digite 'Olá mundo' no meu telefone"
"Deslize da coordenada 300,500 até 300,200"
"Pressione o botão home (keyevent 3)"
```

### Desenvolvimento e Debug
```
"Execute o comando 'getprop ro.build.version.release' no meu telefone"
"Mostre os últimos 50 logs do sistema com filtro 'Error'"
"Instale o app em C:\Downloads\meuapp.apk"
"Desinstale o app com.exemplo.meuapp"
```

### Transferência de Arquivos
```
"Envie o arquivo C:\Downloads\foto.jpg para /sdcard/Pictures/"
"Baixe o arquivo /sdcard/Download/documento.pdf para C:\Documentos\"
```

## 🔧 Comandos Disponíveis

| Comando | Descrição | Exemplo de Uso |
|---------|-----------|----------------|
| `adb_devices` | Lista dispositivos | "Quais dispositivos estão conectados?" |
| `adb_shell` | Executa comando shell | "Execute 'ls /sdcard/' no telefone" |
| `adb_install` | Instala APK | "Instale o app em C:\app.apk" |
| `adb_uninstall` | Remove app | "Desinstale com.example.app" |
| `adb_logcat` | Captura logs | "Mostre logs com filtro 'Error'" |
| `adb_screenshot` | Captura tela | "Screenshot para C:\tela.png" |
| `adb_push` | Envia arquivo | "Envie arquivo.txt para /sdcard/" |
| `adb_pull` | Puxa arquivo | "Baixe /sdcard/foto.jpg para C:\\" |
| `adb_input` | Simula entrada | "Toque em 100, 200" |
| `adb_apps` | Lista apps | "Quais apps tenho instalados?" |
| `adb_info` | Info do sistema | "Mostre informações da bateria" |

## 🔍 Solução de Problemas

### Erro: "ADB não encontrado"
```bash
# Verifique o caminho no código
# Edite a variável ADB_PATH em main.py
ADB_PATH = r"C:\Users\Cristiano\Programação\ADB\adb.exe"
```

### Erro: "Device not found"
```bash
# Teste manualmente
cd "C:\Users\Cristiano\Programação\ADB"
.\adb.exe devices

# Se não aparecer dispositivos:
# 1. Reconecte o cabo USB
# 2. Revoke autorização USB e autorize novamente
# 3. Instale drivers USB do fabricante
```

### Erro: "Permission denied"
- Alguns comandos precisam de root
- Verifique se o app tem as permissões necessárias
- Alguns comandos só funcionam em modo desenvolvedor

### Testando o servidor
```bash
# No diretório do projeto
uv run python main.py

# Se aparecer mensagem sem erro, o servidor está funcionando
# Pressione Ctrl+C para parar
```

## 🚀 Comandos Úteis do uv

```bash
# Instalar/atualizar dependências
uv sync

# Executar o servidor
uv run python main.py

# Adicionar nova dependência
uv add nome-da-biblioteca

# Atualizar todas as dependências
uv sync --upgrade

# Verificar dependências
uv tree
```

## 🔐 Segurança

- ⚠️ Este servidor executa comandos ADB com privilégios do usuário
- ✅ Use apenas com dispositivos próprios
- ⚠️ Cuidado ao executar comandos shell desconhecidos
- ✅ Mantenha o ADB atualizado
- ✅ Dispositivos são isolados por ID (se múltiplos conectados)

## 📈 Melhorias Futuras

- [ ] Suporte a múltiplos dispositivos simultâneos
- [ ] Interface web para monitoramento
- [ ] Cache de comandos frequentes
- [ ] Logs detalhados de operações
- [ ] Suporte a comandos personalizados
- [ ] Integração com scrcpy para controle visual

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch: `git checkout -b minha-feature`
3. Commit: `git commit -m 'Nova feature'`
4. Push: `git push origin minha-feature`
5. Abra um Pull Request

## 📄 Licença

MIT License - use livremente!

## 📞 Suporte

**Problemas comuns:**
1. ✅ Verifique se o uv está instalado: `uv --version`
2. ✅ Confirme o caminho do ADB no código
3. ✅ Teste ADB manualmente antes de usar o MCP
4. ✅ Verifique os logs do Claude Desktop para erros
5. ✅ Certifique-se que o dispositivo autoriza a depuração USB

**Debug avançado:**
```bash
# Testar ADB manualmente
"C:\Users\Cristiano\Programação\ADB\adb.exe" devices

# Testar comando específico
"C:\Users\Cristiano\Programação\ADB\adb.exe" shell "getprop ro.build.version.release"

# Verificar se o Python encontra o MCP
uv run python -c "import mcp; print('MCP OK')"
```