package drunkcats

import javafx.application.Application
import javafx.scene.Scene
import javafx.scene.canvas.Canvas
import javafx.scene.canvas.GraphicsContext
import javafx.scene.control.Button
import javafx.scene.layout.StackPane
import javafx.scene.paint.Color
import javafx.stage.Stage
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.javafx.JavaFx
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.time.Duration
import kotlin.random.Random
import kotlin.random.nextInt


fun main(args: Array<String>) {
    Application.launch(App::class.java, *args)
}

data class CatInfo(
    val x: Float,
    val y: Float,
    val state: CatState,
)

enum class CatState {
    Calm,
    Angry,
    Fighting,
}

fun catsFlow(): Flow<List<CatInfo>> = flow {
    val random = Random(System.currentTimeMillis())

    while (true) {
        val cats = withContext(Dispatchers.Default) {
            List(500_000) {
                CatInfo(
                    x = random.nextFloat(),
                    y = random.nextFloat(),
                    state = CatState.entries[random.nextInt(0..2)]
                )
            }
        }
        emit(cats)
        delay(500)
    }
}


class App : Application() {

    private lateinit var job: Job

    override fun start(stage: Stage) {
        val canvas = Canvas().apply {
            this.width = 640.0
            this.height = 480.0
        }

        val button = Button("ok")
        button.isDisable = false

        val root = StackPane(canvas, button)
        val scene = Scene(root, 640.0, 480.0)

        stage.scene = scene
        stage.show()


        job = Job()
        val context = Dispatchers.JavaFx + job
        val scope = CoroutineScope(context)

        scope.launch {
            var lastTime = System.nanoTime()

            catsFlow().collect { cats ->
                canvas.graphicsContext2D.drawCats(cats)

                val currTime = System.nanoTime()
                val elapsedTime = Duration.ofNanos(currTime - lastTime)
                lastTime = currTime

                println(elapsedTime.toMillisPart())
            }
        }

        stage.setOnCloseRequest {
            job.cancel()
        }
    }
}


private fun GraphicsContext.drawCats(cats: List<CatInfo>) {
    val r = 8.0

    clearRect(0.0, 0.0, canvas.width, canvas.height)
    for (cat in cats) {
        fill = when (cat.state) {
            CatState.Calm -> Color.GREEN
            CatState.Angry -> Color.ORANGE
            CatState.Fighting -> Color.RED
        }

        fillOval(
            canvas.width * cat.x,
            canvas.height * cat.y,
            r * 2,
            r * 2,
        )
    }
}
