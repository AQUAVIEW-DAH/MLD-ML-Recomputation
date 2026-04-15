# In-Situ Profile Requirements For MLD Computation

The current prototype computes observed mixed layer depth using a temperature-threshold method relative to a 10m reference depth. That creates specific requirements for any in-situ data source we want to use.

## Required Fields

A profile needs:

- Latitude
- Longitude
- Timestamp
- Depth or pressure coordinate
- Temperature values
- Platform/source identity when possible

Surface-only observations are not enough. The data must be a vertical profile.

## Current MLD Definition

The current observed MLD label is:

```text
MLD = first depth below 10m where abs(T(depth) - T(10m)) >= 0.2C
```

This is a standard, simple temperature-threshold definition and is appropriate for the prototype. Density-based MLD can come later.

## Vertical Coverage Requirements

A usable profile must:

- Reach the 10m reference depth or bracket it closely enough for interpolation
- Continue below 10m
- Have enough valid temperature-depth levels to detect the 0.2C threshold
- Avoid obvious malformed or duplicate depth/temperature data

Profiles that start deeper than 10m may look useful, but they cannot produce the current comparable label because `T(10m)` is missing.

## Current Quality Filters

The current GoM prototype generally keeps labels when:

- The profile is inside the Gulf of Mexico domain
- The observed MLD is computable
- The observed MLD is in the sane prototype range of 10-100m
- Same-day RTOFS data exists for the profile date
- RTOFS feature extraction succeeds at the profile location

The 100m cap is a pragmatic prototype sanity filter, not a universal oceanographic truth.

## Suitable Sources

Good candidates:

- Argo GDAC profiles
- WOD XBT/CTD/PFL/GLD/APB profiles when they satisfy the 10m and GoM filters
- IOOS/SECOORA ERDDAP glider profiles when grouped by real profile/deployment

Usually not enough by themselves:

- Surface buoys
- Coastal stations
- Satellite SST
- HF radar
- Surface-only ERDDAP datasets

## Important Interpretation

Sparse final training rows do not always mean the raw source is sparse. Many profiles are removed after applying the full chain of requirements:

- GoM domain
- Profile-shaped depth-temperature data
- 10m reference coverage
- Valid MLD range
- Same-day RTOFS availability
- Successful feature extraction

This distinction matters when evaluating future in-situ providers.
