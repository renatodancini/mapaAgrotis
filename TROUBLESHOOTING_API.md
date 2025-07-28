# Solução de Problemas - API

## Problema Identificado

A API está retornando erro **503 (Service Unavailable)** com a mensagem:
```json
{
  "codigo": "JTW-T-17", 
  "mensagem": "Ops, Algo deu errado!", 
  "timestamp": "2025-07-28T14:02:22-0300"
}
```

## Causas Possíveis

1. **Servidor da API indisponível** - O servidor `hom-receituariosipal.agrotis.io` pode estar:
   - Em manutenção
   - Sobrecarregado
   - Temporariamente fora do ar

2. **Token de autenticação expirado** - O token pode ter expirado ou sido revogado

3. **Problemas de rede** - Conectividade com o servidor da API

## Melhorias Implementadas

### 1. Tratamento de Erros Melhorado
- **Timeout configurado** (30 segundos) para evitar travamentos
- **Mensagens de erro detalhadas** mostrando o status HTTP e detalhes da resposta
- **Tratamento específico** para diferentes tipos de erro:
  - Timeout
  - Erro de conexão
  - Erros HTTP
  - Erros inesperados

### 2. Verificador de Status da API
- **Botão "Verificar status da API"** na página Home
- **Feedback visual** com ícones e cores
- **Teste rápido** (10 segundos) para verificar conectividade

### 3. Mensagens de Erro Informativas
- **Status HTTP** exibido para o usuário
- **Detalhes do erro** quando disponíveis
- **Sugestões de ação** baseadas no tipo de erro

## Como Usar

### Verificar Status da API
1. Acesse a página **Home**
2. Clique no botão **"Verificar status da API"**
3. Aguarde o resultado:
   - ✅ Verde = API funcionando
   - ❌ Vermelho = Problema identificado

### Durante o Upload de Planilha
- Se a API estiver indisponível, você verá mensagens detalhadas do erro
- A planilha ainda será salva no banco local
- O mapeamento será feito com dados existentes no banco

## Ações Recomendadas

### Se a API estiver com erro 503:
1. **Aguarde alguns minutos** e tente novamente
2. **Verifique se há manutenção programada**
3. **Entre em contato com o suporte** da Agrotis se o problema persistir

### Se o token estiver expirado:
1. **Solicite um novo token** de autenticação
2. **Atualize a variável `API_TOKEN`** no código
3. **Reinicie a aplicação**

### Se houver problemas de rede:
1. **Verifique sua conexão com a internet**
2. **Teste se consegue acessar outros sites**
3. **Verifique se há firewall bloqueando a conexão**

## Configuração do Token

O token atual está configurado no arquivo `app_streamlit.py`:
```python
API_TOKEN = "2795f2059403445e8808325d29336b4ac1770daeaa96c25879cb6d1d7d8582a82f65aeafb7d59366238b22be21ecece3d2093e3e98e1e5b4bd2c215d8a3ce95a"
```

Para atualizar o token:
1. Edite o arquivo `app_streamlit.py`
2. Substitua o valor da variável `API_TOKEN`
3. Salve o arquivo
4. Reinicie a aplicação Streamlit

## Logs de Erro

Os erros são exibidos diretamente na interface do Streamlit. Para logs mais detalhados, você pode:

1. **Executar a aplicação no terminal** para ver logs completos
2. **Verificar a resposta completa da API** nas mensagens de erro
3. **Usar o verificador de status** para testes rápidos

## Contato

Se o problema persistir, entre em contato com:
- **Suporte Agrotis**: Para problemas com a API
- **Desenvolvedor**: Para problemas com a aplicação local 