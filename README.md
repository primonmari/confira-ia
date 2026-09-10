# 🛡️ Confira IA — Agente Inteligente de Prevenção a Golpes Financeiros e Digitais

## Contexto

Os assistentes virtuais no setor financeiro estão evoluindo de simples chatbots reativos para agentes inteligentes e proativos. O Confira IA surge nesse contexto com um foco específico: atuar como uma linha de defesa preventiva para o usuário, ajudando a:

- **Antecipar riscos** ao analisar mensagens e situações suspeitas antes que o usuário tome uma ação
- **Personalizar a análise** com base nos sinais presentes no relato de cada usuário
- **Orientar de forma consultiva**, sem gerar pânico e sem afirmar conclusões que não pode sustentar
- **Garantir segurança** e confiabilidade nas respostas (anti-alucinação), inclusive reconhecendo quando não há informação suficiente para avaliar um caso

---

## O Que Este Projeto Entrega

### 1. Documentação do Agente

**Caso de Uso:** O Confira IA ajuda pessoas a identificar possíveis golpes bancários e digitais — mensagens de bloqueio de conta, falsas centrais de atendimento, links suspeitos, boletos falsos e solicitações indevidas via Pix — que costumam usar **engenharia social** (urgência, medo, autoridade) para induzir a vítima a agir sem pensar.

**Persona e Tom de Voz:** O agente tem personalidade preventiva, educativa, objetiva e cuidadosa. Não afirma que uma situação é definitivamente fraude, mas destaca sinais de alerta, explica sua relevância e orienta comportamentos mais seguros. Quando não há informação suficiente, declara essa limitação em vez de arriscar uma conclusão. A comunicação é acessível e clara, evitando termos técnicos de segurança digital sem explicação.

**Arquitetura:** O usuário descreve a situação suspeita → o sistema identifica conceitos e busca informações relacionadas na base de conhecimento → os sinais de alerta encontrados são pontuados para definir o nível de risco → o contexto com evidências e orientações é enviado ao agente → o agente gera a resposta final com o nível de risco, sinais identificados, explicação e orientação preventiva.

**Segurança:** O agente só responde com base na base de conhecimento disponível, sempre expõe os sinais que fundamentam sua classificação de risco, nunca solicita dados sensíveis (senhas, tokens, códigos), nunca realiza operações financeiras e nunca afirma com certeza absoluta que algo é ou não fraude.

📄 **Documentação completa:** [`docs/01-documentacao-agente.md`](./docs/01-documentacao-agente.md)

---


### 2. Base de Conhecimento

A base de conhecimento do **Confira IA** está disponibilizada na pasta `data/` e reúne informações que servem de referência para a identificação e prevenção de golpes bancários e digitais.

Os arquivos apresentam diferentes tipos de golpes, sinais de alerta, orientações preventivas, perguntas frequentes, produtos e serviços financeiros relacionados a possíveis fraudes, além de casos utilizados nos testes e na avaliação do agente.

| Arquivo | Formato | Utilização no Agente |
| --- | --- | --- |
| `golpes.json` | JSON | Contém informações sobre diferentes tipos de golpes, incluindo descrições, características e situações relacionadas. |
| `sinais_alerta.json` | JSON | Reúne sinais que podem indicar uma possível tentativa de golpe, como urgência, solicitação de senhas ou códigos de segurança e links suspeitos. |
| `orientacoes.json` | JSON | Contém orientações preventivas e ações recomendadas para diferentes situações identificadas durante a análise. |
| `faq.json` | JSON | Contém perguntas frequentes e respostas relacionadas à segurança bancária e digital. |
| `produtos_financeiros.json` | JSON | Relaciona produtos e serviços financeiros a possíveis golpes e aos sinais de alerta associados. |
| `casos_teste.json` | JSON | Contém situações utilizadas para testar e avaliar as respostas e classificações geradas pelo agente. |
| `INDIA-SPECIFIC-FRAUD-V1.jsonl` | JSONL | Dataset externo complementar com cenários sintéticos de fraudes e golpes específicos da Índia, utilizado para ampliar os cenários de avaliação do agente. |

Os dados utilizados são estruturados para servir como referência durante a análise das situações apresentadas pelo usuário e também para apoiar os testes e a avaliação do comportamento do Confira IA.

📄 **Estratégia de dados:** [`docs/02-base-conhecimento.md`](./docs/02-base-conhecimento.md)

---

### 3. Prompts do Agente

**System Prompt:** Define o comportamento do agente como analista preventivo de sinais de risco, nunca confirma fraude, nunca solicita dados sensíveis, sempre expõe os sinais usados na análise e declara incerteza quando os dados são insuficientes.

**Exemplos de Interação:** Cenários cobrindo casos claros de golpe (ex: mensagem de bloqueio de conta com link), casos ambíguos (relato incompleto) e casos legítimos (mensagem sem sinais de risco).

**Tratamento de Edge Cases:** Situações em que o usuário fornece dados sensíveis sem querer (o agente orienta a não repetir/expor essa informação), relatos vagos (o agente pede mais contexto ou declara limitação) e tentativas de uso indevido do agente para confirmar operações financeiras.

📄 **Prompts completos:** [`docs/03-prompts.md`](./docs/03-prompts.md)

---

### 4. Aplicação Funcional

Protótipo funcional do Confira IA:

- Chatbot interativo em **Streamlit**
- Integração com **LLM local via Ollama**
- Conexão com a base de conhecimento de padrões de golpes

📁 **Código:** [`src/`](./src/)

---

### 5. Avaliação e Métricas

**Métricas utilizadas:**

- Precisão na identificação de sinais de risco em relatos de golpe
- Taxa de respostas seguras (sem alucinação ou conclusões infundadas sobre fraude)
- Coerência entre os sinais identificados e a explicação apresentada ao usuário
- Taxa de reconhecimento correto de "informação insuficiente" quando aplicável

📄 **Detalhes:** [`docs/04-metricas.md`](./docs/04-metricas.md)

---

### 6. Pitch

Pitch de 3 minutos apresentando:

- Qual problema o Confira IA resolve (dificuldade em reconhecer sinais de golpe no momento da pressão)
- Como ele funciona na prática (relato do usuário → análise de sinais → nível de risco e orientação)
- Por que essa solução é relevante (segurança com humildade: nunca afirma certeza que não tem)

📄 **Roteiro:** [`docs/05-pitch.md`](./docs/05-pitch.md)

---

## Ferramentas Utilizadas

| Categoria           | Ferramentas                                                                |
| ------------------- | -------------------------------------------------------------------------- |
| **LLM**             | [Ollama](https://ollama.ai/) (execução local)                              |
| **Desenvolvimento** | [Streamlit](https://streamlit.io/)                                         |

---

## Estrutura do Repositório

```
📁 confira-ia/
│
├── 📄 README.md
│
├── 📁 data/                              # Base de conhecimento de golpes
│   ├── padroes_golpes.json               # Padrões conhecidos de golpe
│   ├── sinais_engenharia_social.json     # Técnicas de persuasão usadas em golpes
│   ├── casos_exemplo.csv                 # Exemplos de relatos para teste
│   └── canais_oficiais.json              # Canais oficiais para verificação
│
├── 📁 docs/                              # Documentação do projeto
│   ├── 01-documentacao-agente.md         # Caso de uso, persona e arquitetura
│   ├── 02-base-conhecimento.md           # Estratégia de dados
│   ├── 03-prompts.md                     # Engenharia de prompts
│   ├── 04-metricas.md                    # Avaliação e métricas
│   └── 05-pitch.md                       # Roteiro do pitch
│
├── 📁 src/                               # Código da aplicação
│   └── app.py                            # Aplicação Streamlit
│
├── 📁 assets/                            # Imagens e diagramas
│   └── ...
│
└── 📁 examples/                          # Exemplos de interação
    └── ...
```

---

## Dicas Finais (aplicadas neste projeto)

1. **Comece pelo prompt:** o system prompt do Confira IA prioriza honestidade sobre certeza — melhor declarar incerteza do que arriscar uma conclusão errada
2. **Use os dados mockados:** os padrões de golpe usados na base de conhecimento evitam qualquer necessidade de dados bancários reais dos usuários
3. **Foque na segurança:** o agente nunca solicita dados sensíveis e nunca confirma definitivamente fraude — o objetivo é orientar, não substituir os canais oficiais
4. **Teste cenários reais:** os casos de exemplo cobrem golpes comuns (Pix, falso suporte bancário, boletos falsos) e situações ambíguas
5. **Seja direto no pitch:** o roteiro de 3 minutos foca no momento de pressão que o usuário enfrenta e como o agente ajuda nesse instante
