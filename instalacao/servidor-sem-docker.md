# OpenBot num servidor sem Docker

Opção do próprio OpenBot para VPS ou servidor de casa com Ubuntu 24.04 ou 26.04 e systemd.
Comandos copiados do `README.md` ("Linux server with no screen") e de `docs/self-hosted-server.md`
do OpenBot v0.77.0. **Validado por formato, não testado em execução por este kit.**

Diferença para o Docker: aqui os agentes rodam direto na máquina, como o usuário `openbot`, sem
a caixa do container em volta. Prefira o [Docker](VPS.md) se a VPS faz outras coisas.

## Instalar

```bash
curl -fsSL https://raw.githubusercontent.com/nightly-labs/openbot/main/scripts/install-server.sh | sudo bash
sudo openbot login
```

O script é baixado de `main` e roda como root: leia antes, se quiser
(`curl -fsSL <mesmo endereço> | less`).

Opções do instalador (vão depois de `sudo bash -s --`, `docs/self-hosted-server.md`):

| Opção | Padrão | Para |
|---|---|---|
| `--user <nome>` | `openbot` | o usuário que roda o OpenBot e os agentes; a pasta dele fica em `/var/lib/<nome>` |
| `--display-size <L>x<A>` | `1280x800` | tamanho da tela virtual que o Computer Use lê |
| `--name <nome>` | `OpenBot` | nome do servidor |

Exemplo: `curl -fsSL https://raw.githubusercontent.com/nightly-labs/openbot/main/scripts/install-server.sh | sudo bash -s -- --name meu-time`

## Comandos do dia a dia (`docs/self-hosted-server.md`, "Commands")

| Comando | Para |
|---|---|
| `openbot status` | versão, conta, estado do servidor, memória |
| `sudo openbot login` | entrar com o código do e-mail |
| `sudo openbot mobile-connect` | QR code para o app do celular |
| `openbot logs -f` | acompanhar o log |
| `sudo openbot start\|stop\|restart` | ligar, parar, reiniciar |
| `sudo openbot update` | instalar a versão mais nova agora |
| `sudo openbot uninstall` | sair e remover; os dados ficam |

## Backup sem Docker

O `docs/self-hosted-server.md` ("Remove") diz que os dados ficam na pasta do usuário do serviço
(`/var/lib/openbot`) e o chaveiro em `/srv/openbot-hosted`, e que "the keyring has the key of the
encrypted data in that home folder, so keep or delete the two together". O kit não traz script
para este caminho; o jeito que segue essa regra é parar, copiar os dois juntos e ligar de novo:

```bash
sudo openbot stop
sudo tar -czf /root/openbot-$(date -u +%Y%m%dT%H%M%SZ).tar.gz /var/lib/openbot /srv/openbot-hosted
sudo openbot start
```

Isto é uma leitura nossa da documentação, não um comando oficial. Para backup com verificação e
restauração, use o Docker com `backup.sh` e `restaurar.sh`.
