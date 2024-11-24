package drunkcats

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material.Button
import androidx.compose.material.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.graphics.drawscope.drawIntoCanvas
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.window.singleWindowApplication
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import org.jetbrains.skia.Color
import org.jetbrains.skia.Paint
import kotlin.random.Random
import kotlin.random.nextInt


fun main() {
    val random = Random(System.currentTimeMillis())

    singleWindowApplication {
        var catsInfo: List<CatInfo> by remember { mutableStateOf(emptyList()) }

        val cs = rememberCoroutineScope { Dispatchers.Default }

        LaunchedEffect(Unit) {
            cs.launch {
                while (true) {
                    catsInfo = List(50_000) {
                        CatInfo(
                            x = random.nextFloat(),
                            y = random.nextFloat(),
                            state = CatState.entries[random.nextInt(0..2)]
                        )
                    }
                    delay(40)
                }
            }
        }

        Box(Modifier.fillMaxSize(), Alignment.Center) {
            Cats(catsInfo)

            Button({}) {
                Text("ok")
            }
        }
    }
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

@Composable
fun Cats(cats: List<CatInfo>) {
    Box(
        Modifier.fillMaxSize().drawBehind {
            drawIntoCanvas { canvas ->
                for (cat in cats) {
                    canvas.nativeCanvas.drawCircle(
                        size.width * cat.x, size.height * cat.y,
                        radius = 8f,
                        paint = Paint().apply {
                            this.color = when (cat.state) {
                                CatState.Calm -> Color.GREEN
                                CatState.Angry -> Color.YELLOW
                                CatState.Fighting -> Color.RED
                            }
                        },
                    )
                }
            }
        }
    )
}
