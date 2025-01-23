# drunk-cats
<img src=https://github.com/user-attachments/assets/a1649bd3-85f6-479a-86d0-83d4a1cd2cea alt="logo" width="100" align="right">

drunk-cats is an application for simulating the interaction of objects with specific behavior patterns in a limited area, providing several additional features and flexible configuration of simulation parameters. Cats were chosen as the model objects :)

## Interaction
Expressed by the following rules:
1. If two cats are at a distance not exceeding r_0, they try to start a fight with a probability of 1.

2. If two cats are at a distance R_0>r_0, they start hissing with a probability inversely proportional to the square of the distance between them.

3. If there are no rivals around the cat, it calmly walks.

At the same time, cats move within a limited area.

## Features
1. Supports over 500,000 cats for rendering
![demo](https://github.com/user-attachments/assets/3248153a-149c-4a5a-933b-c1b3c414fe72)

*20,000 chosen for comfortable demo*

3. Zoom and drag the screen for better viewing experience

![zoom_and_drug](https://github.com/user-attachments/assets/4333d5c0-2ce7-4a2a-a249-625ded57682c)

3. Cats can leave the map

4. Ability to set custom images instead of points

5. Logging of cat interactions
   
![logging](https://github.com/user-attachments/assets/7a690f41-5188-4f62-9e35-d3dbad194059)

6. "Follow" mode for a specific cat

![followe_mode](https://github.com/user-attachments/assets/862c2ace-6f3d-46cc-a13d-86ef3864a352)


## User Settings
The application provides extensive options for configuring the simulation through command-line arguments:

1. --radius: Sets the radius of displayed points (cats). Default: 5 pixels
2. --image-path: Allows setting a path to an image that will be used as a texture for points. By default, no texture is used.
3. --num-points: Determines the number of points (cats) in the simulation. Default: 500.
4. --fight-radius: Sets the radius of the fight zone for cats. Must be smaller than hiss-radius. Default is 15.
5. --hiss-radius: Sets the radius of the hissing zone for cats. Must be larger than fight-radius. Default is 30.
6. --window-width: Sets the width of the application window. Default is 1000 pixels.
7. --window-height: Sets the height of the application window. Default is 800 pixels.
8. --debug: Enables debug mode for additional message output. Disabled by default (False).
These settings allow users to easily adapt the simulation to their needs by changing visual parameters, the number of cats, and their interaction rules.

## Setup

```bash
make build # or just "make"
```

## Run

### Using `make`

```bash
make run
```

### Using `python` directly

#### Linux, MacOS

```bash
./.venv/bin/python main.py [OPTIONS]
```

#### Windows

```bash
./.venv/Scripts/python main.py [OPTIONS]
```

## License

Distributed under the MIT License.
See [LICENSE](https://github.com/AzimMuradov/drunk-cats/blob/master/LICENSE) for more information.
