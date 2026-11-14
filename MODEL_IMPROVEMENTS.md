# Landslide Risk Mapper — Model v2.0

## What changed

The original risk engine was a simple linear weighted sum. Model v2.0 keeps that transparent baseline but adds bounded effects that better represent landslide triggering conditions.

### 1. Continuous slope susceptibility
The slope score now changes smoothly instead of relying on category boundaries. The 30–45° range receives the strongest shallow-slide/debris-flow sensitivity, while very steep faces remain highly hazardous without assuming that every >45° face behaves as a shallow soil slide.

### 2. Slope × rainfall interaction
When both slope and rainfall are high, the model adds a small capped synergy term. This captures the important triggering interaction between gravitational driving stress and rainfall-induced saturation.

### 3. Rainfall intensity bonus
A capped bonus is applied to high hourly rainfall intensity so short cloudburst-like events can influence the result without dominating the model.

### 4. Historical evidence
Nearby documented landslides are used as supporting evidence. Distance to the nearest catalog event is more important than raw event count, and the total adjustment is capped at 5 points.

### 5. Data confidence
The API now returns a confidence score and label based on whether elevation/rainfall data are live, fallback, or simulated.

### 6. Rainfall observation fix
The live Open-Meteo path now requests seven past days and uses completed daily observations for the 24/48/72-hour trigger windows, avoiding a partial current day or forecast value being treated as observed rainfall.

## Validation

The repository contains only a small curated historical catalog (16 records) rather than a large labelled dataset with matched historical terrain/rainfall features. Therefore, this deliverable does **not** claim a fabricated percentage accuracy or train a synthetic classifier and present it as ground truth.

The included tests verify:
- score bounds and risk categories;
- weight normalization;
- monotonic/continuous slope scoring;
- bounded historical evidence;
- confidence output;
- Python syntax/compilation.

For publication-grade accuracy claims, the next step is to train and cross-validate against a substantially larger labelled landslide inventory with time-matched rainfall, DEM-derived slope, lithology/land-cover and drainage variables.
