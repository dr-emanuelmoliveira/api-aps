import requests

url = "http://localhost:8080/message/sendText/modulo-buscaiativa"

payload = {
    "number": "5537984198778",
    "textMessage": { "text": "Testando 123" },
    "delay": 123,
    "quoted": {},
    "linkPreview": True,
    "mentioned": ["<string>"]
}
headers = {
    "apikey": "281704aLJaparaiba881831412022PmpB",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.text)
