from pathlib import Path

from .db import (
    CreateLogDBForHash
)

REPO = Path.home() / "btc" / "bitcoin"
HASH = "a4157fc24a29118b1c9d1ac5b7977104217bcee9"

db = CreateLogDBForHash(REPO, HASH)

def gbt_callback(entry: LogEntry, dict: dict) -> None:
    raise NotImplemented

# LogDebug(BCLog::CMPCTBLOCK, "Peer %d sent us a GETBLOCKTXN for block %s, sending a BLOCKTXN with %u txns. (%u bytes)\n", pfrom.GetId(), block.GetHash().ToString(), resp.txn.size(), tx_requested_size);
# Should it be fuzzy or there be a fuzzy option instead of regex?
gbt_pattern = db.msg_with_args(
    "Peer.*sent us a GETBLOCKTXN",
    [
        "peerid", "blockhash", "txn_count", "txn_size"
    ],
    gbt_callback
)
