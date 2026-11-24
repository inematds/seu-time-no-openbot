# CLAUDE.md — seu-time-no-openbot

Kit do INEMA (gratuito, inema.club) por cima do OpenBot v0.77.0: um time de agentes em PT
(skills + pacote de importação), instalação segura com backup, checklist de segurança, tema INEMA
e `validar.py` com testes.

## Regras deste repo

- Conta e autor: `inematds <inematds@gmail.com>` (author e committer). Push pelo SSH
  (`git@github.com:inematds/seu-time-no-openbot.git`), por causa do workflow do Pages.
- **Nunca commitar código do OpenBot.** A cópia de leitura fica fora do repo
  (`~/projetos/output/openbot-fonte/src`). O `seccomp.json` não entra: o usuário baixa da tag oficial.
- Todo limite novo no `validar.py` cita `arquivo:linha` da tag `v0.77.0`. Mudou de versão do
  OpenBot: atualizar FONTE.md, a imagem do `instalacao/compose.yaml`, o `seccomp.sha256` e as citações.
- O compose tem que continuar igual ao da VPS de teste (sem `container_name`, volume `openbot-data`,
  sem porta); o teste `test_compose_igual_ao_da_vps_de_teste` trava isso.
- Rotular tudo que não rodou num OpenBot real: "validado por formato, não testado em execução".
  Só a subida do container e o `status` foram testados (VPS, 24/11/2026).
- Não citar autor de vídeo, canal ou aula de terceiros. O OpenBot e a licença dele são citados.
- Não rodar docker, AppImage nem `install-server.sh` daqui sem aprovação do Nei (hook do wifi).
- Antes de commitar: `python3 validar.py && python3 -m pytest -q`.
- Tradução EN/ES: `~/projetos/wifi/scripts/inema-traduz`. Imagens: Codex `image_gen`.

## Self-learning

When I correct you, or you catch yourself making a mistake: before continuing, add the lesson as a one-line rule under ## Lessons, so it never happens again.

## Lessons

- Dados de teste com datas: conferir o dia da semana antes de montar a semana esperada (24/11/2026 é terça; a semana de 19/11 vai de 16 a 22).
- Compose do kit não pode fixar `container_name` nem nome de volume diferente do que já roda na VPS: o Compose criaria um volume vazio. Os scripts descobrem container e volume sozinhos.
