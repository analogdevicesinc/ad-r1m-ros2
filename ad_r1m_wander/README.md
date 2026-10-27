# ad_r1m_wander

Minimal reactive wander behaviour for the AD-R1M. Subscribes to `/scan` (from the ToF
camera via `depthimage_to_laserscan`) and publishes velocity commands on `/cmd_vel`.

- Looks at a forward sector (`front_angle_deg`, default ±20°) and reduces it to one
  distance with `method`: `mean` (default), `min`, or `percentile`.
- Distance > `clear_distance` → drive forward. Otherwise stop and rotate (toward the
  side with more room) until the distance exceeds `clear_distance + clear_hysteresis`.
- Stops if scans stop arriving (`scan_timeout`) or too few valid readings (`min_valid_fraction`).
- `/cmd_vel` is the `nav` input of `twist_mux` (priority 30), so joystick (50) and
  keyboard (40) commands override it.
- Publishes `TwistStamped` when `use_stamped` is true (jazzy and later), `Twist` otherwise.

```bash
ros2 launch ad_r1m_wander wander.launch.py method:=mean
```

Do not run alongside Nav2, which also publishes on `/cmd_vel`.
