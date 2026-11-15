# Five-domain dataset and artifact provenance

The supplied archive includes the synthetic India-wide `pricing_data.csv` used
by the original India fare-multiplier model. It does not include the empirical
domain-specific training CSVs described in the BDP project explanation.

| Domain | Data/artifact in this archive | BDP demand model |
|---|---|---|
| Ride | India synthetic fare-pricing data only | Not restored |
| Food | No Zomato/Swiggy raw data | Not restored |
| E-commerce | No raw product time series | Not restored |
| Entertainment | No raw ticket interval data | Not restored |
| Travel | No validated travel-booking data | Not restored |

Historical metrics in project notes are not copied into model artifact folders.
Train each domain with an appropriate, legally usable dataset and record its
source, license, time coverage, target definition and preprocessing.
