"""Public interface for keypairs module."""
from secrets import token_bytes
from typing import Any, Dict, Optional, Tuple

from typing_extensions import Final

from xrpl import CryptoAlgorithm, addresscodec
from xrpl.keypairs import ed25519, secp256k1
from xrpl.keypairs.exceptions import XRPLKeypairsException
from xrpl.keypairs.helpers import get_account_id

# using Any type here because the overhead of an abstract class or protocol
# for these two modules would be overkill and we'll raise in tests if they do
# not satisfy the implicit interface
_ALGORITHM_TO_MODULE_MAP: Final[Dict[CryptoAlgorithm, Any]] = {
    CryptoAlgorithm.ED25519: ed25519,
    CryptoAlgorithm.SECP256K1: secp256k1,
}
# Ensure all CryptoAlgorithms have a module
assert len(_ALGORITHM_TO_MODULE_MAP) == len(CryptoAlgorithm)

_VERIFICATION_MESSAGE: Final[bytes] = b"This test message should verify."


def generate_seed(
    entropy: Optional[str] = None,
    algorithm: CryptoAlgorithm = CryptoAlgorithm.ED25519,
) -> str:
    """
    Generates a seed suitable for use with derive.

    Args:
        entropy: Must be at least addresscodec.SEED_LENGTH bytes long and
            will be truncated to that length
        algorithm: CryptoAlgorithm to use for seed generation

    Returns:
        A seed suitable for use with derive
    """
    if entropy is None:
        parsed_entropy = token_bytes(addresscodec.SEED_LENGTH)
    else:
        parsed_entropy = bytes(entropy, "UTF-8")[: addresscodec.SEED_LENGTH]
    return addresscodec.encode_seed(parsed_entropy, algorithm)


def derive_keypair(seed: str, validator: bool = False) -> Tuple[str, str]:
    """
    Given seed, which can be generated via `generate_seed`, returns
    public and private keypair.

    Args:
        seed: Value from which to derive keypair
        validator: Whether the keypair is a validator keypair.

    Returns:
        A public and private keypair.

    Raises:
        XRPLKeypairsException: If the derived keypair did not generate a
            verifiable signature.
    """
    decoded_seed, algorithm = addresscodec.decode_seed(seed)
    module = _ALGORITHM_TO_MODULE_MAP[algorithm]
    public_key, private_key = module.derive_keypair(decoded_seed, validator)
    signature = module.sign(_VERIFICATION_MESSAGE, private_key)
    if not module.is_valid_message(_VERIFICATION_MESSAGE, signature, public_key):
        raise XRPLKeypairsException(
            "Derived keypair did not generate verifiable signature",
        )
    return public_key, private_key


def derive_classic_address(public_key: str) -> str:
    """
    Returns the classic address for the given public key. See
    https://xrpl.org/cryptographic-keys.html#account-id-and-address
    for more information.

    Args:
        public_key: Public key from which to derive address.

    Returns:
        Classic address corresponding to public key.
    """
    account_id = get_account_id(bytes.fromhex(public_key))
    return addresscodec.encode_classic_address(account_id)


def sign(message: bytes, private_key: str) -> str:
    """
    Given message and private key returns signed message.

    Args:
        message: Message to sign.
        private_key: Private key generated using any of the supported
            CryptoAlgorithm.

    Returns:
        Signed message.
    """
    return (
        _get_module_from_key(private_key)
        .sign(
            message,
            private_key,
        )
        .hex()
        .upper()
    )


def is_valid_message(message: bytes, signature: bytes, public_key: str) -> bool:
    """
    Returns True if message is valid given signature and public key.

    Args:
        message: Message to check against signature.
        signature: Signature of message as created with private key.
        public_key: Public key corresponding to private key used to generate
            signature.

    Returns:
        True if message is valid given signature and public key.
    """
    return _get_module_from_key(public_key).is_valid_message(
        message,
        signature,
        public_key,
    )


def _get_module_from_key(key: str) -> Any:
    if key.startswith(ed25519.PREFIX):
        return _ALGORITHM_TO_MODULE_MAP[CryptoAlgorithm.ED25519]
    return _ALGORITHM_TO_MODULE_MAP[CryptoAlgorithm.SECP256K1]