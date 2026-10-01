"""
Demonstração simples de login com proteção de senha.

Fluxo:  senha -> PBKDF2-HMAC-SHA256 (com salt) -> usuarios.json -> login -> verificação

Usa apenas a biblioteca padrão do Python (hashlib, secrets, hmac, json, getpass).
"""

import getpass
import hashlib
import hmac
import json
import os
import secrets

ARQUIVO = "usuarios.json"   # "banco de dados" da demonstração
ITERACOES = 600_000         # recomendação OWASP (2023+) para PBKDF2-HMAC-SHA256


# ---------------------------------------------------------------- armazenamento
def carregar_usuarios():
    if not os.path.exists(ARQUIVO):
        return {}
    with open(ARQUIVO, encoding="utf-8") as f:
        return json.load(f)


def salvar_usuarios(usuarios):
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------- criptografia
def gerar_hash(senha, salt, iteracoes=ITERACOES):
    """Transforma a senha em um hash. É uma via de mão única: não dá para voltar."""
    return hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, iteracoes)


# ---------------------------------------------------------------- casos de uso
def cadastrar():
    usuario = input("Usuário: ").strip()
    usuarios = carregar_usuarios()
    if not usuario or usuario in usuarios:
        print("Usuário inválido ou já cadastrado.")
        return

    # 1) A senha é recebida (getpass não mostra o que é digitado)
    senha = getpass.getpass("Senha: ")
    print(f"\n[1] Senha recebida pela aplicação (só existe na memória): {senha!r}")

    # 2) Transformação: salt aleatório + PBKDF2
    salt = secrets.token_bytes(16)
    hash_senha = gerar_hash(senha, salt)
    print(f"[2] Salt aleatório gerado:  {salt.hex()}")
    print(f"[2] Hash PBKDF2 ({ITERACOES} iterações): {hash_senha.hex()}")

    # 3) Armazenamento: salva SOMENTE salt + hash (nunca a senha)
    usuarios[usuario] = {
        "algoritmo": "pbkdf2_sha256",
        "iteracoes": ITERACOES,
        "salt": salt.hex(),
        "hash": hash_senha.hex(),
    }
    salvar_usuarios(usuarios)
    print(f"[3] Gravado em {ARQUIVO}:")
    print(json.dumps({usuario: usuarios[usuario]}, indent=2))
    print("\nUsuário cadastrado! A senha original foi descartada.")


def login():
    usuario = input("Usuário: ").strip()
    senha = getpass.getpass("Senha: ")
    print(f"\n[4] Tentativa de login: usuário={usuario!r}, senha digitada={senha!r}")

    registro = carregar_usuarios().get(usuario)
    if registro is None:
        print("Usuário ou senha incorretos.")
        return

    # 5) Verificação: recalcula o hash com o MESMO salt e compara
    salt = bytes.fromhex(registro["salt"])
    hash_calculado = gerar_hash(senha, salt, registro["iteracoes"]).hex()
    print(f"[5] Salt lido do arquivo:     {registro['salt']}")
    print(f"[5] Hash armazenado:          {registro['hash']}")
    print(f"[5] Hash da senha digitada:   {hash_calculado}")

    # compare_digest evita ataques de tempo (timing attack)
    if hmac.compare_digest(hash_calculado, registro["hash"]):
        print("\nOs hashes são iguais -> LOGIN OK ✅")
    else:
        print("\nOs hashes são diferentes -> Usuário ou senha incorretos ❌")


def mostrar_arquivo():
    print(f"\nConteúdo de {ARQUIVO} (o que um invasor veria):")
    print(json.dumps(carregar_usuarios(), indent=2, ensure_ascii=False))


def main():
    opcoes = {"1": cadastrar, "2": login, "3": mostrar_arquivo}
    while True:
        print("\n=== Demo de Login Seguro ===")
        print("1) Cadastrar  2) Login  3) Ver arquivo  0) Sair")
        escolha = input("> ").strip()
        if escolha == "0":
            break
        acao = opcoes.get(escolha)
        if acao:
            acao()
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    main()
