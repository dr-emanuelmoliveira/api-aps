import requests
import json
import re
from datetime import datetime
from pathlib import Path

# Configurações da API
API_URL = "http://localhost:8080/message/sendText/modulo-buscaiativa"
API_KEY = "281704aLJaparaiba881831412022PmpB"

class WhatsAppMessageSender:
    def __init__(self, contacts_file="contacts.json", log_file="message_log.json"):
        """
        Inicializa o enviador de mensagens
        
        Args:
            contacts_file: Arquivo JSON com contatos (padrão: contacts.json)
            log_file: Arquivo de log das mensagens (padrão: message_log.json)
        """
        self.contacts_file = contacts_file
        self.log_file = log_file
        self.log_data = []
        self.load_log()
    
    def load_log(self):
        """Carrega o log existente, se houver"""
        if Path(self.log_file).exists():
            with open(self.log_file, 'r', encoding='utf-8') as f:
                self.log_data = json.load(f)
    
    def save_log(self):
        """Salva o log em arquivo JSON"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.log_data, f, ensure_ascii=False, indent=2)
    
    def format_phone_number(self, phone):
        """
        Formata e valida número de telefone brasileiro
        Adiciona o '9' se o número estiver desatualizado
        
        Formato esperado: 55 (país) + DDD (2 dígitos) + número (8 ou 9 dígitos)
        
        Args:
            phone: Número de telefone
            
        Returns:
            Número formatado ou None se inválido
        """
        # Remove espaços, hífens e parênteses
        phone = re.sub(r'\D', '', str(phone))
        
        # Se começar com 55 (código do Brasil)
        if phone.startswith('55'):
            ddd = phone[2:4]  # 2 dígitos após 55
            numero = phone[4:]  # Resto após DDD
            
            # Valida se DDD tem 2 dígitos
            if len(ddd) != 2 or not ddd.isdigit():
                return None
            
            # Se o número tem 8 dígitos (desatualizado), adiciona 9
            if len(numero) == 8:
                numero = '9' + numero
            
            # Número deve ter 9 dígitos
            if len(numero) != 9 or not numero.isdigit():
                return None
            
            phone = '55' + ddd + numero
        else:
            return None
        
        return phone
    
    def send_message(self, phone, name, message_text):
        """
        Envia mensagem via Evolution API
        
        Args:
            phone: Número de telefone formatado
            name: Nome da pessoa
            message_text: Texto da mensagem
            
        Returns:
            Dicionário com resultado do envio
        """
        payload = {
            "number": phone,
            "textMessage": {"text": message_text},
            "delay": 100,
            "quoted": {},
            "linkPreview": False,
            "mentioned": []
        }
        
        headers = {
            "apikey": API_KEY,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(API_URL, json=payload, headers=headers, timeout=10)
            
            # HTTP 200 e 201 são sucesso
            if response.status_code in [200, 201]:
                response_data = response.json()
                return {
                    "success": True,
                    "message_id": response_data.get("key", {}).get("id"),
                    "status": response_data.get("status"),
                    "response": response_data
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "response": response.text
                }
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout - API não respondeu"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Erro de conexão - API indisponível"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def process_contacts(self, message_template):
        """
        Processa todos os contatos e envia mensagens
        
        Args:
            message_template: Template da mensagem com {nome} como placeholder
                             Exemplo: "Olá {nome}, bem-vindo!"
        """
        try:
            with open(self.contacts_file, 'r', encoding='utf-8') as f:
                contacts = json.load(f)
        except FileNotFoundError:
            print(f"❌ Arquivo {self.contacts_file} não encontrado!")
            return
        except json.JSONDecodeError:
            print(f"❌ Erro ao ler JSON em {self.contacts_file}")
            return
        
        if not isinstance(contacts, list):
            print("❌ JSON deve ser uma lista de contatos")
            return
        
        total = len(contacts)
        success_count = 0
        error_count = 0
        
        print(f"\n📱 Iniciando envio para {total} contatos...")
        print("=" * 60)
        
        for idx, contact in enumerate(contacts, 1):
            # Validação básica do contato
            if not isinstance(contact, dict):
                self.log_entry(None, None, "error", "Contato em formato inválido")
                error_count += 1
                continue
            
            nome = contact.get("nome", "").strip()
            numero = contact.get("numero", "").strip()
            
            if not nome or not numero:
                self.log_entry(nome, numero, "error", "Nome ou número faltando")
                error_count += 1
                continue
            
            # Formata número
            phone_formatted = self.format_phone_number(numero)
            if not phone_formatted:
                self.log_entry(nome, numero, "error", f"Número inválido: {numero}")
                error_count += 1
                continue
            
            # Personaliza mensagem
            try:
                message = message_template.format(nome=nome)
            except KeyError as e:
                message = message_template
            
            # Envia mensagem
            print(f"\n[{idx}/{total}] Enviando para {nome}...")
            result = self.send_message(phone_formatted, nome, message)
            
            if result["success"]:
                print(f"✅ Sucesso! ID: {result['message_id']}")
                self.log_entry(nome, phone_formatted, "success", 
                              f"Mensagem enviada. ID: {result['message_id']}")
                success_count += 1
            else:
                print(f"❌ Erro: {result['error']}")
                self.log_entry(nome, phone_formatted, "error", result['error'])
                error_count += 1
        
        # Resumo final
        print("\n" + "=" * 60)
        print(f"\n📊 RESUMO DO ENVIO:")
        print(f"   ✅ Sucesso: {success_count}/{total}")
        print(f"   ❌ Erros: {error_count}/{total}")
        print(f"\n📝 Log salvo em: {self.log_file}\n")
        
        self.save_log()
    
    def log_entry(self, nome, numero, status, mensagem):
        """
        Registra uma entrada no log
        
        Args:
            nome: Nome da pessoa
            numero: Número de telefone
            status: 'success' ou 'error'
            mensagem: Detalhes do resultado
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "nome": nome,
            "numero": numero,
            "status": status,
            "mensagem": mensagem
        }
        self.log_data.append(entry)


def main():
    """Função principal"""
    
    # Exemplo de uso
    sender = WhatsAppMessageSender(
        contacts_file="contacts.json",
        log_file="message_log.json"
    )
    
    # Template de mensagem com personalização
    message_template = "Olá {nome}, bem-vindo ao nosso serviço! 👋"
    
    # Processa e envia mensagens
    sender.process_contacts(message_template)


if __name__ == "__main__":
    main()
