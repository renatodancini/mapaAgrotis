# Configuração da API do Bing Search

## Problema Identificado

O campo de pesquisa com IA não está funcionando para pesquisas na internet porque a API do Bing Search não está configurada.

## Solução

### 1. Obter uma Chave da API do Bing Search

1. **Acesse o Microsoft Azure Portal**:
   - Vá para [portal.azure.com](https://portal.azure.com)
   - Faça login com sua conta Microsoft

2. **Crie um recurso de Bing Search**:
   - Clique em "Criar um recurso"
   - Pesquise por "Bing Search v7"
   - Selecione "Bing Search v7" da Microsoft
   - Clique em "Criar"

3. **Configure o recurso**:
   - **Assinatura**: Selecione sua assinatura
   - **Grupo de recursos**: Crie um novo ou use existente
   - **Região**: Escolha uma região próxima (ex: Brazil South)
   - **Nome**: Dê um nome ao recurso (ex: "bing-search-api")
   - **Tipo de preço**: Escolha "F0" (gratuito) ou outro plano
   - Clique em "Revisar + criar" e depois "Criar"

4. **Obtenha a chave**:
   - Após a criação, vá para o recurso
   - No menu lateral, clique em "Chaves e endpoint"
   - Copie a **Chave 1** ou **Chave 2**

### 2. Configurar a Variável de Ambiente

#### Windows PowerShell:
```powershell
$env:BING_API_KEY="sua_chave_aqui"
```

#### Windows CMD:
```cmd
set BING_API_KEY=sua_chave_aqui
```

#### Linux/Mac:
```bash
export BING_API_KEY="sua_chave_aqui"
```

### 3. Configuração Permanente (Opcional)

Para não precisar configurar toda vez que abrir o terminal:

#### Windows (PowerShell):
1. Abra o PowerShell como administrador
2. Execute:
```powershell
[Environment]::SetEnvironmentVariable("BING_API_KEY", "sua_chave_aqui", "User")
```

#### Windows (CMD):
1. Abra o CMD como administrador
2. Execute:
```cmd
setx BING_API_KEY "sua_chave_aqui"
```

#### Linux/Mac:
1. Edite o arquivo `~/.bashrc` ou `~/.zshrc`:
```bash
echo 'export BING_API_KEY="sua_chave_aqui"' >> ~/.bashrc
source ~/.bashrc
```

### 4. Verificar a Configuração

1. **Configure a variável de ambiente**
2. **Reinicie a aplicação Streamlit**:
   ```bash
   streamlit run app_streamlit.py
   ```
3. **Teste a pesquisa**:
   - Vá para a página "Pesquisa IA"
   - Digite um termo de pesquisa
   - Verifique se os resultados da internet aparecem

### 5. Limites da API

- **Plano F0 (Gratuito)**: 3 consultas por segundo, 1000 consultas por mês
- **Plano S0 (Pago)**: 3 consultas por segundo, sem limite mensal

### 6. Troubleshooting

#### Erro "API do Bing não configurada":
- Verifique se a variável de ambiente está configurada
- Reinicie a aplicação após configurar a variável

#### Erro "Chave da API do Bing inválida":
- Verifique se a chave está correta
- Certifique-se de que o recurso está ativo no Azure

#### Erro "Limite de requisições excedido":
- Aguarde alguns minutos antes de tentar novamente
- Considere fazer upgrade para um plano pago

#### Erro de conexão:
- Verifique sua conexão com a internet
- Verifique se há firewall bloqueando a conexão

### 7. Segurança

⚠️ **Importante**: 
- Nunca compartilhe sua chave da API
- Não commite a chave no código
- Use sempre variáveis de ambiente
- Considere usar Azure Key Vault para projetos em produção

### 8. Suporte

Se você encontrar problemas:
1. Verifique a documentação oficial da [API do Bing Search](https://docs.microsoft.com/en-us/bing/search-apis/)
2. Consulte os logs de erro na aplicação
3. Entre em contato com o suporte da Microsoft Azure 