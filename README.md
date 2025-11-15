# KartManagementSQL

Grupo:
Matheus Ferreira de Freitas 22.125.085-5
Henrique Hodel Babler 22.125.076-4

---



## Descrição do Projeto:

### Descrição do Professor:

O objetivo deste projeto é estudar o armazenamento de dados em diversos bancos tendo o uso do dado pela aplicação como critério de escolha para o tipo de banco que será usado.
O tema do projeto é livre, porém a implementação deve seguir o seguinte modelo:
graph LR

```mermaid
graph LR
    S1 <--> S2
    S2 <--> RDB
    S2 <--> DB1
    S2 <--> DB2
```

em que:
- RDB é um banco relacional;
- DB1 e DB2 são bancos que não podem ser relacionais (NoSQL) e não podem ser o mesmo banco;
- S1: serviço que deve faz requisições ao serviço S2. Estas requisições podem conter tanto dados fictícios que serão armazenados no bancos como requisições de dados que estão nos bancos e que devem ser retornadas. Os dados fictícios gerados devem ser de pelo menos 3 tipos diferentes, sendo que cada um deles será armazenado em um banco diferente. O serviço S1 deve armazenar todos as respostas de S2 junto com as requisições realizadas para verificação do funcionamento de S1;
- S2: serviço(s) que receberá as requisições de S1 e devem realizar o armazenamento ou busca dos dados nos respectivos bancos. Esta parte pode ser implementada como apenas 1 serviço que lê todos os tipos de mensagem ou como diversos serviços que são responsáveis por tipos de dados diferentes;

---



# Mario Kart Multi DB – Projeto de Banco de Dados

Projeto feito em Python usando três bancos de dados diferentes para simular um "Nintendo Switch" rodando Mario Kart:

- DB1 – MongoDB: catálogo de peças e pistas  
- RDB – PostgreSQL: usuários, corridas e classificação  
- DB2 – Neo4j: grafo das corridas para análise de relacionamentos  
- S1 – Aplicação de terminal (cliente)  
- S2 – API em FastAPI (servidor) que conversa com os bancos  

--------------------------------------------------
## 1. Visão geral dos bancos

### DB1 – MongoDB (Catálogo)

Armazena os dados "de catálogo" do jogo, que são naturalmente documentos:

- Personagens  
- Karts  
- Rodas  
- Asas-deltas  
- Pistas  

Motivo de usar MongoDB:

- Catálogo é flexível, pode mudar atributos com o tempo  
- Estrutura de documento combina bem com listas de itens  
- Leitura rápida para montar o catálogo que o jogador escolhe antes da corrida  

Scripts relacionados:

- `Sistema2/Popular_Bancos/PopDB1.py` – popula o catálogo  
- `Sistema2/Apagar_Bancos/UnpopDB1.py` – limpa o catálogo  

--------------------------------------------------
### RDB – PostgreSQL (Relacional)

É o banco principal para dados tradicionais de sistema:

- Usuários (login, senha, e-mail)  
- Corridas registradas  
- Classificação e pontos por corrida  

Motivo de usar PostgreSQL:

- Consistência forte para login e senhas  
- Ideal para consultas relacionais (joins, relatórios, ranking)  
- Ferramenta padrão de mercado para sistemas transacionais  

Scripts relacionados:

- `Sistema2/Popular_Bancos/PopRDB.py` – popula usuários e dados iniciais  
- `Sistema2/Apagar_Bancos/UnpopRDB.py` – limpa os dados desse banco  
- `Sistema2/migrate_pwd_plain.py` – script auxiliar para migração de senhas, se precisar ajustar dados antigos  

--------------------------------------------------
### DB2 – Neo4j (Grafo)

Armazena a estrutura das corridas em forma de grafo:

Nós principais:

- `Runner` – o corredor (associado a um usuário)  
- `Race` – a corrida em si  
- `Character`, `Kart`, `Wheel`, `Glider`, `Track`  
- `Position` – posição final daquele corredor na corrida  

Relações (exemplos):

- `(Runner) -[:CHOSE_CHARACTER]-> (Character)`  
- `(Runner) -[:CHOSE_KART]-> (Kart)`  
- `(Runner) -[:CHOSE_WHEEL]-> (Wheel)`  
- `(Runner) -[:CHOSE_GLIDER]-> (Glider)`  
- `(Race) -[:ON_TRACK]-> (Track)`  
- `(Position) -[:OF_RUNNER]-> (Runner)`  
- `(Position) -[:IN_RACE]-> (Race)`  
- `(Runner) -[:PARTICIPATED_IN]-> (Race)`  

Motivo de usar Neo4j:

- Permite analisar as corridas como um grafo  
- Facilita perguntas como: “quem usa mais tal kart?”, “quais combinações aparecem juntas?”, “como cada jogador se conecta a itens, pistas e resultados?”  
- Mostra que o mesmo domínio pode ser visto de forma relacional (PostgreSQL) e também como grafo (Neo4j)  

Scripts relacionados:

- `Sistema2/Popular_Bancos/PopDB2.py` – cria algumas corridas de exemplo no grafo  
- `Sistema2/Apagar_Bancos/UnpopDB2.py` – apaga nós e relações do grafo ligados ao projeto  

--------------------------------------------------
## 2. Visão geral de S1 e S2

### S1 – Sistema1 (Cliente de Terminal)

Pasta: `Sistema1/`

Arquivos principais:

- `Main.py`  
  - Interface de terminal estilo Nintendo Switch.  
  - Funções principais:  
    - SignUp (Cadastro) – chama a API S2 para criar usuário.  
    - Login – autentica na S2.  
    - Jogar Mario Kart (Online) – chama S2 para:  
      - Buscar catálogo no Mongo (DB1).  
      - Criar corrida no PostgreSQL e no Neo4j.  
      - Exibir resultados / relatórios no terminal.  

- `s1_report.py`  
  - Funções auxiliares para imprimir relatórios e organizar a saída no terminal.  
  - Formata respostas da API S2 para deixar legível para o usuário.  

S1 nunca acessa os bancos diretamente: tudo acontece via chamadas HTTP para a S2.  

--------------------------------------------------
### S2 – Sistema2 (API FastAPI)

Pasta: `Sistema2/`

Responsável por:

- Servir a API REST (FastAPI) na porta 8000  
- Conectar aos três bancos (MongoDB, PostgreSQL, Neo4j)  
- Fornecer endpoints como:  
  - `/health` – mostra se cada banco está conectado (`pg`, `mongo`, `neo4j`)  
  - `/auth/signup` – cria novo usuário  
  - `/auth/login` – autentica usuário  
  - `/db1/catalog` – retorna catálogo de personagens, karts, etc.  
  - `/race/start` – cria uma corrida utilizando o catálogo e registra em:  
    - DB1 (catálogo já existente)  
    - RDB (corrida / classificação)  
    - DB2 (grafo da corrida)  

--------------------------------------------------
## 3. Estrutura de pastas e arquivos

```bash
ProjetosemPython/
├── Sistema1/
│   ├── Main.py          # cliente de terminal (Nintendo Switch fake)
│   ├── s1_report.py     # funções de relatório e formatação de saída
│   └── __pycache__/     # arquivos .pyc gerados pelo Python, podem ser ignorados
│
└── Sistema2/
    ├── .dockerignore         # arquivos que não vão para a imagem Docker
    ├── .env                  # variáveis de ambiente, credenciais dos bancos
    ├── Dockerfile            # define como construir a imagem Docker da API S2
    │
    ├── Popular_Bancos/
    │   ├── PopDB1.py         # popula o MongoDB (catálogo)
    │   ├── PopDB2.py         # popula o Neo4j (corridas de exemplo)
    │   ├── PopRDB.py         # popula o PostgreSQL (usuários e dados iniciais)
    │   └── seed_all.py       # orquestra a chamada dos scripts acima
    │
    ├── Apagar_Bancos/
    │   ├── UnpopDB1.py       # limpa o MongoDB (catálogo)
    │   ├── UnpopDB2.py       # limpa o Neo4j (grafo)
    │   ├── UnpopRDB.py       # limpa o PostgreSQL (dados do projeto)
    │   └── clean_all.py      # orquestra a limpeza de todos os bancos
    │
    ├── __init__.py           # marca a pasta como pacote Python
    ├── api.py                # aplicação FastAPI, define os endpoints
    ├── check_connections.py  # testa conexões com os 3 bancos
    ├── config.py             # carrega configs e variáveis de ambiente
    ├── docker-compose.yml    # sobe a API S2 em container Docker
    ├── migrate_pwd_plain.py  # script auxiliar para normalizar senhas no RDB
    ├── requirements.txt      # dependências Python da S2
    │
    ├── .devcontainer/
    │   └── devcontainer.json # config do VS Code para dev container
    │
    ├── .vscode/
    │   ├── launch.json       # config de debug do VS Code
    │   └── tasks.json        # tarefas automatizadas no VS Code
    │
    └── db/
        └── __pycache__/      # restos de builds anteriores, podem ser ignorados
```

---

## 4 Pré-requisitos (testado no Pop!_OS)

No Pop!_OS (base Ubuntu), é necessário:

Python 3.10 ou superior

pip (gerenciador de pacotes do Python)

Docker

Docker Compose (ou docker compose já integrado no Docker recente)

Exemplo de instalação:

sudo apt update
sudo apt install -y python3 python3-pip
sudo apt install -y docker.io

# Permitir seu usuário usar Docker sem sudo (precisa relogar depois)
sudo usermod -aG docker $USER

# Se precisar do docker-compose clássico
sudo apt install -y docker-compose




---

## 5. Configuração do ambiente (.env)

Dentro de Sistema2/ existe o arquivo .env.

Ele precisa ter as variáveis de conexão dos três bancos. Exemplo:

# PostgreSQL (RDB)
PG_HOST=...
PG_PORT=...
PG_DB=...
PG_USER=...
PG_PASSWORD=...

# MongoDB (DB1)
MONGO_URI=mongodb+srv://usuario:senha@cluster0.../...

# Neo4j (DB2)
NEO4J_URI=neo4j+s://....
NEO4J_USER=neo4j
NEO4J_PASSWORD=...
NEO4J_DATABASE=neo4j

# Outras configs
JWT_SECRET=algumseguroaqui
JWT_ALGORITHM=HS256

No ambiente real, esses valores apontam para o Supabase (Postgres), Mongo Atlas e Neo4j utilizados no projeto.
O importante é mostrar que todas as conexões são parametrizadas via .env.


---


## 6. Como rodar o projeto (ordem recomendada)
### 6.1. Clonar / abrir o projeto
Se estiver com o zip, basta extrair. Se estiver usando git:
```bash
cd ProjetosemPython
```
--------------------------------------------------
### 6.2. Subir a API S2 com Docker
Entre na pasta do Sistema2:
```bash
cd Sistema2
```
Instalar as dependências (se quiser rodar scripts localmente, fora do container):
```bash
python3 -m pip install --user -r requirements.txt
```
Subir a API com Docker Compose:
```bash
docker compose up -d --build
```
Isso vai:
- Construir a imagem da S2 com base no `Dockerfile`
- Rodar a API na porta 8000
- Usar as variáveis de `.env` para se conectar aos três bancos
Testar o endpoint `/health`:
```bash
curl -s http://localhost:8000/health
```
Saída esperada:
```json
{"pg": true, "mongo": true, "neo4j": true}
```
--------------------------------------------------
### 6.3. Popular os bancos (DB1, RDB, DB2)
Ainda dentro de `Sistema2/`, use os scripts de popular.
**Opção 1 – Python local:**
```bash
python3 Popular_Bancos/PopDB1.py # MongoDB (catálogo)
python3 Popular_Bancos/PopRDB.py # PostgreSQL (usuários, base)
python3 Popular_Bancos/PopDB2.py # Neo4j (corridas de exemplo)
```
**Opção 2 – Rodando os scripts dentro do container da S2:**
```bash
docker compose run --rm s2 python Popular_Bancos/PopDB1.py
docker compose run --rm s2 python Popular_Bancos/PopRDB.py
docker compose run --rm s2 python Popular_Bancos/PopDB2.py
```
Se o `Popular_Bancos/seed_all.py` estiver configurado para chamar os três:
```bash
docker compose run --rm s2 python Popular_Bancos/seed_all.py
```
--------------------------------------------------
### 6.4. Rodar o cliente de terminal S1
Com a API rodando e os bancos populados, volte para a raiz e rode o cliente:
```bash
cd ../Sistema1
python3 Main.py
```
Você deve ver algo assim:
```text
Olá, seja bem-vindo ao Nintendo Switch
1. Login
2. SignUp (Cadastro)
3. Desligar Switch
Escolha:
```
Fluxo típico:
1. Fazer **SignUp (Cadastro)** – cria usuário no RDB via S2
2. Fazer **Login** – autentica pelo endpoint `/auth/login`
3. Escolher **Jogar Mario Kart (Online)** – S1 chama:
- `/db1/catalog` para listar opções de personagem, kart, rodas, etc.
- `/race/start` para registrar a corrida:
- No RDB (corridas e classificação)
- No Neo4j (grafo da corrida)
- Depois usa `s1_report.py` para mostrar o resultado formatado
--------------------------------------------------
### 6.5. Limpar os bancos (reset do projeto)
Quando quiser limpar tudo que foi inserido pelos scripts:
**Opção 1 – Python local:**
```bash
cd ../Sistema2
python3 Apagar_Bancos/UnpopDB1.py
python3 Apagar_Bancos/UnpopRDB.py
python3 Apagar_Bancos/UnpopDB2.py
```
**Opção 2 – Pelo container:**
```bash
docker compose run --rm s2 python Apagar_Bancos/UnpopDB1.py
docker compose run --rm s2 python Apagar_Bancos/UnpopRDB.py
docker compose run --rm s2 python Apagar_Bancos/UnpopDB2.py
```
Se `Apagar_Bancos/clean_all.py` estiver chamando os três:
```bash
docker compose run --rm s2 python Apagar_Bancos/clean_all.py
```
--------------------------------------------------
## 7. Resumo da apresentação

- **S1**: cliente em Python no terminal que o usuário usa diretamente.
- Simula um Nintendo Switch.
- Consome a API S2 para login, catálogo e corridas.
- **S2**: API em FastAPI.
- Conecta em três bancos diferentes.
- Mostra `/health` com o estado de `pg`, `mongo`, `neo4j`.
- Faz toda a lógica de negócio.
- **DB1 – MongoDB**: catálogo do jogo.
- **RDB – PostgreSQL**: usuários, corridas, classificação.
- **DB2 – Neo4j**: grafo das corridas.
Scripts de popular:
- `PopDB1.py` – catálogo no MongoDB
- `PopRDB.py` – usuários e base no PostgreSQL
- `PopDB2.py` – corridas de exemplo no Neo4j
Scripts de limpeza:
- `UnpopDB1.py` – limpa Mongo
- `UnpopRDB.py` – limpa PostgreSQL
- `UnpopDB2.py` – limpa Neo4j
Ordem recomendada de execução:
1. Configurar o `.env` com as credenciais dos três bancos.
2. Subir a API S2 com Docker (`docker compose up -d --build`).
3. Popular os bancos com `PopDB1`, `PopRDB` e `PopDB2` (ou `seed_all.py`).
4. Rodar o cliente S1 (`Main.py`) para usar o sistema.
5. Opcional: limpar tudo com `UnpopDB1`, `UnpopRDB`, `UnpopDB2` (ou `clean_all.py`)

