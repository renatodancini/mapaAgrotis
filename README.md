# Mapa Agrotis

Sistema de gerenciamento de produtos agrícolas com integração à API da Agrotis.

## Funcionalidades

- **Upload de Planilhas**: Upload de arquivos Excel (.xlsx) com dados de produtos
- **Integração com API**: Consulta automática à API da Agrotis para obter informações de produtos
- **Comparativo de Produtos**: Comparação entre dados da planilha e dados da API
- **Pesquisa IA**: Busca inteligente com fuzzy matching e pesquisa web externa
- **Gerenciamento de Configurações**: Controle de visibilidade de páginas e configurações do sistema
- **Exportação de Dados**: Exportação de resultados em formato Excel

## Tecnologias Utilizadas

- **Streamlit**: Interface web
- **Python**: Linguagem de programação
- **Pandas**: Manipulação de dados
- **SQLite**: Banco de dados local
- **RapidFuzz**: Busca fuzzy
- **Requests**: Requisições HTTP

## Instalação

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd mapaAgrotis
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
```

3. Ative o ambiente virtual:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Execução

Para executar o aplicativo:

```bash
streamlit run app_streamlit.py
```

O aplicativo estará disponível em: `http://localhost:8501`

## Estrutura do Projeto

- `app_streamlit.py`: Aplicação principal em Streamlit
- `requirements.txt`: Dependências do projeto
- `produtos.db`: Banco de dados SQLite (criado automaticamente)
- `.gitignore`: Arquivos excluídos do controle de versão

## Configuração

### Credenciais de Acesso
- **Usuário**: `renato.dancini`
- **Senha**: `Sipal@501`

### API Configuration
- **Endpoint**: `https://hom-receituariosipal.agrotis.io/int/fito/api/produtos`
- **Token**: Configurado no código da aplicação

## Uso

1. **Home**: Página principal com upload de planilhas e pesquisa
2. **Pesquisa IA**: Busca inteligente em produtos
3. **Configuração**: Gerenciamento de visibilidade de páginas (requer login)

## Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## Licença

Este projeto é privado e de uso interno da Agrotis. 