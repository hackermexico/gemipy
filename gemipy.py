#!/usr/bin/env python3

import argparse
import sys
import os
import time
import threading
import json
import readline
import importlib.util
from datetime import datetime
from pathlib import Path

# --- Verificar dependencias ---
def verificar_dependencias():
    dependencias = {
        'google.generativeai': 'google-generativeai',
        'colorama': 'colorama'
    }
    
    faltantes = []
    for modulo, paquete in dependencias.items():
        if importlib.util.find_spec(modulo) is None:
            faltantes.append(paquete)
    
    if faltantes:
        print(f"Faltan dependencias: {', '.join(faltantes)}")
        print("Instala con: pip install --user " + " ".join(faltantes))
        sys.exit(1)

verificar_dependencias()

# --- Importar dependencias ---
import google.generativeai as genai
from colorama import init, Fore, Style

# --- Inicializar Colorama ---
init(autoreset=True)

# --- Colores ---
C_TITULO = Fore.MAGENTA + Style.BRIGHT
C_VERDE = Fore.GREEN + Style.BRIGHT
C_CIAN = Fore.CYAN + Style.BRIGHT
C_AMARILLO = Fore.YELLOW + Style.BRIGHT
C_ROJO = Fore.RED + Style.BRIGHT
C_AZUL = Fore.BLUE + Style.BRIGHT
C_RESET = Style.RESET_ALL

# --- Archivos de configuración ---
HISTORIAL_FILE = Path.home() / ".gemipy_historial.json"
CONFIG_FILE = Path.home() / ".gemipy_config.json"

# --- Clase Spinner ---
class Spinner:
    def __init__(self, mensaje="Procesando...", demora=0.1):
        self.spinner_running = True
        self.spinner_thread = threading.Thread(target=self._girar, args=(mensaje, demora))
        self.demora = demora
        self.mensaje = mensaje

    def _girar(self, mensaje, demora):
        simbolos = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        i = 0
        while self.spinner_running:
            sys.stdout.write(f"\r{C_AMARILLO}{mensaje} {simbolos[i % len(simbolos)]}{C_RESET}")
            sys.stdout.flush()
            time.sleep(demora)
            i += 1
        sys.stdout.write(f"\r{' ' * (len(mensaje) + 5)}\r")
        sys.stdout.flush()

    def empezar(self):
        self.spinner_thread.start()

    def parar(self):
        self.spinner_running = False
        self.spinner_thread.join()

# --- Gestor de Historial ---
class GestorHistorial:
    def __init__(self):
        self.historial = self.cargar_historial()
        self.config = self.cargar_config()
        
    def cargar_historial(self):
        try:
            if HISTORIAL_FILE.exists():
                with open(HISTORIAL_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {"conversaciones": [], "actual": []}
    
    def cargar_config(self):
        config_default = {
            "max_historial": 10,
            "usar_contexto": True,
            "temperatura": 0.7,
            "modelo": "gemini-1.5-flash"
        }
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return {**config_default, **json.load(f)}
        except:
            pass
        return config_default
    
    def guardar_historial(self):
        try:
            with open(HISTORIAL_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.historial, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def guardar_config(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def agregar_mensaje(self, rol, contenido):
        mensaje = {
            "rol": rol,
            "contenido": contenido,
            "timestamp": datetime.now().isoformat()
        }
        self.historial["actual"].append(mensaje)
        if len(self.historial["actual"]) > 20:
            self.historial["actual"] = self.historial["actual"][-20:]
        self.guardar_historial()
    
    def guardar_conversacion(self, titulo=""):
        if not self.historial["actual"]:
            return
        
        conversacion = {
            "id": len(self.historial["conversaciones"]) + 1,
            "titulo": titulo or f"Conversación {len(self.historial['conversaciones']) + 1}",
            "mensajes": self.historial["actual"].copy(),
            "fecha": datetime.now().isoformat()
        }
        
        self.historial["conversaciones"].append(conversacion)
        if len(self.historial["conversaciones"]) > self.config["max_historial"]:
            self.historial["conversaciones"] = self.historial["conversaciones"][-self.config["max_historial"]:]
        
        self.historial["actual"] = []
        self.guardar_historial()
    
    def obtener_contexto(self):
        if not self.config["usar_contexto"] or not self.historial["actual"]:
            return ""
        
        contexto = "\nContexto previo:\n"
        for msg in self.historial["actual"][-3:]:
            rol = "Usuario" if msg["rol"] == "user" else "Asistente"
            contexto += f"{rol}: {msg['contenido']}\n"
        return contexto

# --- Funciones de utilidad ---
def efecto_escritura(texto, delay=0.01):
    for caracter in texto:
        sys.stdout.write(caracter)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')

def imprimir_banner():
    banner = f"""
{C_TITULO}    ██████╗ ███████╗███╗   ███╗██╗██████╗ ██╗   ██╗
{C_TITULO}   ██╔════╝ ██╔════╝████╗ ████║██║██╔══██╗╚██╗ ██╔╝
{C_TITULO}   ██║  ███╗█████╗  ██╔████╔██║██║██████╔╝ ╚████╔╝ 
{C_TITULO}   ██║   ██║██╔══╝  ██║╚██╔╝██║██║██╔═══╝   ╚██╔╝  
{C_TITULO}   ╚██████╔╝███████╗██║ ╚═╝ ██║██║██║        ██║   
{C_TITULO}    ╚═════╝ ╚══════╝╚═╝     ╚═╝╚═╝╚═╝        ╚═╝   
{C_CIAN}
    """
    print(banner)
    print(f"{C_AMARILLO}{'-'*60}")
    print(f"{C_CIAN}>> Estado: {C_VERDE}Conectado a Gemini")
    print(f"{C_CIAN}>> Historial: {C_VERDE}{len(gestor_historial.historial['conversaciones'])} conversaciones")
    print(f"{C_CIAN}>> Modelo: {C_VERDE}{gestor_historial.config['modelo']}")
    print(f"{C_AMARILLO}{'-'*60}")
    print(f"{C_VERDE}Comandos: /help, /hist, /save, /config, /exit")
    print(f"{C_AMARILLO}{'-'*60}\n")

def mostrar_ayuda():
    help_text = f"""
{C_AZUL}╔══════════════════════════════════════════════════════════════╗
{C_AZUL}║                       AYUDA DE GEMIPY                       ║
{C_AZUL}╚══════════════════════════════════════════════════════════════╝

{C_CIAN}Comandos:
{C_VERDE}  /help      {C_CIAN}- Mostrar ayuda
{C_VERDE}  /hist      {C_CIAN}- Ver historial
{C_VERDE}  /save      {C_CIAN}- Guardar conversación
{C_VERDE}  /config    {C_CIAN}- Configurar
{C_VERDE}  /clear     {C_CIAN}- Limpiar pantalla
{C_VERDE}  /exit      {C_CIAN}- Salir

{C_CIAN}Características:
{C_VERDE}  • Historial persistente
{C_VERDE}  • Contexto de conversación
{C_VERDE}  • Múltiples modelos
"""
    efecto_escritura(help_text)

def mostrar_historial():
    if not gestor_historial.historial["conversaciones"]:
        print(f"{C_AMARILLO}No hay conversaciones guardadas.{C_RESET}")
        return
    
    print(f"\n{C_AZUL}╔══════════════════════════════════════════════════════════════╗")
    print(f"{C_AZUL}║                    HISTORIAL DE CHATS                    ║")
    print(f"{C_AZUL}╚══════════════════════════════════════════════════════════════╝{C_RESET}")
    
    for conv in gestor_historial.historial["conversaciones"]:
        fecha = datetime.fromisoformat(conv["fecha"]).strftime("%d/%m %H:%M")
        print(f"{C_CIAN}[{conv['id']}] {C_VERDE}{fecha} {C_CIAN}- {conv['titulo'][:40]}{C_RESET}")
    
    print(f"\n{C_AMARILLO}Usa '/load <id>' para cargar una conversación.{C_RESET}")

def cargar_conversacion(id_conv):
    try:
        id_conv = int(id_conv)
        for conv in gestor_historial.historial["conversaciones"]:
            if conv["id"] == id_conv:
                gestor_historial.historial["actual"] = conv["mensajes"].copy()
                print(f"{C_VERDE}Conversación {id_conv} cargada.{C_RESET}")
                return True
        print(f"{C_ROJO}No se encontró la conversación {id_conv}.{C_RESET}")
    except ValueError:
        print(f"{C_ROJO}ID inválido.{C_RESET}")
    return False

def mostrar_config():
    print(f"\n{C_AZUL}╔══════════════════════════════════════════════════════════════╗")
    print(f"{C_AZUL}║                     CONFIGURACIÓN                      ║")
    print(f"{C_AZUL}╚══════════════════════════════════════════════════════════════╝{C_RESET}")
    
    for key, value in gestor_historial.config.items():
        print(f"{C_CIAN}{key:15} {C_VERDE}{value}{C_RESET}")
    
    print(f"\n{C_AMARILLO}Usa '/config <clave> <valor>' para modificar.{C_RESET}")

def modificar_config(clave, valor):
    if clave not in gestor_historial.config:
        print(f"{C_ROJO}Clave inválida: {clave}{C_RESET}")
        return False
    
    try:
        if clave in ["max_historial"]:
            valor = int(valor)
        elif clave in ["temperatura"]:
            valor = float(valor)
        elif clave in ["usar_contexto"]:
            valor = valor.lower() in ["true", "1", "yes", "si"]
        
        gestor_historial.config[clave] = valor
        gestor_historial.guardar_config()
        print(f"{C_VERDE}Config actualizada: {clave} = {valor}{C_RESET}")
        return True
    except ValueError:
        print(f"{C_ROJO}Valor inválido para {clave}{C_RESET}")
        return False

# --- Inicializar gestor ---
gestor_historial = GestorHistorial()

# --- Consulta a Gemini ---
def consultar_gemini(prompt: str) -> str:
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return f"{C_ROJO}Error: No hay API Key. Usa: export GOOGLE_API_KEY='tu_key'"
        
        genai.configure(api_key=api_key)
        
        contexto = gestor_historial.obtener_contexto()
        prompt_completo = f"{contexto}\n\nNueva consulta: {prompt}"
        
        generation_config = {
            "temperature": gestor_historial.config["temperatura"],
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048,
        }
        
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        
        model = genai.GenerativeModel(
            model_name=gestor_historial.config["modelo"],
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        response = model.generate_content(prompt_completo)
        return response.text

    except Exception as e:
        return f"{C_ROJO}Error: {str(e)}{C_RESET}"

# --- Función principal ---
def main():
    parser = argparse.ArgumentParser(description="Terminal GEMIPY con historial")
    parser.add_argument("prompt", nargs="?", default=None, help="Prompt directo")
    args = parser.parse_args()
    
    limpiar_pantalla()
    imprimir_banner()
    
    # Configurar historial de inputs
    try:
        readline.read_history_file(str(Path.home() / ".gemipy_input_history"))
    except:
        pass
    
    if args.prompt:
        # Modo directo
        spinner = Spinner(mensaje="Procesando...")
        spinner.empezar()
        respuesta = consultar_gemini(args.prompt)
        spinner.parar()
        print(f"\n{C_CIAN}>> RESPUESTA:{C_RESET}\n")
        efecto_escritura(respuesta)
        
        gestor_historial.agregar_mensaje("user", args.prompt)
        gestor_historial.agregar_mensaje("assistant", respuesta)
    else:
        # Modo interactivo
        try:
            while True:
                try:
                    prompt_usuario = input(f"{C_VERDE}gemipy{C_CIAN}@{C_AZUL}user{C_CIAN}:~{C_RESET}$ ")
                    readline.write_history_file(str(Path.home() / ".gemipy_input_history"))
                except EOFError:
                    print(f"\n{C_AMARILLO}Saliendo...{C_RESET}")
                    break
                
                comando = prompt_usuario.strip()
                if not comando:
                    continue
                
                # Comandos especiales
                if comando.startswith('/'):
                    partes = comando[1:].split()
                    cmd = partes[0].lower() if partes else ""
                    
                    if cmd in ["exit", "quit", "salir"]:
                        print(f"\n{C_AMARILLO}¡Hasta luego!{C_RESET}")
                        break
                    
                    elif cmd in ["clear", "limpiar"]:
                        limpiar_pantalla()
                        imprimir_banner()
                    
                    elif cmd in ["hist", "historial"]:
                        mostrar_historial()
                    
                    elif cmd == "load" and len(partes) > 1:
                        cargar_conversacion(partes[1])
                    
                    elif cmd == "save":
                        titulo = " ".join(partes[1:]) if len(partes) > 1 else ""
                        gestor_historial.guardar_conversacion(titulo)
                        print(f"{C_VERDE}Conversación guardada.{C_RESET}")
                    
                    elif cmd == "config":
                        if len(partes) == 1:
                            mostrar_config()
                        elif len(partes) == 3:
                            modificar_config(partes[1], partes[2])
                        else:
                            print(f"{C_ROJO}Uso: /config <clave> <valor>{C_RESET}")
                    
                    elif cmd in ["help", "ayuda"]:
                        mostrar_ayuda()
                    
                    else:
                        print(f"{C_ROJO}Comando desconocido: /{cmd}{C_RESET}")
                    
                    continue
                
                # Consulta normal
                spinner = Spinner(mensaje="Pensando...")
                spinner.empezar()
                respuesta = consultar_gemini(prompt_usuario)
                spinner.parar()
                
                gestor_historial.agregar_mensaje("user", prompt_usuario)
                gestor_historial.agregar_mensaje("assistant", respuesta)
                
                print(f"\n{C_CIAN}>> RESPUESTA:{C_RESET}\n")
                efecto_escritura(respuesta)
                print()

        except KeyboardInterrupt:
            print(f"\n\n{C_AMARILLO}Interrupción por usuario.{C_RESET}")
        finally:
            gestor_historial.guardar_historial()
            try:
                readline.write_history_file(str(Path.home() / ".gemipy_input_history"))
            except:
                pass

if __name__ == "__main__":
    main()
