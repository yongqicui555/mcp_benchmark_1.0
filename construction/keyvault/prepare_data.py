from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa
from cryptography.x509.oid import NameOID


def write_text(path: Path, value: str) -> None:
    path.write_text(value, encoding="utf-8")


def generate_seed(seed_dir: Path, force: bool = False) -> None:
    if seed_dir.exists() and force:
        shutil.rmtree(seed_dir)
    seed_dir.mkdir(parents=True, exist_ok=True)
    (seed_dir / ".revoked").mkdir(exist_ok=True)

    rsa_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    write_text(
        seed_dir / "id_rsa",
        rsa_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8"),
    )
    write_text(
        seed_dir / "id_rsa.pub",
        rsa_key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH,
        )
        .decode("utf-8")
        + " keyvault@example\n",
    )

    ed_key = ed25519.Ed25519PrivateKey.generate()
    write_text(
        seed_dir / "id_ed25519",
        ed_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8"),
    )
    write_text(
        seed_dir / "id_ed25519.pub",
        ed_key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH,
        )
        .decode("utf-8")
        + " keyvault-ed@example\n",
    )

    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "KeyVault Operations"),
            x509.NameAttribute(NameOID.COMMON_NAME, "keyvault.local"),
        ]
    )
    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(rsa_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(rsa_key, hashes.SHA256())
    )
    write_text(seed_dir / "server-ca.pem", cert.public_bytes(serialization.Encoding.PEM).decode("utf-8"))

    trust_store = {
        "trusted_certificates": [
            {
                "name": "keyvault.local",
                "fingerprint": cert.fingerprint(hashes.SHA256()).hex(),
                "source": "seed",
            }
        ]
    }
    write_text(seed_dir / "trust_store.json", json.dumps(trust_store, ensure_ascii=False, indent=2))


def copy_seed(seed_dir: Path, target_dir: Path, force: bool = False) -> None:
    if not seed_dir.exists():
        raise FileNotFoundError(f"missing seed directory: {seed_dir}")
    if target_dir.exists() and force:
        shutil.rmtree(target_dir)
    if target_dir.exists():
        return
    shutil.copytree(seed_dir, target_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare KeyVault benchmark test data.")
    parser.add_argument("--seed-dir", default="keyvault/keyvault_data_seed")
    parser.add_argument("--copy-to", default="")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    seed_dir = Path(args.seed_dir)
    generate_seed(seed_dir, force=args.force)
    if args.copy_to:
        copy_seed(seed_dir, Path(args.copy_to), force=args.force)
    print(seed_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
