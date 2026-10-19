# APA №2 16Z — SOURCE проверки 07–09
07. PR175 preserve_guarded_save: exclusive byte snapshot, before/after SHA, protected source checks. SOURCE: https://github.com/dvikt33-ux/safe-bim-layer/pull/175 . Решение REUSE; следующий OFFLINE race test.
08. PR173 LIVE-02 receipt: 69→119 GUID, two Hotlink instances, one batch, one save, reopenVerified=true. SOURCE: https://github.com/dvikt33-ux/safe-bim-layer/pull/173 . LIVE receipt exists; independent binary ACCEPTED not verified.
09. PR173 persistence-provenance: saved snapshot differs from later scratch; cause unattributed. SOURCE: https://github.com/dvikt33-ux/safe-bim-layer/pull/173 . REJECT late scratch as proof; next independent read-only SHA, no replay.
