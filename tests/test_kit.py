"""Testes do kit. Rodam com `python3 -m pytest -q` ou `python3 -m unittest discover -s tests`.

Nenhum teste chama docker nem precisa da cópia do OpenBot: os scripts de backup rodam no modo
teste (OPENBOT_DADOS_DIR = pasta falsa no lugar do volume).
"""
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "importar"))
sys.path.insert(0, str(RAIZ / "skills" / "assessor-financeiro" / "scripts"))

import validar  # noqa: E402
import montar_pacote  # noqa: E402
import resumo_semana  # noqa: E402

OBRIGATORIOS = [".config/OpenBot/openbot.db", ".local/share/keyrings/login.keyring",
                ".config/openbot-container/keyring-password"]


def escrever(p: Path, texto: str) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(texto, encoding="utf-8")
    return p


SKILL_OK = '---\nname: "Teste"\ndescription: "Faz um teste."\n---\n\n# Teste\n\nInstrução.\n'


class TestKitInteiro(unittest.TestCase):
    def test_validar_passa_no_kit(self):
        r = subprocess.run([sys.executable, str(RAIZ / "validar.py")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("tudo certo", r.stdout)


class TestSkills(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)

    def skill(self, texto=SKILL_OK):
        escrever(self.tmp / "s" / "SKILL.md", texto)
        return self.tmp / "s"

    def test_skill_valida(self):
        self.assertEqual(validar.validar_skill(self.skill()), [])

    def test_descricao_501_reprova(self):
        e = validar.validar_skill(self.skill(f'---\nname: "T"\ndescription: "{"a" * 501}"\n---\n\nx\n'))
        self.assertTrue(any("description com 501" in x for x in e), e)

    def test_descricao_500_passa(self):
        self.assertEqual(validar.validar_skill(self.skill(f'---\nname: "T"\ndescription: "{"a" * 500}"\n---\n\nx\n')), [])

    def test_nome_81_reprova(self):
        e = validar.validar_skill(self.skill(f'---\nname: "{"n" * 81}"\ndescription: "d"\n---\n\nx\n'))
        self.assertTrue(any("name com 81" in x for x in e), e)

    def test_exemplo_1001_reprova(self):
        e = validar.validar_skill(self.skill(f'---\nname: "T"\ndescription: "d"\nexample-prompt: "{"e" * 1001}"\n---\n\nx\n'))
        self.assertTrue(any("example-prompt com 1001" in x for x in e), e)

    def test_sem_frontmatter_reprova(self):
        self.assertTrue(validar.validar_skill(self.skill("# só texto\n")))

    def test_yaml_quebrado_reprova(self):
        self.assertTrue(validar.validar_skill(self.skill("---\nname: a: b: c\n---\n\nx\n")))

    def test_nome_com_acento_reprova(self):
        e = validar.validar_skill(self.skill('---\nname: "Organização"\ndescription: "d"\n---\n\nx\n'))
        self.assertTrue(any("slug" in x for x in e), e)

    def test_env_reprova(self):
        p = self.skill()
        escrever(p / ".env", "X=1")
        self.assertTrue(any(".env" in x for x in validar.validar_skill(p)))

    def test_zip_dentro_reprova(self):
        p = self.skill()
        escrever(p / "assets" / "x.zip", "x")
        self.assertTrue(validar.validar_skill(p))

    def test_link_simbolico_reprova(self):
        p = self.skill()
        os.symlink(p / "SKILL.md", p / "link.md")
        self.assertTrue(any("simbólico" in x for x in validar.validar_skill(p)))

    def test_icone_que_nao_e_png_reprova(self):
        p = self.skill()
        escrever(p / "assets" / "icon.png", "nao sou png")
        self.assertTrue(any("icon.png" in x for x in validar.validar_skill(p)))

    def test_201_arquivos_reprova(self):
        p = self.skill()
        for i in range(201):
            escrever(p / "references" / f"r{i}.md", "x")
        self.assertTrue(any("arquivos" in x for x in validar.validar_skill(p)))

    def test_slug_igual_ao_do_codigo(self):
        # mesmo resultado do slugify de skill-package.ts para nomes do kit
        self.assertEqual(validar.slugify("Orquestrador do time"), "orquestrador-do-time")
        self.assertEqual(validar.slugify("Organização"), "organizac-a-o")


class TestTema(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.base = json.loads((RAIZ / "themes" / "inema.json").read_text(encoding="utf-8"))

    def tema(self, t, nome="teste.json"):
        return validar.validar_tema(escrever(self.tmp / nome, json.dumps(t)))

    def test_tema_inema_passa(self):
        self.assertEqual(validar.validar_tema(RAIZ / "themes" / "inema.json"), [])

    def test_tema_inema_tem_as_cores_da_marca(self):
        self.assertEqual(self.base["colors"]["canvas"], "#0c0c10")
        self.assertEqual(self.base["colors"]["accent"].upper(), "#FACC15")

    def test_cor_faltando_reprova(self):
        t = copy.deepcopy(self.base)
        del t["colors"]["danger"]
        self.assertTrue(any("danger" in x for x in self.tema(t)))

    def test_hex_errado_reprova(self):
        t = copy.deepcopy(self.base)
        t["colors"]["accent"] = "#FACC1"
        self.assertTrue(self.tema(t))

    def test_aparencia_errada_reprova(self):
        t = copy.deepcopy(self.base)
        t["appearance"] = "escuro"
        self.assertTrue(self.tema(t))

    def test_nome_de_arquivo_com_maiuscula_reprova(self):
        self.assertTrue(self.tema(self.base, "INEMA.json"))


class TestCompose(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.texto = (RAIZ / "instalacao" / "compose.yaml").read_text(encoding="utf-8")

    def compose(self, texto):
        return validar.validar_compose(escrever(self.tmp / "compose.yaml", texto))

    def test_compose_do_kit_passa(self):
        self.assertEqual(validar.validar_compose(RAIZ / "instalacao" / "compose.yaml"), [])

    def test_compose_igual_ao_da_vps_de_teste(self):
        import yaml
        s = yaml.safe_load(self.texto)["services"]["openbot"]
        self.assertEqual(s["image"], "ghcr.io/nightly-labs/openbot:0.77.0")
        self.assertEqual(s["security_opt"], ["seccomp=./seccomp.json", "no-new-privileges:true"])
        self.assertEqual((s["shm_size"], s["stop_grace_period"], s["mem_limit"]), ("1g", "60s", "6g"))
        self.assertEqual(s["volumes"], ["openbot-data:/data"])
        self.assertNotIn("container_name", s)
        self.assertNotIn("ports", s)

    def test_sem_seccomp_reprova(self):
        self.assertTrue(any("seccomp" in x for x in self.compose(self.texto.replace("      - seccomp=./seccomp.json\n", ""))))

    def test_sem_no_new_privileges_reprova(self):
        self.assertTrue(any("no-new-privileges" in x for x in self.compose(self.texto.replace("      - no-new-privileges:true\n", ""))))

    def test_sem_memoria_reprova(self):
        self.assertTrue(any("memória" in x for x in self.compose(self.texto.replace("    mem_limit: 6g\n", ""))))

    def test_latest_reprova(self):
        self.assertTrue(any("latest" in x for x in self.compose(self.texto.replace(":0.77.0", ":latest"))))

    def test_pasta_do_host_reprova(self):
        self.assertTrue(self.compose(self.texto.replace("- openbot-data:/data", "- ./dados:/data")))

    def test_socket_do_docker_reprova(self):
        t = self.texto.replace("- openbot-data:/data", "- openbot-data:/data\n      - /var/run/docker.sock:/var/run/docker.sock")
        self.assertTrue(any("docker.sock" in x for x in self.compose(t)))

    def test_unconfined_reprova(self):
        self.assertTrue(self.compose(self.texto.replace("seccomp=./seccomp.json", "seccomp=unconfined")))


class TestImportacao(unittest.TestCase):
    def setUp(self):
        self.fonte = json.loads((RAIZ / "importar" / "agentes.json").read_text(encoding="utf-8"))
        self.man = montar_pacote.manifesto(self.fonte, "2026-11-24T00:00:00Z")
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)

    def test_manifesto_do_kit_passa(self):
        self.assertEqual(validar.validar_manifesto(self.man), [])

    def test_quatro_agentes_e_um_canal(self):
        self.assertEqual([a["key"] for a in self.man["agents"]], ["orquestrador", "financeiro", "organizador", "revisor"])
        self.assertEqual(self.man["channels"][0]["lead"], "orquestrador")

    def test_rotinas_saem_desligadas(self):
        for a in self.man["agents"]:
            for r in a["routines"]:
                self.assertIs(r["active"], False)
                self.assertEqual(r["timezone"], "America/Sao_Paulo")

    def test_zip_montado_passa(self):
        z = montar_pacote.montar(self.tmp / "p.zip", exportado_em="2026-11-24T00:00:00Z")
        self.assertEqual(validar.validar_zip(z), [])
        with zipfile.ZipFile(z) as f:
            nomes = f.namelist()
        self.assertIn("openbot-import.json", nomes)
        self.assertIn("agents/financeiro/skills/assessor-financeiro/scripts/resumo_semana.py", nomes)
        self.assertFalse([n for n in nomes if "__pycache__" in n])

    def test_key_invalida_reprova(self):
        m = copy.deepcopy(self.man)
        m["agents"][0]["key"] = "-Ruim"
        self.assertTrue(validar.validar_manifesto(m))

    def test_key_repetida_reprova(self):
        m = copy.deepcopy(self.man)
        m["agents"][1]["key"] = m["agents"][0]["key"]
        self.assertTrue(validar.validar_manifesto(m))

    def test_descricao_2001_reprova(self):
        m = copy.deepcopy(self.man)
        m["agents"][0]["description"] = "x" * 2001
        self.assertTrue(validar.validar_manifesto(m))

    def test_agenda_invalida_reprova(self):
        m = copy.deepcopy(self.man)
        m["agents"][0]["routines"][0]["schedule"] = {"kind": "weekly", "weekday": 7, "time": "17:00"}
        self.assertTrue(validar.validar_manifesto(m))

    def test_intervalo_menor_que_3_min_reprova(self):
        self.assertFalse(validar.agenda_valida({"kind": "interval", "amount": 2, "unit": "minutes"}))
        self.assertTrue(validar.agenda_valida({"kind": "interval", "amount": 30, "unit": "minutes"}))

    def test_skill_fora_do_prefixo_reprova(self):
        m = copy.deepcopy(self.man)
        m["agents"][0]["skills"] = ["agents/outro/skills/x"]
        self.assertTrue(validar.validar_manifesto(m))

    def test_membro_desconhecido_reprova(self):
        m = copy.deepcopy(self.man)
        m["channels"][0]["members"].append("fantasma")
        self.assertTrue(validar.validar_manifesto(m))

    def test_fuso_invalido_reprova(self):
        m = copy.deepcopy(self.man)
        m["agents"][0]["routines"][0]["timezone"] = "Brasil/Hora"
        self.assertTrue(validar.validar_manifesto(m))

    def test_zip_sem_manifesto_na_raiz_reprova(self):
        z = self.tmp / "ruim.zip"
        with zipfile.ZipFile(z, "w") as f:
            f.writestr("pasta/openbot-import.json", "{}")
        self.assertTrue(validar.validar_zip(z))


class TestBackup(unittest.TestCase):
    """backup.sh e restaurar.sh no modo teste: uma pasta falsa no lugar do volume, zero docker."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.dados = self.tmp / "dados"
        self.backups = self.tmp / "backups"
        for f in OBRIGATORIOS:
            escrever(self.dados / f, f"conteudo de {f}")
        escrever(self.dados / "OpenBot" / "Agents" / "financeiro" / "financas" / "despesas.csv",
                 "data,valor,descricao,categoria,forma,origem\n2026-11-24,29.90,almoço,Alimentação,pix,texto\n")
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        # um "docker" falso que registra qualquer chamada: o teste exige que ninguém o chame
        escrever(self.bin / "docker", f"#!/bin/sh\necho \"$@\" >> {self.tmp}/docker-chamado\nexit 99\n").chmod(0o755)

    def rodar(self, script, *args, manter="7"):
        env = {**os.environ, "OPENBOT_DADOS_DIR": str(self.dados), "OPENBOT_BACKUP_DIR": str(self.backups),
               "OPENBOT_BACKUP_KEEP": manter, "PATH": f"{self.bin}:{os.environ['PATH']}"}
        return subprocess.run(["bash", str(RAIZ / "instalacao" / script), *args], env=env,
                              capture_output=True, text=True)

    def backups_feitos(self):
        return sorted(p.name for p in self.backups.glob("openbot-*.tar.gz"))

    def foto(self):
        return {p.relative_to(self.dados).as_posix(): p.read_bytes() for p in self.dados.rglob("*") if p.is_file()}

    def tearDown(self):
        self.assertFalse((self.tmp / "docker-chamado").exists(), "modo teste chamou docker")

    def test_bash_n(self):
        for s in ("backup.sh", "restaurar.sh", "achar-openbot.sh"):
            self.assertEqual(subprocess.run(["bash", "-n", str(RAIZ / "instalacao" / s)]).returncode, 0, s)

    def test_backup_e_restauracao_ida_e_volta(self):
        original = self.foto()
        r = self.rodar("backup.sh")
        self.assertEqual(r.returncode, 0, r.stderr)
        [arq] = self.backups_feitos()
        p = self.backups / arq
        self.assertEqual(oct(p.stat().st_mode & 0o777), "0o600")
        self.assertEqual(oct(self.backups.stat().st_mode & 0o777), "0o700")
        self.assertTrue((self.backups / (arq + ".sha256")).is_file())
        self.assertFalse(list(self.backups.glob("*.partial")))
        # estraga os dados e restaura
        (self.dados / ".config" / "OpenBot" / "openbot.db").write_text("estragado")
        escrever(self.dados / "lixo.txt", "não estava no backup")
        r = self.rodar("restaurar.sh", str(p))
        self.assertEqual(r.returncode, 2, "sem --confirmo não pode restaurar")
        self.assertIn("lixo.txt", [x.name for x in self.dados.iterdir()])
        r = self.rodar("restaurar.sh", str(p), "--confirmo")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.foto(), original)
        # o backup de antes da restauração existe e o restaurado continua lá
        self.assertEqual(len(self.backups_feitos()), 2)
        self.assertIn(arq, self.backups_feitos())

    def test_rotacao_mantem_os_mais_novos(self):
        import time
        for _ in range(3):
            self.assertEqual(self.rodar("backup.sh", manter="2").returncode, 0)
            time.sleep(1.1)
        feitos = self.backups_feitos()
        self.assertEqual(len(feitos), 2)
        self.assertEqual(len(list(self.backups.glob("*.sha256"))), 2)

    def test_sem_chaveiro_falha_e_nao_apaga_os_antigos(self):
        self.assertEqual(self.rodar("backup.sh").returncode, 0)
        antes = self.backups_feitos()
        (self.dados / ".local" / "share" / "keyrings" / "login.keyring").unlink()
        import time
        time.sleep(1.1)
        r = self.rodar("backup.sh", manter="1")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("login.keyring", r.stderr)
        self.assertEqual(self.backups_feitos(), antes)
        self.assertFalse(list(self.backups.glob("*.partial")))

    def test_backup_dentro_dos_dados_recusa(self):
        env = {**os.environ, "OPENBOT_DADOS_DIR": str(self.dados), "OPENBOT_BACKUP_DIR": str(self.dados / "bk"),
               "PATH": f"{self.bin}:{os.environ['PATH']}"}
        r = subprocess.run(["bash", str(RAIZ / "instalacao" / "backup.sh")], env=env, capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)

    def test_restaurar_arquivo_corrompido_recusa(self):
        self.assertEqual(self.rodar("backup.sh").returncode, 0)
        [arq] = self.backups_feitos()
        with open(self.backups / arq, "ab") as f:
            f.write(b"x")
        r = self.rodar("restaurar.sh", str(self.backups / arq), "--confirmo")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("não bate", r.stderr)


class TestResumoSemana(unittest.TestCase):
    def test_resumo(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        csv = escrever(tmp / "d.csv", "data,valor,descricao,categoria,forma,origem\n"
                       "2026-11-15,10.00,café,Alimentação,pix,texto\n"       # domingo: semana anterior
                       "2026-11-16,29.90,almoço,Alimentação,pix,texto\n"     # segunda: começa a semana
                       "2026-11-18,150.00,mercado,Alimentação,débito,foto\n"
                       "2026-11-20,60.50,combustível,Transporte,crédito,áudio\n"
                       "2026-11-22,1200.00,aluguel,Moradia,boleto,texto\n"   # domingo: fecha a semana
                       "2026-11-23,5.00,bala,Alimentação,dinheiro,texto\n"   # segunda seguinte: fora
                       "xx,1,linha ruim,Outros,pix,texto\n")
        r = resumo_semana.resumir(resumo_semana.ler(csv), resumo_semana.segunda_da_semana(
            __import__("datetime").date(2026, 11, 19)))
        self.assertEqual(r["total"], 1440.40)
        self.assertEqual(r["total_anterior"], 10.00)
        self.assertEqual(r["por_categoria"][0], ("Moradia", 1200.00))
        self.assertAlmostEqual(sum(v for _, v in r["por_categoria"]), r["total"])
        t = resumo_semana.texto(r)
        self.assertIn("R$ 1.440,40", t)
        self.assertIn("Alimentação: R$ 179,90", t)


if __name__ == "__main__":
    unittest.main()
