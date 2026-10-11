"""Regression guards for the latency-sensitive Moment Arc broadcast entrypoint."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "src/org/uwuaosp/systemui/moment/arc/MomentArcController.kt"
PLUGIN = ROOT / "src/org/uwuaosp/systemui/moment/arc/MomentArcPlugin.kt"

class MomentArcAsyncQATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = CONTROLLER.read_text(encoding="utf-8")
        cls.plugin = PLUGIN.read_text(encoding="utf-8")

    def test_icon_service_binder_calls_are_in_bounded_executor(self):
        src = self.src
        self.assertIn("private val iconExecutor = ThreadPoolExecutor(", src)
        self.assertIn("ArrayBlockingQueue<Runnable>(MAX_ICON_TASKS)", src)
        self.assertIn("0, 1, 15L, TimeUnit.SECONDS", src)
        icon_fn = src.split("private fun createIconView(",1)[1].split("private fun loadIcon(",1)[0]
        self.assertIn("iconExecutor.execute {", icon_fn)
        self.assertIn("loadIcon(target)", icon_fn.split("iconExecutor.execute {",1)[1])
        self.assertNotIn("loadIcon(target)", icon_fn.split("iconExecutor.execute {",1)[0])

    def test_dismissed_overlay_cannot_receive_late_icon(self):
        src = self.src
        self.assertIn("overlayGeneration.incrementAndGet()", src)
        self.assertIn("overlayGeneration.get() == generation && overlayView != null", src)
        self.assertIn("mainHandler.post {", src)

    def test_pending_touch_queue_is_bounded(self):
        self.assertIn("touchCoordinatesQueue.size >= MAX_PENDING_TOUCHES",self.src)
        self.assertIn("private const val MAX_PENDING_TOUCHES = 32",self.src)

    def test_touch_events_use_cached_setting_without_binder_reads(self):
        touch = self.src.split("fun onTouchCoordinates(", 1)[1].split(
            "    fun hide()", 1
        )[0]
        self.assertIn("if (!isMomentArcEnabled())", touch)
        self.assertNotIn("Settings.Secure.getIntForUser", touch)
        self.assertIn("fun isMomentArcEnabled(): Boolean = momentArcEnabled", self.src)
        self.assertIn("fun refreshEnabledState()", self.src)
        self.assertIn("controller.refreshEnabledState()", self.plugin)
        self.assertIn("Intent.ACTION_USER_SWITCHED -> {", self.plugin)

    def test_plugin_shutdown_releases_worker(self):
        self.assertIn("fun destroy() {", self.src)
        self.assertIn("iconExecutor.shutdownNow()", self.src)
        self.assertIn("controller.destroy()", self.plugin)
        self.assertIn("if (destroyed) return", self.src)
        self.assertIn('Log.e(TAG, "MomentArc gesture command failed", e)', self.plugin)
        self.assertIn('Log.e(TAG, "MomentArc registration failed", e)', self.plugin)

if __name__ == "__main__":
    unittest.main()
