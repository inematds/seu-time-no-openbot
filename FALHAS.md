# FALHAS.md — uma linha por falha (mais recente no topo)

| data | o que quebrou | menor correção | prompt \| infra |
|---|---|---|---|
| 24/11/2026 | deploy do Pages falhou 2× com "No artifacts named github-pages" logo depois do upload ter dado certo | `gh run rerun <id>` (corrida de consulta do artefato no GitHub; o workflow está certo) | infra |
| 24/11/2026 | guia reprovado pelo revisor (nota 7): "Como começar" só oferecia Claude Code/Codex, e quem assina só o ChatGPT travava no passo 1 | 1ª opção = colar o pedido na IA que a pessoa já usa; R2 aprovou (nota 8) | prompt |
| 24/11/2026 | restaurar.sh falhava às vezes: o backup de segurança caía no mesmo segundo do backup restaurado e o nome colidia | backup.sh espera o próximo segundo em vez de falhar | infra |
| 24/11/2026 | compose do kit com `container_name: openbot` e volume `name: openbot-data` divergia do que já rodava na VPS (`openbot_openbot-data`): trocar de compose criaria um volume vazio | compose igual ao da VPS + `achar-openbot.sh` lê container e volume do Compose; teste trava a igualdade | prompt |
| 24/11/2026 | teste do resumo semanal com datas da semana errada (assumi que 16/11 era domingo) | conferir o dia da semana nos dados de teste | prompt |
