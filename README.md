# 📈 SmartInvestor

SmartInvestor é uma aplicação para monitoramento de ativos financeiros. Os usuários podem favoritar ativos e definir limites de preço, recebendo notificações quando esses limites forem atingidos.
🚀 Funcionalidades

    Painel Administrativo do Django: Gerenciamento de ativos e usuários diretamente pelo Django Admin.
    Monitoramento de Ativos: Atualização automática dos preços dos ativos.
    Notificações por E-mail: Envio automático de alertas quando o preço de um ativo atinge o limite definido pelo usuário.
    Integração com BRAPI: Obtém os preços dos ativos em tempo real.

🛠 Tecnologias Utilizadas

    Backend: Django + Django Admin
    Banco de Dados: SQLite
    Integração de Dados: API BRAPI
    Gerenciamento de Dependências: pip e venv

🔧 Configuração e Execução
1️⃣ Clone o repositório

git clone https://github.com/GabeMed/smart-investor.git
cd smart-investor

2️⃣ Crie e ative um ambiente virtual

python3 -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate

3️⃣ Instale as dependências

pip install -r requirements.txt

4️⃣ Configure as variáveis de ambiente

Crie um arquivo .env na raiz do projeto e adicione:

BRAPI_KEY=sua-chave-brapi
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-de-app
EMAIL_TEST=seu-email-de-teste@gmail.com

5️⃣ Configure o banco de dados

python manage.py makemigrations
python manage.py migrate

6️⃣ Crie um superusuário para acessar o painel do admin

python manage.py createsuperuser

Siga as instruções para definir um nome de usuário e senha.
7️⃣ Execute o servidor Django

python manage.py runserver

Agora, acesse o painel em:
🔗 http://127.0.0.1:8000/admin

Faça login com as credenciais do superusuário e gerencie os ativos e usuários diretamente pelo painel administrativo.
📬 Testando Envio de E-mails

O envio de notificações pode ser testado manualmente:

python manage.py shell

E dentro do shell do Django:

from django.core.mail import send_mail

send_mail(
    'Teste de Alerta',
    'Seu ativo atingiu o limite de preço!',
    'seu-email@gmail.com',
    ['email-destino@gmail.com'],
    fail_silently=False,
)

Se configurado corretamente, você receberá um e-mail de teste.
