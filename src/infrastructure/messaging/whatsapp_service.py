import requests
import time

# Configuración del servidor WAHA (WhatsApp HTTP API) local
# Por defecto WAHA corre en el puerto 3000
WAHA_BASE_URL = "http://localhost:3000"

class WhatsAppService:
    @staticmethod
    def checar_estado() -> bool:
        """Verifica si el servidor local de WAHA está corriendo y el celular conectado."""
        try:
            # Revisa el estado de la sesión predeterminada ('default')
            response = requests.get(f"{WAHA_BASE_URL}/api/sessions/default", timeout=5)
            if response.status_code == 200:
                data = response.json()
                # WAHA devuelve status 'WORKING' cuando el celular está sincronizado correctamente
                return data.get("status") == "WORKING"
            return False
        except requests.exceptions.RequestException:
            return False

    @staticmethod
    def obtener_qr() -> str:
        """Obtiene la imagen del código QR en base64 si la sesión necesita escanearse."""
        try:
            response = requests.get(f"{WAHA_BASE_URL}/api/default/auth/qr", timeout=5)
            if response.status_code == 200:
                return response.json().get("qr", "")
            return ""
        except requests.exceptions.RequestException:
            return ""

    @staticmethod
    def iniciar_sesion():
        """Le pide a WAHA que levante la sesión 'default'."""
        try:
            requests.post(
                f"{WAHA_BASE_URL}/api/sessions/", 
                json={"name": "default", "config": {}},
                timeout=5
            )
        except requests.exceptions.RequestException as e:
            print(f"Error al iniciar sesión WAHA: {e}")

    @staticmethod
    def formatear_numero(numero: str) -> str:
        """Limpia el número y le agrega el sufijo oficial que requiere WhatsApp (@c.us)."""
        # Elimina espacios, guiones y el símbolo +
        limpio = "".join(filter(str.isdigit, str(numero)))
        
        # Validación básica para México (10 dígitos o 12 con código de país 52)
        if len(limpio) == 10:
            limpio = f"521{limpio}" # Agregamos el 52 y el 1 (móvil MX para WhatsApp)
        elif len(limpio) == 12 and limpio.startswith("52"):
            # A veces WA requiere el 1 después del 52 para números de México nuevos
            limpio = f"521{limpio[2:]}"
            
        return f"{limpio}@c.us"

    @staticmethod
    def enviar_mensaje(telefono: str, mensaje: str) -> bool:
        """Envía un mensaje de texto puro al teléfono indicado."""
        chat_id = WhatsAppService.formatear_numero(telefono)
        
        payload = {
            "chatId": chat_id,
            "text": mensaje,
            "session": "default"
        }
        
        try:
            print(f"   [WAHA] Enviando mensaje a {chat_id}...")
            response = requests.post(f"{WAHA_BASE_URL}/api/sendText", json=payload, timeout=10)
            if response.status_code in [200, 201]:
                print(f"   ✅ [WAHA] Mensaje enviado exitosamente.")
                return True
            else:
                print(f"   ❌ [WAHA] Error enviando mensaje: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"   ❌ [WAHA] Servidor local no responde: {e}")
            return False

# Prueba rápida manual
if __name__ == "__main__":
    print("Iniciando prueba de conexión con WAHA...")
    WhatsAppService.iniciar_sesion()
    time.sleep(2)
    
    if WhatsAppService.checar_estado():
        print("✅ Servidor WAHA conectado y celular sincronizado.")
        # Escribe aquí un teléfono real para probar (ej. 5512345678)
        WhatsAppService.enviar_mensaje("8116607645", "¡Hola Mundo desde Scalio!")
    else:
        print("❌ El servidor WAHA no está conectado o falta escanear el QR.")
        qr = WhatsAppService.obtener_qr()
        """
        si qr != "":
            Aquí se podría pintar el QR o enviar por Telegram, 
            pero por interfaz local de WAHA se puede ver en http://localhost:3000/
        """
