# Favorite / Transfer Contract v0.1

Archicad Favorites store dimensions, Classification and Properties, but Element Transfer Settings let the project control which settings are applied.

For SBIM automation this creates two separate concepts:

1. Favorite = verified TYPE definition.
2. Executor request = PLACEMENT / instance geometry.

Default automation transfer set: SBIM_TYPE_APPLY.

The agent should select a Favorite by StableTypeID, apply the intended transfer behavior explicitly, then set or preserve placement-specific geometry (length, endpoints, story, offsets, rotation, polygon etc.) and validate through Model Dump.

Important Archicad nuance:
- named Transfer Sets are stored with the project;
- the user's chosen default Transfer Set for Favorites is stored locally as a user preference.

Therefore the automation layer may never assume that the user's local default is correct.

A released Favorite must pass:
- type lookup by StableTypeID
- no suffixed duplicate name
- correct Layer
- correct Building Material/Composite/Profile
- correct Classification/Properties
- controlled transfer behavior
- post-application Model Dump check

See favorite-transfer-policy-v0.1.yaml and favorite-blueprints-v0.1.yaml.
