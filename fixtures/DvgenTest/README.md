# DvgenTest fixture

Reference solution generated with the dv-generate templates: one table (`dvgen_widget`), a view pair, a main form, five environment variables (Text, Decimal, Boolean, JSON, Secret) and one connection reference.

Verified 2026-10-18 (re-verified by tests/run.sh): imports as an unmanaged solution into a dev environment (platform 9.2.26092.158), re-exports with every component intact, and exports as managed from there. It does not cover picklist/boolean/decimal columns or the AppModule.

Build and import: `./pack.sh`, then `pac solution import --path DvgenTest.zip`.
