# Demo Script

## 1. Start With The Ocean Problem

Mixed layer depth, or MLD, is the depth of the ocean surface layer that is well mixed by wind, waves, cooling, and turbulence. It matters because it controls how much heat, momentum, and biological material are available near the surface.

For hurricanes, a deeper mixed layer can provide more ocean heat to a storm. For Navy and ocean operations, MLD affects sound propagation and underwater vehicle behavior. For ocean scientists, it is a sensitive diagnostic of fronts, eddies, and upper-ocean dynamics.

## 2. Explain The Modeling Gap

Ocean forecast models like RTOFS give us complete spatial coverage, but they have biases. Those biases are often worst near energetic features like fronts and eddies, where the real ocean changes over short distances.

In-situ observations, such as Argo profiles, measure the real ocean, but they are sparse. A nearby profile may be accurate where it was measured but not exactly at the user query point.

The product idea is to combine both: use the model for spatial context, use observations for reality checks, and use ML to learn the correction pattern.

## 3. Explain Why We Built A Historical Replay

The long-term vision is a live service. But for the current prototype, reliable live in-situ support is not ready yet. Instead of pretending the system is operational, we built a historical replay sandbox.

We chose a Jul-Aug 2025 window where we have same-day RTOFS fields and dense enough Argo observations. The model is trained only on data before the replay window, and the app replays the held-out period as if it were live.

This lets us demonstrate the complete product loop honestly.

## 4. Open The Dashboard

Open:

```text
http://127.0.0.1:5174/
```

Point out that the map is centered on the Gulf of Mexico, because that is the initial region of interest for the MLD/frontogenesis use case.

## 5. Choose A Replay Date

Select one of the available replay dates. The app is constrained to the frozen historical sandbox window.

This is important: the date selector is not decorative. It controls which same-day RTOFS field and which holdout observations are used.

## 6. Show The Map Layers

Walk through the toggles:

- Model field: where RTOFS thinks the mixed layer is deep or shallow
- Correction hotspots: where the ML model applies the biggest correction
- Final corrected field: the resulting estimate after correction
- All in-situ points: the actual replay observations available that day

The visual goal is the aha moment: the user can see not just a number, but the spatial correction story.

## 7. Click A Query Point

Click a point in the Gulf.

The panel should show:

- Corrected MLD estimate
- Raw model MLD
- Correction magnitude
- Confidence
- Nearby observations used for provenance

Explain that the response is designed to answer both:

```text
What is the best estimate here?
```

and:

```text
Why should I believe it?
```

## 8. Explain Prototype Status

Be clear that this is prototype-ready, not production-ready.

The prototype proves the app/product pattern:

- Query
- Model estimate
- Observation-informed correction
- Confidence
- Provenance
- Map explanation

The next scientific step is better validation and broader live in-situ integration. The next product step is turning this replay sandbox pattern into a reliable operational data path.
