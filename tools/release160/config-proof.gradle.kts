
// Standalone proof source set: upstream tests keep their normal discovery rules.
val mcgatewayProof by sourceSets.creating {
    compileClasspath += sourceSets.main.get().output + configurations.runtimeClasspath.get()
    runtimeClasspath += output + compileClasspath
}
tasks.register<JavaExec>("mcgatewayConfigCompatibility") {
    dependsOn(mcgatewayProof.classesTaskName)
    classpath = mcgatewayProof.runtimeClasspath
    mainClass.set("com.rtm516.mcxboxbroadcast.core.configs.ConfigCompatibilityProof")
    maxHeapSize = "256m"
}
