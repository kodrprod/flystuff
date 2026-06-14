# Autonomous Snack-Delivery Drone — Simulation

A complete, runnable software simulation of a hobby drone that flies a snack
(say, a chocolate bar) from a home base to a friend's **balcony**, drops it
precisely onto a printed **ArUco marker** using a real downward camera + OpenCV
computer vision, then flies home and lands.

Everything runs **natively on your M1 Mac** in pure Python. There is no Docker,
no Linux, no ROS, no game engine — just a handful of `pip` packages.

This README is written assuming you have **never used Terminal before**. Follow
it top to bottom and copy-paste each command block exactly.

---

## What the simulation actually does

It mirrors the real-world system you eventually want to build:

1. **A friend "taps a button"** → sends their GPS location, the balcony's marker
   ID, and the balcony height. (`dispatch.py`)
2. **The dispatch station** turns that into a flight mission and launches the
   drone. (`dispatch.py` → `mission.py`)
3. **Cruise on GPS.** The drone climbs and flies to the building. GPS is only
   good to a few meters — not nearly precise enough to hit a balcony. (`sensors.py`)
4. **Vision takeover.** Above the balcony, the drone's downward camera sees the
   ArUco marker. **Real OpenCV ArUco detection + `solvePnP` pose estimation**
   (no machine learning) tells it exactly where the marker is and how high above
   it the drone is. (`camera_sim.py` renders the image, `vision.py` detects it.)
5. **Precision align + descend.** PID controllers centre the drone over the
   marker and lower it to a safe release height, fighting wind the whole time.
   (`control.py`, `mission.py`)
6. **Drop, ascend, return home, land.** (`drop.py`, `mission.py`)

The drone-command interface (`arm()`, `takeoff()`, `goto_local()`,
`set_velocity_body()`, `actuate_servo()`, …) deliberately mimics **MAVSDK /
MAVLink**, so the same vision + control + mission code can later drive a real
drone (see *Where this goes next* at the bottom).

### Tested results (measured, not promised)

Across 5 random seeds, headless:

| Metric | Result |
| --- | --- |
| Snack drop error (vision-guided) | **mean 6.7 cm, worst 10.4 cm** (target ≤ 20 cm) |
| What a GPS-only drop would miss by | **~2.5 m on average** |
| Accuracy improvement from vision | **~36×** |
| Return-to-home landing (GPS only) | mean ~1.7 m |
| Pass rate | **5 / 5** |

The point is visible right there: GPS alone misses by meters; the camera+vision
stage brings it down to **centimeters**.

---

## 1. Install Python 3 (one time)

Your Mac may already have Python 3. Check first.

**Open Terminal:** press `Cmd + Space`, type `Terminal`, press `Return`. A window
with a text prompt appears. You type commands here and press `Return` to run them.

Copy-paste this and press `Return`:

```
python3 --version
```

- If it prints something like `Python 3.10.6` (anything 3.10 or newer), you're
  set — **skip to step 2**.
- If it says "command not found" or a version older than 3.10, install Python:

  Go to **https://www.python.org/downloads/macos/**, download the latest
  **"macOS 64-bit universal2 installer"** (the recommended one — it's built for
  Apple Silicon), open the downloaded `.pkg`, and click through the installer.
  Then **close and reopen Terminal** and run `python3 --version` again.

> Recommended: Python **3.12**. The pinned package versions in
> `requirements.txt` all install as ready-made wheels on Python 3.10–3.13, so no
> compiler is involved.

---

## 2. Set up the project

You have two options. **Option A is the easy one.**

### Option A — the one-step setup script

In Finder, open this project folder, then **double-click `setup_mac.command`**.
A Terminal window opens and installs everything automatically.

If macOS blocks it ("cannot be opened because it is from an unidentified
developer"), do this once: **right-click** `setup_mac.command` → **Open** →
**Open**. Or just use Option B below.

### Option B — type the commands yourself

This does exactly what the script does. Copy-paste **one block at a time**,
pressing `Return` after each, and wait for each to finish.

**2.1 — Go into the project folder.** Type `cd ` (with a space), then drag the
`drone_delivery_sim` folder from Finder onto the Terminal window (this pastes its
path), then press `Return`. It will look like this:

```
cd "/Users/andreas/Desktop/Code/Flystuff/drone_delivery_sim"
```

**2.2 — Create a private Python environment** (a "virtual environment" — a
sandbox for this project's packages so they don't affect anything else):

```
python3 -m venv .venv
```

**2.3 — Activate it.** You must do this every time you open a new Terminal to
work on the project. After it runs, your prompt shows `(.venv)` at the start:

```
source .venv/bin/activate
```

**2.4 — Install the required packages:**

```
pip install -r requirements.txt
```

This downloads NumPy, OpenCV (with ArUco), Matplotlib and the video tools. It
takes a minute. You're done when it returns to the prompt with no red errors.

---

## 3. Run the simulation

Make sure your prompt shows `(.venv)` (if not, re-run `source .venv/bin/activate`
from inside the project folder). Then:

```
python main.py
```

**What you'll see:**

- A **dashboard window** opens and animates the whole flight: a top-down map
  (home → balcony → home), a side view showing the balcony at its height, the
  **live camera image with the detected marker outlined in green**, and a
  telemetry panel (state, altitude, height above marker, offset, battery, wind).
- The **Terminal** prints each mission phase (`CRUISE_TO_WAYPOINT`,
  `SEARCH_MARKER`, `PRECISION_ALIGN`, `DESCEND`, `DROP`, …) and a results summary
  at the end (drop error, GPS-only comparison, etc.).
- A **demo video** is saved to `outputs/mission_demo.mp4` (or
  `outputs/mission_demo.gif` if your machine can't make an MP4) so you can
  re-watch and share it.

Close the dashboard window to exit.

**Variations:**

```
python main.py --seed 12      # a different random scenario (wind/GPS draw)
python main.py --headless     # no window — just compute and save the video
python main.py --no-video     # fastest — skip the video file
```

---

## 4. Run the tests

These prove the vision and the full mission actually work. With `(.venv)` active
and inside the project folder, run each:

```
python tests/test_vision.py
```
```
python tests/test_smoke.py
```
```
python tests/test_mission.py
```

`test_mission.py` flies several full missions and prints a report with the drop
accuracy and pass rate. (If you happen to have `pytest` installed, you can also
run `python -m pytest tests/ -s`, but it is not required.)

---

## 5. Change the scenario

Open **`config.py`** in any text editor — every adjustable number is in there
with a comment. The fun ones to try:

- `balcony_height_m` — how high the balcony is (e.g. change `8.0` to `15.0`).
- `wind_base_mps` and `wind_turbulence_mps` — make it windier and watch the PID
  fight harder.
- `gps_bias_sigma_m` — make GPS worse and see vision still nail the drop.
- `marker_size_m`, `marker_id` — the printed marker.
- `release_height_above_balcony_m` — how high above the floor it drops from.

Save the file and re-run `python main.py`. No other changes needed.

---

## 6. Troubleshooting (common Mac gotchas)

**The dashboard window doesn't appear / "no display" / it just hangs.**
This is a Matplotlib backend issue. `main.py` already tries the native `MacOSX`
backend first, then `TkAgg`. If you still get no window, run headless and watch
the saved video instead:
```
python main.py --headless
```
If you *want* a live window and the native one fails, install Tk support and try
again: `pip install pyqt5` then `MPLBACKEND=QtAgg python main.py`. You can also
force a backend, e.g. `MPLBACKEND=TkAgg python main.py`.

**`ModuleNotFoundError: No module named 'cv2.aruco'` or `module 'cv2' has no
attribute 'aruco'`.** You have the wrong OpenCV package. You need
**`opencv-contrib-python`**, not `opencv-python`. Fix it cleanly:
```
pip uninstall -y opencv-python opencv-contrib-python
pip install opencv-contrib-python==4.13.0.92
```
Do **not** have both installed at once — that's the usual cause.

**The video isn't created / MP4 fails.** MP4 needs `imageio-ffmpeg` (it's in
`requirements.txt`). If MP4 export ever fails on your machine, the program
automatically falls back to writing an animated **GIF** at
`outputs/mission_demo.gif` and tells you so — that's expected, not an error.

**`command not found: python` or packages "not found" when running.** You forgot
to activate the environment. From inside the project folder run
`source .venv/bin/activate` (your prompt should then show `(.venv)`), and use
`python` (not `python3`) once activated.

**A note on OpenCV versions (already handled).** OpenCV ≥ 4.7 uses
`cv2.aruco.ArucoDetector` + `cv2.aruco.generateImageMarker()`, while older
versions use `cv2.aruco.detectMarkers()` + `cv2.aruco.drawMarker()`. The code in
`vision.py` detects which API your installed OpenCV has and uses the right one
automatically, so either works.

---

## 7. How the code is organized

```
drone_delivery_sim/
  README.md            <- you are here
  requirements.txt     <- pinned, Apple-Silicon-friendly package versions
  setup_mac.command    <- one-step setup (double-click or `bash setup_mac.command`)
  config.py            <- ALL tunable scenario parameters, in one place
  main.py              <- entry point: runs one full mission with the dashboard
  src/
    geo.py             <- GPS lat/lon <-> local meters helpers
    dispatch.py        <- DeliveryRequest -> MissionPlan ("tap a button" backend)
    drone.py           <- flight physics + MAVSDK-style command interface
    sensors.py         <- simulated noisy GPS, ToF rangefinder, barometer
    camera_sim.py      <- renders the synthetic downward camera image
    vision.py          <- REAL OpenCV ArUco detect + solvePnP (the hardware part)
    control.py         <- PID controllers (centering + descent)
    planner.py         <- obstacle-avoiding route planner (A* + reactive steering)
    mission.py         <- the mission state machine + failsafes
    drop.py            <- payload release + landing-error model
    visualize.py       <- matplotlib dashboard + MP4/GIF export
  tests/
    test_vision.py     <- detection + pose accuracy, graceful failure
    test_mission.py    <- full missions, drop accuracy, pass rate
    test_smoke.py      <- imports, short run, a video file is produced
  outputs/             <- generated videos/gifs land here
```

**Design boundary that matters:** `vision.py` only ever receives an *image*. It
has no access to the drone's true position — everything it reports is inferred
from pixels, exactly as it would be on a Raspberry Pi looking at a real camera.
The camera renderer (`camera_sim.py`) and the detector (`vision.py`) share the
*same* pinhole camera model from `config.py`, so the height the vision recovers
from the marker's apparent size is geometrically honest.

---

## 8. Where this goes next (Phase 2 — not built yet)

Because the drone command interface in `drone.py` mimics **MAVSDK/MAVLink**, the
higher-level brains of this project — `vision.py`, `control.py` and
`mission.py` — are written to be reusable on real hardware:

1. **Software-in-the-loop first.** Swap the simulated `drone.py` backend for a
   real MAVLink connection to **ArduPilot or PX4 SITL** (their official drone
   simulators). The mission logic and vision stay the same; only the backend
   that receives `arm()` / `takeoff()` / `set_velocity_body()` changes.
2. **Then real hardware.** Run `vision.py` on a **Raspberry Pi companion
   computer** with a real downward camera and a **ToF rangefinder**, talking over
   MAVLink to a flight controller (Pixhawk / STM32-class) that stabilises the
   motors. The Pi runs the OpenCV vision and decision logic; the flight
   controller just executes movement commands — the same split this simulation
   already models.

Keep the camera intrinsics in `config.py` matched to your real camera (do a
one-time calibration), print the ArUco marker at the configured `marker_size_m`,
and the same pipeline transfers across.

Happy (simulated) flying. 🍫🚁

---

# 3D World Upgrade — collision, LiDAR, a Blender world, and the onboard/ground split

The simulator now flies inside a real **3D world** (your Blender model, or a
built-in sample world), the drone can **crash into things**, it has a
**front camera + LiDAR** to see obstacles, and the work is split across a
simulated **onboard computer (the drone) and ground station (your laptop)**
talking over a radio **link** with latency, limited bandwidth and packet loss.

Everything above still works exactly the same — this is added on top. Across
several seeds the snack still drops a **mean ~7 cm** from the marker (worst ~10
cm), with the 3D collision world active — no loss of accuracy.

## A. One extra install (the 3D engine)

The 3D engine is **PyBullet**. First just try it inside your activated
environment:

```
pip install pybullet
```

- If that works, you're done — re-run `pip install -r requirements.txt`.
- If it FAILS (newest Python versions sometimes have no PyBullet wheel yet), make
  a **Python 3.12** environment instead. Install Python 3.12 from
  python.org/downloads, then, in the project folder:

```
python3.12 -m venv .venv312
source .venv312/bin/activate
pip install -r requirements.txt
```

Good news: **if PyBullet refuses to install, the simulator still runs.** It
automatically falls back to a built-in pure-Python 3D engine (collision, LiDAR
and camera feeds all still work — the camera pictures just look simpler). So you
are never blocked.

## B. New ways to run it

```
python main.py                     # the full mission, now inside the 3D world
python main.py --feeds             # LIVE multi-feed window (3rd-person + cameras), real time
python main.py --speed 0.5         # slow the live window to half speed (watch every step)
python main.py --multifeed         # save the combined multi-feed video (see below)
python main.py --split             # run the drone + ground station as TWO processes
python main.py --single-process    # the same split, in one process (faster)
python setup_positions.py          # place the start / drop points by hand (see D)
python main.py --world sample      # use the built-in sample world (default)
python main.py --world blender     # use YOUR exported Blender world
python world/import_model.py m.obj # use ANY .obj model as the world (no Blender — see I)
```

New since the last version (the four things added on top):

* **Obstacle-avoiding navigation** — the drone now plans a route AROUND (or over)
  buildings, trees and walls instead of flying a straight line into them, so you
  can put the start anywhere. See **section J**.
* **A real LIVE feed** — `--feeds` opens a window that updates *while the mission
  flies*, paced to **real time** (1 simulated second = 1 wall-clock second) so you
  can actually watch each phase. `--speed` changes the playback rate. See **K**.
* **More on the dashboard** — current **ground speed**, climb/descent rate,
  distance-to-goal, obstacle-avoidance status, and the planned route are now shown.
* **Bring your own 3D model** without Blender — `python world/import_model.py`. See **I**.

The **multi-feed video** (`outputs/multifeed_demo.mp4`) shows four things at once:
a 3rd-person view of the drone in the world with the **LiDAR hits painted red on
the model**, the **front camera**, the **down camera with the ArUco detection**,
and a **LiDAR radar** + telemetry (including what's running onboard vs on the
ground and the link status).

The **compute split** prints what runs where, the link latency / bandwidth /
dropped packets, and whether the onboard computer's per-tick budget was exceeded.

## C. Building your own world in Blender

1. In Blender: **Scene Properties → Units → Unit System = Metric, Unit Scale =
   1.000** (so 1 Blender unit = 1 metre).
2. Model your building / balcony / obstacles to scale.
3. **Add → Empty → Plain Axes**, rename it exactly **`DRONE_START`**, and place it
   where the drone launches. Add another named exactly **`DROP_TARGET`** where the
   snack should land.
4. (Optional, for looks) add flat image planes for the two ArUco markers.
5. **Scripting tab → Open →** choose `world/export_from_blender.py` **→ Run
   Script (▶)**. It writes `world/world_blender.obj` and `world/scene.json`.
6. Set `use_sample_world = False` in `config.py` (or run with `--world blender`),
   then `python main.py`.

The two Empties are the *authoritative* positions the simulator reads — that's far
more reliable than detecting a marker in a render. Naming rule: every mesh object
counts as a solid obstacle (a crash if touched) EXCEPT objects whose name starts
with `MARKER` or `GROUND`.

## D. Manual setup mode (see and move the start / drop points)

If detection isn't enough or you just want to place things by hand:

```
python setup_positions.py
```

It shows the world as a **wireframe** (so the points are visible even inside a
building), draws **DRONE_START as a green glowing star** and **DROP_TARGET as a
pink one** on top, lets you **orbit** to look around, type new coordinates, and
**save** them back to `world/scene.json`. If no window opens on your Mac it falls
back to saving orbit images (`outputs/setup_view.png`) — add `--no-gui` to force
that. Use `--demo` to just render the images and exit.

## E. What "flight failed" means now

Any contact between the drone and a solid object (building, balcony, railing,
tree…) **after takeoff and before the final home landing** ends the flight as
**FAILED** (you'll see the object it hit, and the time/place). Touching the ground
at home for launch and landing is allowed. The onboard **LiDAR reflex** tries to
prevent this by halting the drone if something is too close ahead.

## F. New settings in `config.py`

All under the "3D WORLD UPGRADE KNOBS" heading: which world to load
(`use_sample_world`, `world_backend`), the drone collision size
(`drone_radius_m`, `collision_margin_m`), the LiDAR (`lidar_range_m`, ray counts,
`lidar_reflex_stop_m`), the front/3rd-person cameras, and the link + compute split
(`link_latency_ms`, `link_bandwidth_kbps`, `link_packet_loss`,
`onboard_budget_ms_per_tick`).

Also: **navigation** (`enable_path_planning`, `nav_clearance_m`, `nav_max_climb_m`,
`waypoint_tol_m`, and the reactive `avoid_range_m` / `avoid_gain`) and the **live
view** (`live_speed`, `live_update_hz`, `live_feeds`).

## G. New tests

```
python tests/test_world.py      # scale (1 m cube), collision, reflex, LiDAR ranges
python tests/test_compute.py    # link latency / bandwidth / loss, budget, the split
python tests/test_planner.py    # the route planner: clear vs around vs over obstacles
python tests/test_navigation.py # full missions from starts behind the tree/building
```

(The original `test_vision.py`, `test_mission.py`, `test_smoke.py` still pass with
the 3D world active.)

## H. Troubleshooting the new parts

**`pip install pybullet` fails.** Use a Python 3.12 venv (section A) — or just run
without it; the built-in numpy fallback engine takes over automatically. You can
force a backend with `world_backend = "pybullet"` or `"numpy"` in `config.py`.

**A `cv2.imshow` / feed window doesn't open.** The multi-feed is exported as a
video file regardless, so open `outputs/multifeed_demo.mp4`. Live OpenCV windows
need a desktop session; the headless path always works.

**The drone "crashes" immediately on my Blender world.** Check your `DRONE_START`
Empty isn't inside a wall, and that the cruise altitude in `config.py`
(`cruise_altitude_m`) is above your balcony/roof so it approaches from above.

**Two-process split seems stuck.** Some setups dislike `multiprocessing`; the code
falls back to single-process automatically. You can also just use
`--single-process`.

---

## I. Bring your own 3D model (no Blender needed)

You don't have to use Blender. If you have a model as a Wavefront **`.obj`** file
(almost every 3D tool can "Export to OBJ"), point the importer at it:

```
python world/import_model.py /path/to/my_model.obj
```

That copies your model into `world/`, works out which parts are solid obstacles
(everything EXCEPT objects whose name starts with `GROUND` or `MARKER`, same rule
as the Blender exporter), and writes `world/scene.json` so it becomes the world.
Then place the start / landing spots and fly — exactly the workflow you already use:

```
python setup_positions.py     # drag to orbit, type the start / landing coordinates, save
python main.py                # fly your model (with obstacle-avoiding navigation)
python main.py --feeds        # ...with the live multi-feed window
```

Notes:
* The simulator works in **metres** (1 OBJ unit = 1 m). If your model imports
  sideways it is probably **Y-up** — re-run with `--y-up`. Rescale with `--scale`.
* Export your model with **named objects** (the `o`/`g` lines) so each obstacle can
  be identified — that's how a crash can tell you *what* it hit.
* Switch back to the built-in demo world any time: `python main.py --world sample`.

## J. Obstacle-avoiding navigation (the drone now routes around things)

Previously the drone flew a dead-straight line from the start to the balcony, and
the only obstacle handling was an onboard reflex that could merely **stop**. So if
you moved the start so a tree or a wall sat in between, it would bump into it or
stall. Now there are **two layers** working together (the same split a real drone
uses — the laptop plans, the drone reacts):

1. **A global route planner** (`src/planner.py`, a ground-station task). It builds a
   2-D obstacle map of your world *at the flight altitude* and runs an A\* search to
   find a clear path, then smooths it into waypoints. If it can't go **around**
   something, it climbs and flies **over** it (it prefers the lowest altitude that
   works). The planned route is drawn on the dashboard map (dashed green).
2. **An onboard reactive layer.** Because the cruise flies on imperfect GPS in wind,
   the *actual* path drifts a little off the plan; a 360-degree probe gently
   **steers the drone away** from anything it drifts toward (and slides around it)
   instead of just halting.

Try it: open `world/scene.json` (or run `python setup_positions.py`) and move
`drone_start` behind the building or the tree, then `python main.py`. The summary
prints whether it flew a *clear straight path* or *avoided obstacles*. Tuning knobs
are in `config.py` under "Navigation / obstacle-avoiding path planner" and the
reactive-avoidance lines (`nav_clearance_m`, `nav_max_climb_m`, `avoid_range_m`,
`avoid_gain`). Set `enable_path_planning = False` to go back to straight-line flight.

> A note on clearance: the cruise is GPS-guided, so it keeps a real safety buffer
> (`nav_clearance_m`) from obstacles — just like a real drone that can't trust GPS
> to the centimetre. Lower it for tight indoor worlds; raise it to be more cautious.

## K. A real, time-accurate live feed

The on-screen window now updates **while the mission flies** and is paced to **real
time** — 1 simulated second takes 1 wall-clock second — so the fast phases
(`SEARCH`, `PRECISION_ALIGN`, `DESCEND`, `DROP`) are actually watchable instead of
flashing by. Two views:

```
python main.py             # the 4-panel dashboard, live + real time (map, side, down-cam, telemetry)
python main.py --feeds     # the rich multi-feed window: 3rd-person + LiDAR + front cam + down cam + radar
```

Control the pace (applies to either):

```
python main.py --speed 0.5    # half speed (slow-motion — great for the drop)
python main.py --speed 2      # double speed
python main.py --feeds --speed 0.5
```

The video files (`outputs/mission_demo.mp4`, `outputs/multifeed_demo.mp4`) are still
saved as before, so you can re-watch and share. (Defaults for the live view live in
`config.py` under "Live view": `live_speed`, `live_update_hz`, `live_feeds`.)

The **telemetry** panel now also shows the **current ground speed**, the
climb/descent rate, distance to the goal, and whether obstacle avoidance is actively
steering.

---

## Where this 3D version goes next (still Phase 2)

The split is already modelled the way the real system works: the **onboard** half
(flight control, state estimation, the down-camera ArUco + precision PID, and the
LiDAR reflex) is exactly what a Raspberry Pi + flight controller run locally; the
**ground** half (dispatch, planning, heavy mapping, logging, video) is your
laptop. To go to hardware you replace the simulated `drone.py` backend with a real
MAVLink/MAVSDK link (first to PX4/ArduPilot SITL, then a real Pixhawk + Pi + ToF),
keep `vision.py`, `control.py`, `mission.py`, `world.py`'s LiDAR/collision
interfaces, and feed real camera + LiDAR frames in place of the simulated ones.
