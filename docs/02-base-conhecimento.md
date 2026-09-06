# Base de Conhecimento

## Estrutura da Base de Conhecimento

A base de conhecimento do **Confira IA** está armazenada na pasta `data` e reúne informações estruturadas sobre golpes bancários e digitais, sinais de alerta, orientações preventivas, produtos e serviços financeiros relacionados a possíveis fraudes, perguntas frequentes e casos utilizados para avaliação do agente.

| Arquivo                         | Formato | Utilização no Agente                                                                                                                                            |
| ------------------------------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `golpes.json`                   | JSON    | Contém os principais tipos de golpes, suas descrições, características e situações relacionadas.                                                                |
| `sinais_alerta.json`            | JSON    | Contém sinais que podem indicar uma tentativa de golpe, como urgência, solicitação de senhas, códigos de segurança e links suspeitos.                           |
| `orientacoes.json`              | JSON    | Contém orientações preventivas e ações recomendadas para diferentes situações de risco.                                                                         |
| `faq.json`                      | JSON    | Contém perguntas frequentes e respostas relacionadas à segurança bancária e digital.                                                                            |
| `produtos_financeiros.json`     | JSON    | Relaciona produtos e serviços financeiros a possíveis golpes e sinais de alerta associados.                                                                     |
| `casos_teste.json`              | JSON    | Contém situações utilizadas para testar e avaliar as respostas e classificações do agente.                                                                      |
| `INDIA-SPECIFIC-FRAUD-V1.jsonl` | JSONL   | Dataset externo complementar, contendo cenários sintéticos de fraudes e golpes específicos da Índia, utilizado para ampliar os cenários de avaliação do agente. |

---

## Adaptações nos Dados

A base de conhecimento foi adaptada para o contexto de **segurança bancária e prevenção contra golpes**.

Os dados originalmente propostos no projeto foram substituídos por informações relacionadas a:

- golpes bancários e digitais;
- sinais de alerta;
- orientações de segurança;
- perguntas frequentes;
- produtos e serviços financeiros;
- situações de risco relacionadas a possíveis fraudes.

Também foram adicionados casos de teste para avaliar o comportamento do agente diante de diferentes situações relatadas pelos usuários.

Como complemento à base principal, foi utilizado o dataset público **India-Specific Fraud & Scam Dataset (v1.0)**, disponibilizado no Hugging Face pela VNOVA AI.

O dataset contém cenários sintéticos relacionados a fraudes, golpes e crimes cibernéticos com foco na Índia, incluindo situações envolvendo:

- golpes com UPI;
- phishing;
- fraudes de KYC;
- golpes envolvendo OTP;
- falsas centrais de atendimento;
- falsas ofertas de emprego;
- golpes de investimento;
- fraudes em marketplaces;
- golpes envolvendo cartões;
- engenharia social;
- outros cenários de fraude digital.

O dataset externo foi utilizado como fonte complementar de cenários e padrões de golpes, principalmente para ampliar a diversidade dos casos utilizados na avaliação do agente.

### Licença e Atribuição

O dataset está disponível sob a licença CC BY 4.0.

Para o uso no projeto, a atribuição é feita da seguinte forma:

> VNOVA AI — India-Specific Fraud & Scam Dataset (v1.0), disponível no Hugging Face, sob licença CC BY 4.0.

---

## Estratégia de Integração

### Como os dados são carregados?

Os arquivos JSON da pasta `data` são carregados pela aplicação utilizando Python.

O carregamento é realizado por meio de uma função responsável por abrir cada arquivo e converter seu conteúdo para estruturas de dados do Python.

```python
import json


def carregar_json(caminho):

    with open(caminho, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def carregar_jsonl(caminho):

    dados = []

    with open(caminho, "r", encoding="utf-8") as arquivo:
        for linha in arquivo:
            linha = linha.strip()

            if linha:
                dados.append(json.loads(linha))

    return dados


# Carregar arquivos JSON
golpes = carregar_json("data/golpes.json")
sinais_alerta = carregar_json("data/sinais_alerta.json")
orientacoes = carregar_json("data/orientacoes.json")
faq = carregar_json("data/faq.json")
produtos_financeiros = carregar_json("data/produtos_financeiros.json")
casos_teste = carregar_json("data/casos_teste.json")

# Carregar arquivo JSONL
india_fraud = carregar_jsonl("data/INDIA-SPECIFIC-FRAUD-V1.jsonl")

```

### Como os dados são utilizados?

Após o carregamento, os dados ficam disponíveis para serem consultados pela aplicação de acordo com a situação apresentada pelo usuário.

A aplicação identifica o contexto da pergunta e utiliza as informações relevantes da base de conhecimento para complementar o contexto enviado ao modelo de linguagem.

Os dados não são inseridos integralmente no `system prompt`. A aplicação busca apenas as informações relevantes para a situação apresentada, reduzindo o volume de dados enviado ao modelo e mantendo as respostas alinhadas à base de conhecimento.

---

## Exemplo de Contexto Montado

Um exemplo de contexto enviado ao agente poderia ser:

```text
Situação relatada pelo usuário:

"Recebi uma mensagem dizendo que minha conta será bloqueada
e pedindo para clicar em um link para atualizar meus dados."


Contexto identificado:

Produto/serviço:
- Conta bancária


Possíveis golpes relacionados:
- Falso bloqueio de conta
- Falsa atualização cadastral
- Phishing


Sinais de alerta identificados:
- Ameaça de bloqueio
- Link para atualização de dados
- Senso de urgência


Orientações relacionadas:
- Não clicar no link.
- Não informar dados pessoais ou bancários.
- Acessar o serviço diretamente pelo aplicativo ou site oficial.
- Procurar um canal oficial para confirmar a situação.
```

Esse contexto reúne as informações relevantes recuperadas da base de conhecimento e fornece ao modelo os elementos necessários para elaborar uma resposta segura e contextualizada.

---

## Regras do Agente

O agente deve seguir algumas regras para garantir respostas seguras e alinhadas ao objetivo do projeto:

```text
- Não afirmar que a situação é definitivamente uma fraude.
- Informar quando existem características compatíveis com golpes conhecidos.
- Apresentar o nível de risco de acordo com os sinais identificados.
- Não solicitar senhas, códigos de segurança ou dados bancários.
- Orientar o usuário a utilizar canais oficiais.
- Quando não houver informação suficiente na base, informar a limitação.
```

---

## Fluxo de Utilização da Base

De forma simplificada, o funcionamento pode ser representado pelo seguinte fluxo:

```text
Usuário
   ↓
Relato da situação
   ↓
Identificação do contexto
   ↓
Consulta à base de conhecimento
   ↓
Seleção das informações relevantes
   ↓
Montagem do contexto
   ↓
Modelo de linguagem
   ↓
Resposta orientativa
```

A estratégia permite que o agente utilize uma base estruturada e específica para o domínio de **segurança bancária**, mantendo o modelo de linguagem responsável pela interpretação da situação e pela elaboração da resposta em linguagem natural.
