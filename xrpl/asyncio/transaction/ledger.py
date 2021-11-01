"""High-level methods that fetch transaction information from the XRP Ledger."""

from typing import Any, Dict, Optional, cast

import xrpl.asyncio.clients.client as client
import xrpl.asyncio.clients.exceptions as exception
from xrpl.models.requests import Tx
from xrpl.models.response import Response


async def get_transaction_from_hash(
    tx_hash: str,
    client: client.Client,
    binary: bool = False,
    min_ledger: Optional[int] = None,
    max_ledger: Optional[int] = None,
) -> Response:
    """
    Given a transaction hash, fetch the corresponding transaction from the ledger.

    Args:
        tx_hash: the transaction hash.
        client: the network client used to communicate with a rippled node.
        binary: If true, return transaction data and metadata as binary
            serialized to hexadecimal strings. If false, return transaction data and
            metadata as JSON. The default is false.
        min_ledger: Use this with max_ledger to specify a range of up to
            1000 ledger indexes, starting with this ledger (inclusive). If the server
            cannot find the transaction, it confirms whether it was able to search all
            the ledgers in this range.
        max_ledger: Use this with min_ledger to specify a range of up to
            1000 ledger indexes, ending with this ledger (inclusive). If the server
            cannot find the transaction, it confirms whether it was able to search
            all the ledgers in the requested range.

    Returns:
        The Response object containing the transaction info.

    Raises:
        XRPLRequestFailureException: if the transaction fails.
    """
    response = await client.request_impl(
        Tx(
            transaction=tx_hash,
            binary=binary,
            max_ledger=max_ledger,
            min_ledger=min_ledger,
        )
    )
    if not response.is_successful():
        result = cast(Dict[str, Any], response.result)
        raise exception.XRPLRequestFailureException(result)
    return response
