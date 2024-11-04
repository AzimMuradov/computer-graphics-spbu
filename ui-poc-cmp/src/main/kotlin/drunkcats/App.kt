package drunkcats

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material.Button
import androidx.compose.material.Text
import androidx.compose.runtime.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.window.singleWindowApplication
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
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
                    catsInfo = List(50000) {
                        CatInfo(
                            x = random.nextFloat(),
                            y = random.nextFloat(),
                            state = CatState.entries[random.nextInt(0..2)]
                        )
                    }
                    delay(random.nextLong(500))
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
    Canvas(Modifier.fillMaxSize()) {
        for (cat in cats) {
            drawCircle(
                color = when (cat.state) {
                    CatState.Calm -> Color.Green
                    CatState.Angry -> Color.Yellow
                    CatState.Fighting -> Color.Red
                },
                radius = 8f,
                center = Offset(size.width * cat.x, size.height * cat.y)
            )
        }
    }
}
