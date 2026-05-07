# Niassa AI Agent - Documentação

## Visão Geral

O AI Agent é um sistema que permite ao chatbot Niassa acessar informações de empresas e produtos do banco de dados em tempo real. Quando o usuário faz uma pergunta sobre empresas, alojamentos, restaurantes, experiências, produtores ou produtos, o agent:

1. **Detecta a intenção** da pergunta
2. **Busca dados relevantes** no banco de dados
3. **Enriquece o contexto** do LLM com essas informações
4. **Gera uma resposta** baseada em dados reais

## Funcionalidades

### 1. Busca de Alojamentos
Quando o usuário pergunta sobre hotéis, alojamentos, hospedagem:
```
"Onde posso ficar em Niassa?"
"Quais alojamentos há em Inhassoro?"
"Recomenda algum hotel em Quelimane?"
```

### 2. Busca de Restaurantes
Quando o usuário pergunta sobre comida, restaurantes:
```
"Quais restaurantes há em Sofala?"
"Onde posso comer em Inhambane?"
"Que comida típica há aqui?"
```

### 3. Busca de Experiências
Quando o usuário pergunta sobre tours, passeios, atividades:
```
"Quais experiências há em Niassa?"
"Que tours posso fazer?"
"Quais atividades há na zona de Inharrime?"
```

### 4. Busca de Produtores
Quando o usuário pergunta sobre produtores, agricultas, fornecedores:
```
"Quais produtores há?"
"Onde posso comprar produtos locais?"
"Quem fornece produtos agrícolas?"
```

### 5. Busca de Produtos
Quando o usuário pergunta sobre produtos para comprar:
```
"Quais produtos estão disponíveis no mercado?"
"Onde posso comprar frutas?"
"Que artigos há para venda?"
```

## Arquitetura

### Arquivo: `controllers/ai_agent.py`

Contém as funções principais:

- `search_companies()` - Busca genérica de empresas
- `search_lodgings()` - Busca de alojamentos
- `search_restaurants()` - Busca de restaurantes
- `search_experiences()` - Busca de experiências
- `search_producers()` - Busca de produtores
- `search_products()` - Busca de produtos (ProducerProduct)
- `extract_search_intent()` - Detecta a intenção da mensagem
- `_build_context_from_search()` - Formata resultados em texto

### Arquivo: `routers/ai.py` (Modificado)

O router foi modificado para:

1. Detectar intenção na mensagem do usuário
2. Buscar contexto relevante se necessário
3. Injetar contexto na instrução de sistema do LLM
4. Manter a resposta natural e conversacional

## Fluxo de Execução

```
User Message
    ↓
[Detecta Intenção] → extract_search_intent()
    ↓
[Se intenção detectada]
    ↓
[Busca Dados] → search_*() functions
    ↓
[Formata Contexto] → _build_context_from_search()
    ↓
[Enriquece Prompt] → system instruction + contexto
    ↓
[Groq LLM] → Gera resposta natural
    ↓
User Response
```

## Exemplos de Respostas

### Exemplo 1: Busca de Alojamento
**Usuário**: "Quais alojamentos há em Inhassoro?"

**Sistema detecta**: intent="lodgings", location="Inhassoro"

**Contexto adicionado ao LLM**:
```
Alojamentos disponíveis em Niassa:
- Inhassoro Beach Hotel em Inhassoro: Hotel beira-mar com vista para o oceano...
- Pousada Inhassoro em Inhassoro: Acomodação aconchegante no centro da vila...
```

**Resposta do Bot**: "Em Inhassoro, temos o Inhassoro Beach Hotel com vista para o oceano e a Pousada Inhassoro, ambas excelentes opções!"

### Exemplo 2: Busca de Produtor
**Usuário**: "Onde compro produtos agrícolas?"

**Sistema detecta**: intent="producers"

**Contexto adicionado ao LLM**:
```
Produtores disponíveis:
- Quinta da Fruta em Inhassoro: Produtor de frutas e verduras locais...
- Agro Niassa em Quelimane: Fornecedor de produtos agrícolas certificados...
```

**Resposta do Bot**: "Temos excelentes produtores locais! A Quinta da Fruta em Inhassoro e a Agro Niassa em Quelimane oferecem produtos agrícolas de alta qualidade."

## Integração com o Frontend

O frontend (niassa-connect) já está configurado para usar este agente. O chat envia mensagens para:

```
POST /api/ai/chat/stream
```

O sistema deteta automaticamente se é sobre empresas e busca dados relevantes.

## Melhorias Futuras

1. **Ranking por Relevância**: Ordenar resultados por avaliação, reviews
2. **Filtros Avançados**: Preço, distância, categorias específicas
3. **Recomendações Personalizadas**: Baseado no histórico do usuário
4. **Cache**: Cache de buscas frequentes para melhor performance
5. **Multi-language**: Suport para mais idiomas
6. **Analytics**: Tracking de perguntas frequentes

## Testing

Para testar o agente localmente:

```bash
# Terminal 1: Inicia o backend
cd niassaavanca
python -m uvicorn main:app --reload

# Terminal 2: Faz requisição de teste
curl -X POST http://localhost:8000/ai/chat/stream \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Quais alojamentos há em Niassa?",
    "history": []
  }'
```

## Troubleshooting

### "Nenhum resultado encontrado"
- O agente detectou a intenção mas não encontrou dados
- Isso é normal, o LLM ainda responde baseado no conhecimento geral

### "Erro ao buscar contexto"
- Verifique se o banco de dados está conectado
- Verifique os logs do servidor

### "Context muito grande"
- O sistema limita automaticamente a 3-5 resultados
- Aumentar o limite em `search_*()` se necessário

---

**Última atualização**: Mai 2026
**Versão**: 1.0
