# Sync Strategy

## Goal

Allow users to adapt translated subtitles to a different release without needing to understand subtitle timing math.

## Delivery Levels

### Level 1: Global Offset

Shift all subtitle timestamps earlier or later by a single value. This is the MVP sync feature and should cover many real-world cases.

### Level 2: Linear Stretch

Support stretch or compression when releases differ by pacing or frame-rate conversion behavior.

### Level 3: Manual Anchors

Let the user place known timing anchors and interpolate the rest of the timeline from those anchors.

### Level 4: Audio-Assisted Sync

Use speech and silence boundaries to improve alignment automatically.

## UX Modes

### Easy Mode

- try auto sync
- shift earlier or later
- fine tune with preview

### Advanced Mode

- global offset
- stretch percent
- anchor points
- drift visualization
- audio matching controls

## Data Needed

- source timeline
- target timeline adjustments
- optional anchor points
- preview snapshots for validation

## Constraint

Advanced sync must not delay the first release. The text pipeline and simple review path come first.

