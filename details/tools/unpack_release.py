#!/usr/bin/env python3
from __future__ import annotations
import base64,hashlib,pathlib,tarfile,sys
ACTIVE_RELEASE='v2.4'
EXPECTED_SHA256='9c84aa48a42d0b8161673cc8d8323a57cdfafd81511192cf3b5666317f192020'
def main():
 d=pathlib.Path(__file__).resolve().parents[1]; r=d/'releases'/ACTIVE_RELEASE; data=base64.b64decode((r/f'machine-state-{ACTIVE_RELEASE}.tar.gz.b64').read_text(encoding='ascii')); actual=hashlib.sha256(data).hexdigest(); assert actual==EXPECTED_SHA256,(actual,EXPECTED_SHA256); target=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else r/f'{ACTIVE_RELEASE}-unpacked'; target.mkdir(parents=True,exist_ok=True); tmp=target/f'machine-state-{ACTIVE_RELEASE}.tar.gz'; tmp.write_bytes(data); tf=tarfile.open(tmp,'r:gz'); tf.extractall(target); tf.close(); tmp.unlink(); print(target)
if __name__=='__main__': raise SystemExit(main())
