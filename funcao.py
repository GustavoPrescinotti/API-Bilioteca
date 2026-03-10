import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
def verificar_senha(senha):

    if len(senha) < 10:
        return "A senha deve ter no mínimo 10 caracteres"

    tem_maiuscula = False
    tem_minuscula = False
    tem_numero = False
    tem_simbolo = False
    simbolos = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    for letra in senha:
        if letra.isupper():
            tem_maiuscula = True
        elif letra.islower():
            tem_minuscula = True
        elif letra.isdigit():
            tem_numero = True
        elif letra in simbolos:
            tem_simbolo = True

    if not tem_maiuscula: return "Falta uma letra maiúscula"
    if not tem_minuscula: return "Falta uma letra minúscula"
    if not tem_numero:    return "Falta um número"
    if not tem_simbolo:   return "Falta um símbolo especial"

    return None


def enviando_email(destinario, assunto, mensagem):
    user = 'loomasistema@gmail.com'
    senha = 'hmmghiewzrhpraus'

    msg = MIMEText(mensagem)
    msg['Subject'] = assunto  # Corrigido: Subject
    msg['From'] = user
    msg['To'] = destinario

    try:
        # Corrigido: smtp.gmail.com
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(user, senha)
        server.send_message(msg)
        server.quit()
        print(f"E-mail enviado com sucesso para {destinario}!")
    except Exception as e:
        print(f"Erro ao enviar o e-mail em segundo plano: {e}")