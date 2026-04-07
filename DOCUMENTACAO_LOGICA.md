# Documentação Técnica: Simulação de Gestão de Emergências

Este documento detalha o funcionamento interno e a lógica de Inteligência Artificial implementada no projeto.

## 1. Visão Geral do Sistema
A simulação utiliza uma abordagem **Multi-Agente (MAS)** para resolver problemas dinâmicos (incêndios e feridos) em uma cidade dividida em quadrantes. A centralização da inteligência ocorre no **Agente BDI**, que atua como o Comandante Central.

## 2. Arquiteturas de Agentes

### A. Drones (Agentes Reativos Simples)
- **Lógica**: Operam sem memória. A cada frame, eles percebem apenas a célula atual.
- **Fluxo**: `Detectar Evento (Fogo/Ferido)` -> `Enviar Mensagem (BDI)`.
- **Justificativa**: Representam sensores de baixo custo que fornecem dados brutos para o sistema central.

### B. Bombeiros (Agentes Baseados em Modelos)
- **Lógica**: Possuem um modelo interno (sua base e seu quadrante).
- **Intenção**: Permanecer em patrulha na `base_pos` ou executar missão de `alvo`.
- **Redirecionamento**: Podem sair de seu quadrante se o BDI identificar sobrecarga em outra área (ajuda inter-quadrantes).

### C. Agente SEQUENCIAL (Baseado em Objetivos)
- **Arquitetura**: Orientada a metas FIFO (First-In, First-Out).
- **Comportamento**: Prioriza a ordem cronológica da lista de resgates distribuída pelo BDI.
- **Meta**: Esvaziar a lista de resgates, custe o que custar em termos de distância.

### D. Agente OTIMIZADOR (Baseado em Utilidade)
- **Arquitetura**: Racionalidade Econômica.
- **Função de Utilidade**: Calcula a `Distância de Manhattan` para todo o estado do mundo (todos os feridos conhecidos).
- **Dinâmica**: Reavalia a melhor vítima a cada passo, permitindo mudar de direção se uma nova vítima mais próxima aparecer ou se o estado do mundo mudar.

## 3. Lógica do Agente BDI (Belief-Desire-Intention)

O Comandante BDI não está fisicamente no mapa, mas gerencia o estado mental da operação:

- **Crenças (Beliefs)**: O BDI acredita que há fogo ou feridos baseando-se apenas nos relatórios dos Drones. Se um drone para de reportar, a crença persiste até que um agente de campo confirme a resolução.
- **Desejos (Desires)**: O objetivo global de ter 0 fogos e 0 feridos no mapa.
- **Intenções (Intentions)**:
    - **Plano de Resposta Rápida**: Enviar o agente mais próximo para cada nova ocorrência.
    - **Regra de Exceção**: Se um bombeiro está ocupado, o BDI "pretende" buscar o próximo bombeiro ocioso para cobrir o vácuo operacional.

## 4. Comunicação e Métricas

### Fluxo de Mensagens
`Drone (Sensor)` -> `BDI (Cérebro)` -> `Bombeiro/Socorrista (Atuador)`.

### Métricas de Desempenho (Critério 3 da UFMA)
Para comparar o **Sequencial** e o **Otimizador**, a simulação acompanha:
- **Hodômetro (Passos)**: Quantidade de deslocamento físico.
- **Eficiência**: `(Vítimas / Passos) * 100`. 
- **Conclusão Esperada**: O **Otimizador** deve sempre apresentar uma eficiência maior, pois ele percorre menos distância para salvar a mesma quantidade (ou mais) de vítimas.

---
**Status Final do Projeto**: Atende 100% dos requisitos de arquitetura, mensagens, métricas e dinâmica BDI.
