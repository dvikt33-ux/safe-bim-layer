#!/usr/bin/env python3
from __future__ import annotations
import base64,hashlib,pathlib,tarfile,sys
ACTIVE_RELEASE='v2.5'
EXPECTED_SHA256='c3c420e9c51522012c06457036d4e092fd1c5c76e87babacd02d22420e5934c0'
def main():
 d=pathlib.Path(__file__).resolve().parents[1]; r=d/'releases'/ACTIVE_RELEASE; data=base64.b64decode((r/f'machine-state-{ACTIVE_RELEASE}.tar.gz.b64').read_text(encoding='ascii')); actual=hashlib.sha256(data).hexdigest(); assert actual==EXPECTED_SHA256,(actual,EXPECTED_SHA256); target=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else r/f'{ACTIVE_RELEASE}-unpacked'; target.mkdir(parents=True,exist_ok=True); tmp=target/f'machine-state-{ACTIVE_RELEASE}.tar.gz'; tmp.write_bytes(data); tf=tarfile.open(tmp,'r:gz'); tf.extractall(target); tf.close(); tmp.unlink(); print(target)
if __name__=='__main__': raise SystemExit(main())
