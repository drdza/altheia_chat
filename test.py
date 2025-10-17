import requests

API_KEY = "change-me"
API_URL = "http://127.0.0.1:8000"

def ask(question: str):
    url = f"{API_URL}/chat"
    payload = {"question": question}
    resp = requests.post(url, json=payload)
    if resp.status_code != 200:
        print("Error:", resp.status_code, resp.text)
        return
    data = resp.json()
    print(f"Q: {question}")
    print(f"A: {data['answer']}\n")


def ingest(doc_id, text):
    url = f"{API_URL}/admin/ingest/raw-text"
    params = {"doc_id": doc_id, "text": text}
    headers = {"X-Api-Key": API_KEY}
    r = requests.post(url, params=params, headers=headers)
    print("Status:", r.status_code, "->", r.json())

def ingest_file(doc_id: str, filepath: str):
    url = f"{API_URL}/admin/ingest/file"
    headers = {"X-Api-Key": API_KEY}
    files = {
        "file": open(filepath, "rb")
    }
    data = {
        "doc_id": doc_id
    }
    r = requests.post(url, headers=headers, files=files, data=data)
    print("Status:", r.status_code, "->", r.json())


def rephrase(text: str, style: str = ""):
    url = f"{API_URL}/rephrase/"
    payload = {"text": text, "style": style}
    resp = requests.post(url, json=payload)

    data = resp.json()
    print(f"Q: {text}")
    print(f"A: {data['rephrased']}\n")
    



if __name__ == "__main__":
    while True:    
        option = int(input(
    """
    --------- Opciones Disponibles --------
    1.- Hacer una pregunta
    2.- Reformular
    3.- Inyectar a la base de conocimiento
    4.- Ingestar documento (Word, PDF, Texto, Markdown, Excel)    
    0.- Salir
    ---------------------------------------
    Elija una opción: """))            
        match option:
            case 0:
                exit()
            case 1:
                user = input("\n¿Cual es tu pregunta? ")
                ask(user)
            case 2:
                text = input("\nInstrucción : ")
                style = input("\nEstilo (Breve, Conciso, Agresivo, Profesional, etc.): ")
                rephrase(text, style)
            case 3:
                id_ingest = input("ID de tu contexto: ")
                txt_ingest = input("Contexto: ")
                ingest(id_ingest, txt_ingest)
            case 4:
                id_ingest = input("ID del documento: ")
                filepath = input("Ruta completa al archivo: ")
                ingest_file(id_ingest, filepath)


