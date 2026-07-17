#!/usr/bin/env python3
"""
ADB MCP Server - Permite ao Claude comunicar com dispositivos Android via ADB
"""

import asyncio
import subprocess
import sys
import json
from typing import Any, Sequence
from pathlib import Path

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

# Caminho para o ADB - ajuste conforme necessário
ADB_PATH = r"C:\Users\Cristiano\Programação\ADB\adb.exe"

class ADBMCPServer:
    def __init__(self):
        self.server = Server("adb-mcp-server")
        self.setup_handlers()

    async def execute_adb(self, command: str, timeout: int = 30) -> str:
        """Executa um comando ADB e retorna o resultado"""
        try:
            full_command = f'"{ADB_PATH}" {command}'
            print(f"Executando: {full_command}", file=sys.stderr)
            
            process = await asyncio.create_subprocess_shell(
                full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout
            )
            
            if process.returncode != 0 and stderr:
                error_msg = stderr.decode('utf-8', errors='ignore').strip()
                if 'daemon started' not in error_msg.lower():
                    raise Exception(f"Comando ADB falhou: {error_msg}")
            
            return stdout.decode('utf-8', errors='ignore').strip()
            
        except asyncio.TimeoutError:
            raise Exception(f"Comando ADB timeout após {timeout} segundos")
        except Exception as e:
            raise Exception(f"Erro ao executar comando ADB: {str(e)}")

    async def _execute_aux_app_query(self, device_flag: str, args: dict[str, Any]) -> str:
        """
        Executa o aplicativo auxiliar para consultar um Content Provider e retorna o resultado.
        Espera que o app auxiliar grave o resultado em 'output_file'.
        """
        aux_app_package = args.get("aux_app_package")
        aux_app_activity = args.get("aux_app_activity")
        output_file_remote = args.get("output_file")
        
        if not all([aux_app_package, aux_app_activity, output_file_remote]):
            raise ValueError("aux_app_package, aux_app_activity e output_file são obrigatórios para query_content_provider.")

        # Prepara os extras para a Intent
        extras = []
        if args.get("uri"):
            extras.append(f"--es uri '{args['uri']}'")
        if args.get("projection"):
            extras.append(f"--es projection '{json.dumps(args['projection'])}'")
        if args.get("selection"):
            extras.append(f"--es selection '{args['selection']}'")
        if args.get("selection_args"):
            extras.append(f"--es selection_args '{json.dumps(args['selection_args'])}'")
        if args.get("sort_order"):
            extras.append(f"--es sort_order '{args['sort_order']}'")
        extras.append(f"--es output_file '{output_file_remote}'")

        # Comando para iniciar a atividade do aplicativo auxiliar
        start_command = (
            f"am start -n {aux_app_package}/{aux_app_activity} "
            f"-a android.intent.action.VIEW {' '.join(extras)}"
        )
        
        # Executa o comando de início do app
        await self.execute_adb(f'{device_flag} shell "{start_command}"')
        
        # Aguarda um tempo para o app processar e gravar o arquivo
        await asyncio.sleep(2) # Ajuste este tempo conforme a complexidade da query

        # Puxa o arquivo de saída do dispositivo
        local_output_file = f"temp_content_provider_output_{Path(output_file_remote).name}"
        await self.execute_adb(f'{device_flag} pull {output_file_remote} "{local_output_file}"')
        
        # Lê o conteúdo do arquivo local
        content = Path(local_output_file).read_text(encoding='utf-8', errors='ignore')
        
        # Opcional: Remover o arquivo temporário no dispositivo e no PC
        await self.execute_adb(f'{device_flag} shell rm {output_file_remote}')
        Path(local_output_file).unlink(missing_ok=True)
        
        return content


    def setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            return [
                types.Tool(
                    name="adb_devices",
                    description="Lista todos os dispositivos Android conectados",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                types.Tool(
                    name="adb_shell",
                    description="Executa um comando shell no dispositivo Android",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Comando shell para executar no dispositivo"
                            },
                            "device_id": {
                                "type": "string",
                                "description": "ID do dispositivo (opcional, usa o primeiro disponível se não especificado)"
                            }
                        },
                        "required": ["command"]
                    }
                ),
                types.Tool(
                    name="adb_install",
                    description="Instala um APK no dispositivo",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "apk_path": {
                                "type": "string",
                                "description": "Caminho para o arquivo APK"
                            },
                            "device_id": {
                                "type": "string",
                                "description": "ID do dispositivo (opcional)"
                            }
                        },
                        "required": ["apk_path"]
                    }
                ),
                types.Tool(
                    name="adb_uninstall",
                    description="Desinstala um app do dispositivo",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "package_name": {
                                "type": "string",
                                "description": "Nome do pacote do app (ex: com.example.app)"
                            },
                            "device_id": {
                                "type": "string",
                                "description": "ID do dispositivo (opcional)"
                            }
                        },
                        "required": ["package_name"]
                    }
                ),
                types.Tool(
                    name="adb_logcat",
                    description="Captura logs do dispositivo Android",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filter": {
                                "type": "string",
                                "description": "Filtro para os logs (opcional)"
                            },
                            "lines": {
                                "type": "integer",
                                "description": "Número de linhas para capturar (padrão: 100)"
                            },
                            "device_id": {
                                "type": "string",
                                "description": "ID do dispositivo (opcional)"
                            }
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="adb_screenshot",
                    description="Captura screenshot do dispositivo",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "save_path": {
                                "type": "string",
                                "description": "Caminho local para salvar a screenshot"
                            },
                            "device_id": {
                                "type": "string",
                                "description": "ID do dispositivo (opcional)"
                            }
                        },
                        "required": ["save_path"]
                    }
                ),
                types.Tool(
                    name="adb_push",
                    description="Envia arquivo do PC para o dispositivo",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "local_path": {
                                "type": "string",
                                "description": "Caminho local do arquivo"
                            },
                            "remote_path": {
                                "type": "string",
                                "description": "Caminho no dispositivo"
                            },
                            "device_id": {
                                "type": "string",
                                "description": "ID do dispositivo (opcional)"
                            }
                        },
                        "required": ["local_path", "remote_path"]
                    }
                ),
                types.Tool(
                    name="adb_pull",
                    description="Puxa arquivo do dispositivo para o PC",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "remote_path": {
                                "type": "string",
                                "description": "Caminho do arquivo no dispositivo"
                            },
                            "local_path": {
                                "type": "string",
                                "description": "Caminho local para salvar"
                            },
                            "device_id": {
                                "type": "string",
                                "description": "ID do dispositivo (opcional)"
                            }
                        },
                        "required": ["remote_path", "local_path"]
                    }
                ),
                types.Tool(
                    name="adb_input",
                    description="Simula entrada de texto ou toque na tela",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "input_type": {
                                "type": "string",
                                "enum": ["text", "tap", "swipe", "keyevent"],
                                "description": "Tipo de entrada"
                            },
                            "value": {
                                "type": "string",
                                "description": "Texto para digitar, coordenadas para tap (x y), coordenadas para swipe (x1 y1 x2 y2), ou código do keyevent"
                            },
                            "device_id": {
                                "type": "string",
                                "description": "ID do dispositivo (opcional)"
                            }
                        },
                        "required": ["input_type", "value"]
                    }
                ),
                types.Tool(
                    name="adb_apps",
                    description="Lista apps instalados no dispositivo",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "system_apps": {
                                "type": "boolean",
                                "description": "Incluir apps do sistema (padrão: false)"
                            },
                            "device_id": {
                                "type": "string",
                                "description": "ID do dispositivo (opcional)"
                            }
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="adb_info",
                    description="Obtém informações gerais do dispositivo Android (bateria, versão, modelo, memória, armazenamento).",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "info_type": {
                                "type": "string",
                                "enum": ["battery", "version", "model", "memory", "storage", "all"],
                                "description": "Tipo de informação a obter"
                            },
                            "device_id": {
                                "type": "string",
                                "description": "ID do dispositivo (opcional)"
                            }
                        },
                        "required": ["info_type"]
                    }
                ),
                types.Tool(
                    name="adb_get_system_property",
                    description="Obtém o valor de uma propriedade de sistema específica.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "property_name": {
                                "type": "string",
                                "description": "Nome da propriedade de sistema (ex: ro.build.version.sdk, ro.product.manufacturer)"
                            },
                            "device_id": {
                                "type": "string",
                                "description": "ID do dispositivo (opcional)"
                            }
                        },
                        "required": ["property_name"]
                    }
                ),
                types.Tool(
                    name="adb_list_features",
                    description="Lista as funcionalidades de hardware e software suportadas pelo dispositivo.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "ID do dispositivo (opcional)"
                            }
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="adb_check_app_details",
                    description="Obtém detalhes sobre um aplicativo específico instalado no dispositivo.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "package_name": {
                                "type": "string",
                                "description": "Nome do pacote do aplicativo (ex: com.android.chrome)"
                            },
                            "device_id": {
                                "type": "string",
                                "description": "ID do dispositivo (opcional)"
                            }
                        },
                        "required": ["package_name"]
                    }
                ),
                 types.Tool(
                    name="adb_list_accounts",
                    description="Lista as contas de usuário configuradas no dispositivo Android.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "ID do dispositivo (opcional)"
                            }
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="adb_network_info",
                    description="Obtém informações detalhadas sobre a conectividade de rede do dispositivo.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "ID do dispositivo (opcional)"
                            }
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="adb_running_processes",
                    description="Lista todos os processos em execução no dispositivo Android.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "ID do dispositivo (opcional)"
                            }
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="adb_screen_resolution",
                    description="Obtém a resolução da tela do dispositivo Android.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "string",
                                "description": "ID do dispositivo (opcional)"
                            }
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="adb_query_content_provider",
                    description="Consulta um Content Provider no dispositivo Android usando um aplicativo auxiliar.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "uri": {
                                "type": "string",
                                "description": "URI do Content Provider (ex: content://sms/inbox, content://contacts/people)"
                            },
                            "projection": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Lista de colunas a serem retornadas (opcional)"
                            },
                            "selection": {
                                "type": "string",
                                "description": "Cláusula WHERE para filtrar resultados (opcional)"
                            },
                            "selection_args": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Argumentos para a cláusula WHERE (opcional)"
                            },
                            "sort_order": {
                                "type": "string",
                                "description": "Ordem de classificação (opcional)"
                            },
                            "aux_app_package": {
                                "type": "string",
                                "description": "Nome do pacote do aplicativo auxiliar no dispositivo que fará a consulta."
                            },
                            "aux_app_activity": {
                                "type": "string",
                                "description": "Nome completo da atividade no aplicativo auxiliar para ser acionada."
                            },
                            "output_file": {
                                "type": "string",
                                "description": "Caminho no /sdcard/ onde o app auxiliar deve salvar os resultados (ex: /sdcard/cp_output.txt)"
                            },
                            "device_id": {
                                "type": "string",
                                "description": "ID do dispositivo (opcional)"
                            }
                        },
                        "required": ["uri", "aux_app_package", "aux_app_activity", "output_file"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict[str, Any] | None
        ) -> list[types.TextContent]:
            try:
                if arguments is None:
                    arguments = {}

                device_flag = ""
                if arguments.get("device_id"):
                    device_flag = f"-s {arguments['device_id']}"

                result = ""

                if name == "adb_devices":
                    result = await self.execute_adb("devices -l")
                    
                elif name == "adb_shell":
                    command = arguments["command"]
                    result = await self.execute_adb(f'{device_flag} shell "{command}"')
                    
                elif name == "adb_install":
                    apk_path = arguments["apk_path"]
                    if not Path(apk_path).is_file():
                        raise FileNotFoundError(f"APK não encontrado: {apk_path}")
                    result = await self.execute_adb(f'{device_flag} install "{apk_path}"')
                    
                elif name == "adb_uninstall":
                    package = arguments["package_name"]
                    result = await self.execute_adb(f'{device_flag} uninstall {package}')
                    
                elif name == "adb_logcat":
                    lines = arguments.get("lines", 100)
                    filter_text = arguments.get("filter", "")
                    
                    cmd = f'{device_flag} logcat -d -t {lines}'
                    if filter_text:
                        cmd += f' | findstr /I "{filter_text}"'
                    
                    result = await self.execute_adb(cmd)
                    
                elif name == "adb_screenshot":
                    save_path = arguments["save_path"]
                    temp_remote_path = "/sdcard/screenshot_temp.png"
                    await self.execute_adb(f'{device_flag} shell screencap -p {temp_remote_path}')
                    await self.execute_adb(f'{device_flag} pull {temp_remote_path} "{save_path}"')
                    await self.execute_adb(f'{device_flag} shell rm {temp_remote_path}')
                    result = f"Screenshot salva em: {save_path}"
                    
                elif name == "adb_push":
                    local_path = arguments["local_path"]
                    remote_path = arguments["remote_path"]
                    if not Path(local_path).is_file():
                        raise FileNotFoundError(f"Arquivo local não encontrado: {local_path}")
                    result = await self.execute_adb(f'{device_flag} push "{local_path}" "{remote_path}"')
                    
                elif name == "adb_pull":
                    remote_path = arguments["remote_path"]
                    local_path = arguments["local_path"]
                    result = await self.execute_adb(f'{device_flag} pull "{remote_path}" "{local_path}"')
                    
                elif name == "adb_input":
                    input_type = arguments["input_type"]
                    value = arguments["value"]
                    
                    input_commands = {
                        "text": f'input text "{value}"',
                        "tap": f'input tap {value}',
                        "swipe": f'input swipe {value}',
                        "keyevent": f'input keyevent {value}'
                    }
                    
                    if input_type in input_commands:
                        result = await self.execute_adb(f'{device_flag} shell {input_commands[input_type]}')
                    else:
                        raise Exception(f"Tipo de input inválido: {input_type}")
                        
                elif name == "adb_apps":
                    system_apps = arguments.get("system_apps", False)
                    flag = "" if system_apps else "-3"
                    result = await self.execute_adb(f'{device_flag} shell pm list packages {flag}')
                    
                elif name == "adb_info":
                    info_type = arguments["info_type"]
                    
                    info_commands = {
                        "battery": "dumpsys battery",
                        "version": "getprop ro.build.version.release",
                        "model": "getprop ro.product.model",
                        "memory": "cat /proc/meminfo | head -5",
                        "storage": "df /data",
                        "all": "getprop | grep -E '(ro.build.version.release|ro.product.model|ro.product.manufacturer|ro.hardware|ro.boot.hardware|ro.board.platform)'"
                    }
                    
                    if info_type in info_commands:
                        result = await self.execute_adb(f'{device_flag} shell {info_commands[info_type]}')
                    else:
                        raise Exception(f"Tipo de informação inválido: {info_type}")
                
                elif name == "adb_get_system_property":
                    property_name = arguments["property_name"]
                    result = await self.execute_adb(f'{device_flag} shell getprop {property_name}')

                elif name == "adb_list_features":
                    result = await self.execute_adb(f'{device_flag} shell pm list features')
                
                elif name == "adb_check_app_details":
                    package_name = arguments["package_name"]
                    result = await self.execute_adb(f'{device_flag} shell dumpsys package {package_name}')

                elif name == "adb_list_accounts":
                    result = await self.execute_adb(f'{device_flag} shell dumpsys account')
                
                elif name == "adb_network_info":
                    result = await self.execute_adb(f'{device_flag} shell dumpsys connectivity')
                
                elif name == "adb_network_telephony":
                    result = await self.execute_adb(f'{device_flag} shell dumpsys telephony.registry')
                
                elif name == "adb_network_wifi":
                    result = await self.execute_adb(f'{device_flag} shell dumpsys wifi')
                
                elif name == "adb_running_processes":
                    result = await self.execute_adb(f'{device_flag} shell ps -A')

                elif name == "adb_screen_resolution":
                    result = await self.execute_adb(f'{device_flag} shell wm size')
                
                elif name == "adb_query_content_provider":
                    # Chama a nova função auxiliar para Content Providers
                    result = await self._execute_aux_app_query(device_flag, arguments)
                    
                else:
                    raise Exception(f"Ferramenta desconhecida: {name}")

                return [types.TextContent(type="text", text=result or "Comando executado com sucesso")]

            except Exception as e:
                error_msg = f"Erro: {str(e)}"
                return [types.TextContent(type="text", text=error_msg)]

    async def run(self):
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="adb-mcp-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

async def main():
    """Função principal"""
    server = ADBMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())