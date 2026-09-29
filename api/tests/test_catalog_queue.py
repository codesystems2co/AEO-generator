"""Visible catalog queue never lists more than six products."""
import unittest

from app.services.catalog_offer import (
    advance_queue,
    block_caption,
    queue_snapshot,
    queue_window,
)


class QueueWindowTest(unittest.TestCase):
    def test_window_shows_six_and_only_one_analyzing(self):
        pending = [{"id": i, "name": f"P{i}"} for i in range(1, 12)]
        window = queue_window(pending, active_id=3)
        self.assertEqual(len(window), 6)
        self.assertEqual(sum(1 for row in window if row["state"] == "analyzing"), 1)
        self.assertEqual(window[2]["state"], "analyzing")

    def test_analyzed_item_drops_when_the_next_enters(self):
        pending = [{"id": i, "name": f"P{i}"} for i in range(1, 10)]
        after = advance_queue(pending, analyzed_id=1)
        snap = queue_snapshot(after, active_id=2, phase="analyzing", block_index=1, total=9)
        self.assertEqual(len(snap["window"]), 6)
        self.assertEqual([row["id"] for row in snap["window"]], [2, 3, 4, 5, 6, 7])
        self.assertEqual(snap["window"][0]["state"], "analyzing")
        self.assertEqual(sum(1 for row in snap["window"] if row["state"] == "analyzing"), 1)
        self.assertNotIn(1, [row["id"] for row in snap["window"]])

    def test_block_caption_names_the_current_range(self):
        self.assertEqual(block_caption(2, 20, 45), "bloque 2, productos 21–40")
        snap = queue_snapshot(
            [{"id": 21, "name": "P21"}],
            active_id=21,
            phase="analyzed",
            block_index=2,
            total=45,
        )
        self.assertEqual(snap["caption"], "bloque 2, productos 21–40")
        self.assertEqual(snap["window"][0]["state"], "analyzed")


if __name__ == "__main__":
    unittest.main()
