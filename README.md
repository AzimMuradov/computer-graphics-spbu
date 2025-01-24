# drunk-cats

<img src=https://github.com/user-attachments/assets/a1649bd3-85f6-479a-86d0-83d4a1cd2cea alt="logo" width="100" align="right" style="margin-left: 16px; margin-bottom: 16px">

**drunk-cats** is an application for simulating the interactions between objects in a limited area.
The objects have specific behavior patterns (see [interactions](#interactions)).
The app is also have a quite flexible configuration of simulation parameters (see [run options](#run-options)).

Cats were chosen just as the model objects :smile_cat:

## Interactions

Expressed by the following rules:

1. If two cats are at a distance not exceeding r, they try to start a fight with a probability of 1.

2. If two cats are at a distance R > r, they start hissing with a probability inversely proportional to the square of
   the distance between them.

3. If there are no rivals around the cat, it calmly walks.

At the same time, cats move within a limited area.

## Features

1. Supports over 500_000 cats for rendering

![many_cats_demo](https://github.com/user-attachments/assets/3248153a-149c-4a5a-933b-c1b3c414fe72)

*20_000 chosen for comfortable demo*

2. You can zoom and drag the screen for better viewing experience

![zoom_and_drug_demo](https://github.com/user-attachments/assets/4333d5c0-2ce7-4a2a-a249-625ded57682c)

3. You can scare cats so that they run away from the cursor

![cursor push demo](https://github.com/user-attachments/assets/9c9c39b5-10de-4d48-b6bf-40ca74b83472)


4. You can set a custom image for the cats or use predefined with Tom

![texture feature demo](https://github.com/user-attachments/assets/98ae71fd-b501-4853-a240-45573482dd75)


5. You can turn on logs of cat interactions

![logging_demo](https://github.com/user-attachments/assets/7a690f41-5188-4f62-9e35-d3dbad194059)

6. "Follow" mode for a specific cat

**Double-click** on the cat you want to follow (labeled with :star:), and **press 'F'** to release him

![follow_mode](https://github.com/user-attachments/assets/862c2ace-6f3d-46cc-a13d-86ef3864a352)

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

## Run Options

The application provides extensive options for configuring the simulation through command-line arguments.

These settings allow users to easily adapt the simulation to their needs by changing visual parameters, the number of
cats, and their interaction rules.

| Option              | Description                                                                   |         Default         |
|---------------------|-------------------------------------------------------------------------------|:-----------------------:|
| --radius FLOAT      | set the radius of the points (cats)                                           |            5            |
| --image-path PATH   | set a path to an image that will be used as a texture for points (cats)       | no texture (use colors) |
| --num-points INT    | set the number of points (cats) in the simulation                             |       500 points        |
| --fight-radius INT  | set the radius of the fight zone for cats, must be smaller than hiss-radius   |           15            |
| --hiss-radius INT   | set the radius of the hissing zone for cats, must be larger than fight-radius |           30            |
| --window-width INT  | set the width of the application window                                       |       1000 pixels       |
| --window-height INT | set the height of the application window                                      |       800 pixels        |
| --debug, --no-debug | enable debug messages                                                         |        disabled         |

## License

Distributed under the MIT License.
See [LICENSE](https://github.com/AzimMuradov/drunk-cats/blob/master/LICENSE) for more information.
