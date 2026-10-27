
// Offline compatibility proof using actual Configurate and generated config interfaces.
tasks.register<JavaExec>("mcgatewayConfigCompatibility") {
    dependsOn(tasks.testClasses)
    classpath = sourceSets["test"].runtimeClasspath
    mainClass.set("com.rtm516.mcxboxbroadcast.core.configs.ConfigCompatibilityProof")
    maxHeapSize = "256m"
}
