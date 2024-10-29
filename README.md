# Vamos começar
Primeira coisa é que você deve ter uma versão do python que suporta o django, estarei usando a versão 3.9

# 1 Etapa
Agora com o python instalado precisamos de um lugar para trabalhar, usaremos o VS code para isso, então, vamos começar.
Abrindo o terminal na sua pasta do projeto vamos rodar os seguintes comandos:
- Criar nosso ambiente virtual:
```
python -m venv venv
```
- Acessar o script (caso não esteja ativado scripts, veja como ativar aqui Windows: https://www.youtube.com/watch?v=mmXzYxR7s9c)
```
./venv/bin/Activate.ps1
```
- Instalar as dependências
```
pip install -r requirements.txt
```
- Criar seu banco de dados
```
python manage.py makemigrations
```
```
python manage.py migrate
```
- Criar seu super usuário
```
python manage.py createsuperuser
```
- Partir pro abraço!
```
python manage.py runserver
```
Lembre de colocar suas keys para autorizar a request para a IA.
