# Why Earth visibility matters

A lander can talk to Earth directly only when Earth is above the horizon. When it is not, the lander needs a relay satellite or must wait.

LunaNav uses two numbers:

- **Earth visibility (%)**: the share of the window during which the centre of Earth is above the local horizon.
- **Longest comms gap (h)**: the longest uninterrupted period without Earth in view.

**Important:** this is *geometric line of sight only*. It does not tell you whether a radio link would actually work (antenna, power, data rate, ground-station availability). Earth in view is necessary for direct communication, not sufficient.

Some sites never see Earth (the far side of the Moon): they always need a relay. LunaNav says so instead of simply giving a low score.
