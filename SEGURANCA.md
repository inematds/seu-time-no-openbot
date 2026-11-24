# Checklist de segurança do seu time no OpenBot

O próprio OpenBot avisa no README: os agentes rodam com `danger-full-access` e
`approvalPolicy: never`, "They can read and modify files, run commands, use the network, and control
the embedded browser without per-action confirmations". É uma escolha do produto, não um defeito
(`SECURITY.md`). Este checklist diz como reduzir o estrago se um agente errar.
Cada item cita onde está na documentação do OpenBot v0.77.0. Não é conselho jurídico.

## 1. Permissão de cada agente: menos que "acesso completo"

Cada agente tem um nível de **Permissions**: *Workspace only* (só a pasta dele), *Ask first*
(pergunta antes) ou *Full access* (`docs/architecture/structure.md`).

- [ ] **Financeiro, Organizador e Revisor:** *Ask first*. Eles só precisam da pasta deles e de
      responder a você. No computador, *Workspace only* também serve.
- [ ] **Orquestrador:** *Ask first*. Um agente novo nasce com os limites de quem o criou
      (`docs/architecture/agents.md`): se o Orquestrador estiver restrito, o time que ele monta
      também fica.
- [ ] **No Docker, use *Ask first*, não *Workspace only*, para agentes Codex:** dentro do container o
      Codex no modo *Workspace only* pode falhar (`bwrap: Failed to make / slave`) e o OpenBot pede
      para escolher *Ask first* ou *Full access* (`docs/docker.md`, "Not confirmed").
- [ ] Um agente só consegue **diminuir** a própria permissão. Aumentar é sempre você
      (`docs/architecture/agents.md`).

## 2. Conta de IA: separe se a sua é importante

O OpenBot usa o login que você já tem no Codex, no Claude, no Gemini etc. Ele não paga nem revende
o uso, e "a provider can limit or close an account that breaks them" (`docs/provider-terms.md`).

- [ ] Leia o que o seu provedor diz sobre ferramentas de terceiros antes de usar a assinatura.
- [ ] **Claude pela assinatura:** o próprio OpenBot classifica o risco de "não claro" (seu uso no
      seu computador) a "alto" (outras pessoas usando os seus agentes). Agentes rodando sozinhos
      podem passar do "uso individual comum" (`docs/provider-terms.md`, "Risk by use").
- [ ] Se a conta de IA é a do seu trabalho ou tem histórico que você não quer perder, use uma
      **conta separada** para o time, ou uma chave de API paga (o método que a Anthropic indica
      para produtos feitos com o Agent SDK, segundo a mesma página).
- [ ] Para testar sem conta paga: os modelos marcados **Free** do OpenCode não pedem login
      (`README.md`, "Agent setup"). O OpenBot avisa que, no Cline, o provedor de modelo grátis pode
      usar os seus pedidos para treinar modelos.

## 3. WhatsApp: chip separado, nunca o número importante

O WhatsApp do OpenBot é um cliente não oficial (Baileys) e "WhatsApp can restrict or block a
number that it sees as automated" (`docs/messaging.md`).

- [ ] Use um **número só para o OpenBot** (chip separado). Nunca o número do trabalho, do banco ou
      o que você não pode perder.
- [ ] Na hora de ligar, escolha **A number only for OpenBot**.
- [ ] Em **Who can write**, ponha só você e quem você confia: quem pode escrever pode dar trabalho
      aos agentes, com as permissões que eles têm (`docs/messaging.md`, "Limits").
- [ ] Se o OpenBot ficar uns 14 dias sem conexão, o WhatsApp remove o aparelho e você liga de novo.

## 4. Senhas: no cofre, nunca na conversa

- [ ] Senha, cartão e código de banco não vão no chat nem em arquivo do workspace. As skills do kit
      já recusam guardar isso.
- [ ] Use um cofre de senhas. O OpenBot conecta com Bitwarden e Vaultwarden por chave de API
      (`docs/docker.md`, "Limits").
- [ ] No Docker, todos os agentes rodam como o mesmo usuário e um agente consegue ler as chaves de
      outro. Agentes que não podem dividir chaves vão em **containers separados**
      (`docs/docker.md`, "Security").

## 5. Backup

- [ ] Rode o `backup.sh` antes de mudar qualquer coisa e todo dia (ver [instalacao/VPS.md](instalacao/VPS.md)).
- [ ] Copie os backups para **fora** da máquina. Eles têm as chaves dos dados: trate como senha.
- [ ] Teste a restauração uma vez, num container de teste, antes de precisar dela.

## 6. O container

- [ ] Mantenha o `seccomp.json` oficial e o `no-new-privileges`. Nunca `seccomp=unconfined`,
      `--privileged` ou `--no-sandbox` (`docs/docker.md`, "Security"). O `validar.py` confere.
- [ ] Não monte o socket do Docker, a sua pasta pessoal nem pasta que os agentes não podem mudar.
- [ ] Não publique porta: o acesso é pelo app e por `openbot.run/app`.
- [ ] Fixe a versão da imagem, leia as notas antes de atualizar e nunca volte para uma mais velha.

## 7. Automações

- [ ] **Webhooks:** o segredo aparece uma vez só; guarde no cofre do serviço que envia
      (`docs/webhooks.md`).
- [ ] **Local scripts:** ligue só para o agente que precisa; qualquer programa do mesmo usuário lê
      o token (`docs/automation.md`, "Security").
- [ ] Rotinas do pacote do kit chegam **desligadas**. Ligue uma de cada vez e veja quanto ela usa da
      sua assinatura.

## 8. A licença

- [ ] O OpenBot usa a **PolyForm Noncommercial 1.0.0**: grátis para uso pessoal e outros usos não
      comerciais. O README diz "OpenBot is not free software".
- [ ] **Uso comercial pede licença paga** do OpenBot (Settings → Billing, planos Starter e Team, ou
      licenses@openbot.run). Se o time trabalha para a sua empresa ou para clientes, isso vale para você.
