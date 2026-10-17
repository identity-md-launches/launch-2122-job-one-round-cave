# State Gate

Check whether **proven Ethereum state meets your conditions**, without trusting
an RPC's value claims or a saved success report. Python 3.9+ standard library
only. Keep the sibling `state-witness/` folder beside this tool.

One command from the repository root demonstrates it offline on the real,
historical ZTO/IMD Uniswap v4 pool witness:

```sh
python3 -B line-2/tools/state-gate/gate.py demo
```

When tried on 2026-10-17, all four conditions passed: the PoolManager account
exists, its stored code hash matches the caller policy, the sampled pool slot
exists, and its raw uint256 value equals
`5142201741628931703247188819393128666781505348170750299503867444289`.
The slot is `keccak256(abi.encode(poolId, uint256(6)))` for the assigned ZTO/IMD
pool, inherited from the earlier real proof. This demonstration's fixed root is
an RPC observation, not an independently authenticated checkpoint. No new chain
data was fetched. The pool layout and its association with ZTO/IMD remain
external assumptions; this tool checks raw state without interpreting a price.

To see **valid evidence fail a condition**, run:

```sh
python3 -B line-2/tools/state-gate/gate.py demo --reject
```

That command deliberately expects a zero pool word. It prints `verified: true`
and `accepted: false`, then exits **3**. This is a condition mismatch, not a
broken proof. A malformed or incomplete proof instead exits **1**, prints error
JSON to stderr and no decision report to stdout. Exit **0** means verified and
accepted; argparse errors exit **2**. Consumers must inspect these statuses.

## Check your own evidence

Review your policy and independently authenticate the state root first. The
policy never supplies the root; the `check` command requires it explicitly:

```sh
python3 -B line-2/tools/state-gate/gate.py check \
  line-2/tools/state-gate/examples/pool-policy.json \
  line-2/tools/state-witness/examples/zto-pool-mainnet.json \
  --state-root 0x70c13580735123b57c0a9a24692875f4ef366b04c69d92af9f539561e626d512
```

This is the same historical example, not a current-state check. For your own
work, replace **all three inputs** with reviewed conditions, a corresponding
`state-witness/1` witness and your independently trusted root. The verifier
binds the account and exact requested slot set to the policy; metadata such as
the witness's address, chain label and block root cannot override them.

The policy has exactly four fields: `format` (`state-gate/1`), `address`
(20-byte hex), `account` (an object) and `storage` (an array). At least one
condition is required. Unknown fields are rejected.

| Conditions | Meaning |
| --- | --- |
| `account.exists` | Exact boolean account existence |
| `account.nonce`, `account.nativeBalanceWei` | Numeric conditions |
| `account.codeHash`, `account.storageRoot` | Exact 32-byte commitments, case-insensitive hex |
| `storage[].slot` | Required uint256 hex key, unique numerically |
| `storage[].exists` | Exact boolean storage inclusion |
| `storage[].value` | Numeric condition on the raw unsigned word |

Each storage entry requires `exists`, `value`, or both. Numeric conditions are
either `{"equals":"123"}` or an inclusive range such as
`{"min":"100","max":"200"}`. Either range endpoint may be omitted.
Values must be canonical unsigned decimal **strings** fitting uint256; empty
conditions, JSON numbers, booleans, signs, leading zeros and inverted ranges
are rejected. Arithmetic uses Python integers throughout. Proven storage
absence has value zero and `exists: false`; missing proof nodes are errors.
An account-only policy requires an account-only witness with no storage rows.

Successful output includes every condition's actual value, expected value and
pass flag. `policySha256` hashes the parsed policy serialized as sorted-key,
compact ASCII JSON; it identifies exact policy spelling and array order, not
the original file bytes or a signature. It is useful for recording what was
checked, but does not authenticate the policy. No `accepted` result is produced
until **all requested proofs** verify, even if an earlier condition fails.

Inputs and symlink targets must remain within the current working directory.
Policy files are bounded to 64 KiB; witness files to 1 MB, 64 slots and 128
nodes per proof. Duplicate JSON keys and non-finite constants are rejected.
The tool reads workspace inputs and prints JSON only. It never invokes the
ancestor's capture helpers, accesses environment variables, opens wallets,
signs, sends transactions, pays, posts or deploys. No installation is needed.

## Checks and limits

All 15 tests passed, including the real pool and ZTO absence witnesses,
inclusive ranges, large exact integers, rejected conditions, corrupted proofs,
wrong roots/accounts/slot sets, malformed policies, metadata independence,
deterministic reports, input immutability and CLI exit behavior:

```sh
python3 -B -m unittest discover -s line-2/tools/state-gate -p 'test_*.py' -v
```

This is a predicate over sampled proven state. It does not authenticate Ethereum
consensus, canonicality, finality or freshness, prove a storage layout, resolve
proxy behavior, establish token balances from unknown slots, or predict whether
a future transaction will succeed. Account native ETH is not token balance or
pool liquidity. A code hash proves stored commitment identity, not safe code.
The caller must trust both the root and the conditions. No new coin is needed.
