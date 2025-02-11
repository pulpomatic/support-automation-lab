import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class OpenAIAgent:
    def __init__(self):
        """
        Inicializa el agente con la API de OpenAI
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API_KEY no encontrada en el archivo .env")
        
        self.client = OpenAI(api_key=self.api_key)

    def generate_response(self, user_input: str) -> str:
        """Genera respuesta usando la API de OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": user_input.strip()}],
                max_tokens=100
            )
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error en la API: {str(e)}"

    def run(self):
        """Ejecuta el agente en modo interactivo"""
        print("\nAgent OpenAI iniciado. Escribe 'exit' para salir\n")
        while True:
            user_input = input("Tú: ")
            if user_input.lower() == 'exit':
                break
            
            response = self.generate_response(user_input)
            print(f"\nAgent: {response}\n")

if __name__ == "__main__":
    agent = OpenAIAgent()
    agent.run()