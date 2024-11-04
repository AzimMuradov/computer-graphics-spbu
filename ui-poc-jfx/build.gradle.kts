plugins {
    alias(libs.plugins.kotlin.jvm)
    alias(libs.plugins.javafx)
    application
}

repositories {
    mavenCentral()
}

dependencies {
    implementation(libs.kotlinx.coroutines.core)
    implementation(libs.kotlinx.coroutines.javafx)
}

javafx {
    version = libs.versions.javafx.asProvider().get()
    modules = listOf("javafx.controls")
}

application {
    mainClass.set("drunkcats.AppKt")
}
