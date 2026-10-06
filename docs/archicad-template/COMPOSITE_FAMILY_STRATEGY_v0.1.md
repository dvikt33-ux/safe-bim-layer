# Composite and Favorite Family Strategy v0.1

The Core template must not pretend that one wall buildup is universally valid for IZHS, MKD or TRC.

A released Archicad Composite is static: its total thickness is the sum of its Building Material skins. Therefore it is created only after the exact product/system dimensions and project calculations are known.

## Important ceramic masonry note

GOST 530-2012 defines 1NF brick as 250x120x65 mm and contains a table of multiple ceramic-stone sizes/formats. Commercial names such as "Porotherm 12" are not a safe universal mapping from NF to wall thickness. For example, market products called Porotherm 12 are typically partition products with an approximately 120 mm wall dimension, while exterior ceramic blocks are commonly product families identified by actual wall dimensions such as 380/440/510 mm.

Therefore:
- no Core Favorite named merely "12NF exterior wall";
- product manufacturer/model + actual working dimension must be verified;
- thermal conductivity and thermal resistance are sourced/calculated separately;
- the template may contain a family blueprint without creating the final Composite until verification.

## Multi-element assemblies

Prefer multi-element representation where systems need independent control:
- ventilated facade;
- brick cladding with real cavity/ties;
- structural frame + infill + facade;
- structural slab + architectural floor buildup;
- complex flat-roof buildup when structural and architectural responsibility is separated.

This keeps layer control, quantities, openings, coordination and junction behavior explicit.

## Generated Favorites

GPT should not invent the final type from raw parameters.

Workflow:
1. choose family blueprint;
2. resolve product/system/calculation inputs;
3. generate exact Building Materials/Composite/Profile if needed;
4. create Favorite;
5. assign StableTypeID;
6. run junction/section/quantity tests;
7. promote Favorite from CANDIDATE to VERIFIED.

See composite-family-registry-v0.1.yaml.
