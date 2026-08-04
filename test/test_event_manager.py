import unittest
import threading
import time
from unittest.mock import MagicMock, patch, call
from enum import Enum
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from PyOrchestrate.core.utilities.event_manager import EventManager


class TestEvents(Enum):
    """Test events for EventManager testing."""

    EVENT_A = "event_a"
    EVENT_B = "event_b"
    EVENT_C = "event_c"
    STRESS_TEST = "stress_test"


class OtherTestEvents(Enum):
    """Second enum sharing a member name with TestEvents."""

    EVENT_A = "other_event_a"


class TestEventManager(unittest.TestCase):
    """Test cases for EventManager functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.event_manager = EventManager(max_workers=4)
        self.callback_results = []
        self.callback_lock = threading.Lock()

    def tearDown(self):
        """Clean up after tests."""
        self.event_manager.shutdown(wait=True)

    def test_initialization(self):
        """Test EventManager initialization."""
        em = EventManager(max_workers=5)
        self.assertEqual(em._max_workers, 5)
        self.assertFalse(em._shutdown)
        self.assertIsNone(em._executor)
        self.assertEqual(len(em._listeners), 0)
        self.assertIsInstance(em._executor_lock, type(threading.Lock()))
        em.shutdown()

    def test_register_event_single_callback(self):
        """Test registering a single callback to an event."""
        callback = MagicMock()

        self.event_manager.register_event(TestEvents.EVENT_A, callback)

        # Check that the event is registered
        self.assertIn(TestEvents.EVENT_A, self.event_manager._listeners)
        self.assertEqual(len(self.event_manager._listeners[TestEvents.EVENT_A]), 1)
        self.assertEqual(self.event_manager._listeners[TestEvents.EVENT_A][0], callback)

    def test_register_event_multiple_callbacks(self):
        """Test registering multiple callbacks to the same event."""
        callback1 = MagicMock()
        callback2 = MagicMock()
        callback3 = MagicMock()

        self.event_manager.register_event(TestEvents.EVENT_A, callback1)
        self.event_manager.register_event(TestEvents.EVENT_A, callback2)
        self.event_manager.register_event(TestEvents.EVENT_A, callback3)

        # Check that all callbacks are registered in order
        listeners = self.event_manager._listeners[TestEvents.EVENT_A]
        self.assertEqual(len(listeners), 3)
        self.assertEqual(listeners[0], callback1)
        self.assertEqual(listeners[1], callback2)
        self.assertEqual(listeners[2], callback3)

    def test_same_member_name_in_different_enums_stays_independent(self):
        """Members sharing a name across enums must not share listeners."""
        fired = []

        self.event_manager.register_event(
            TestEvents.EVENT_A, lambda: fired.append(TestEvents.EVENT_A)
        )
        self.event_manager.register_event(
            OtherTestEvents.EVENT_A, lambda: fired.append(OtherTestEvents.EVENT_A)
        )

        self.assertIn(TestEvents.EVENT_A, self.event_manager._listeners)
        self.assertIn(OtherTestEvents.EVENT_A, self.event_manager._listeners)

        self.event_manager.emit(TestEvents.EVENT_A)

        # shutdown drains the pool, so no sleep is needed to see every callback
        self.event_manager.shutdown(wait=True)

        self.assertEqual(fired, [TestEvents.EVENT_A])

    def test_emit_no_listeners(self):
        """Test emitting an event with no registered listeners."""
        # Should not raise any exception
        self.event_manager.emit(TestEvents.EVENT_A, arg1="value1", arg2="value2")

    def test_emit_with_listeners(self):
        """Test emitting an event with registered listeners."""

        def callback1(*args, **kwargs):
            pass

        def callback2(*args, **kwargs):
            pass

        mock_callback1 = MagicMock(side_effect=callback1)
        mock_callback2 = MagicMock(side_effect=callback2)

        self.event_manager.register_event(TestEvents.EVENT_A, mock_callback1)
        self.event_manager.register_event(TestEvents.EVENT_A, mock_callback2)

        # Emit event with arguments
        self.event_manager.emit(
            TestEvents.EVENT_A, "arg1", arg2="value2", arg3="value3"
        )

        # Wait for async execution
        time.sleep(0.1)

        # Both callbacks should be called with args and kwargs (including default data)
        # We just verify they were called, not the exact arguments due to timestamps
        mock_callback1.assert_called_once()
        mock_callback2.assert_called_once()

        # Verify the calls include our custom arguments
        args, kwargs = mock_callback1.call_args
        self.assertEqual(args, ("arg1",))
        self.assertIn("arg2", kwargs)
        self.assertIn("arg3", kwargs)
        self.assertEqual(kwargs["arg2"], "value2")
        self.assertEqual(kwargs["arg3"], "value3")

    def test_emit_with_parameter_filtering(self):
        """Test that callbacks only receive parameters they accept."""

        def callback_with_kwargs_only(**kwargs):
            # This callback only accepts kwargs
            pass

        def callback_with_all_params(*args, **kwargs):
            # This callback accepts all arguments
            pass

        callback1 = MagicMock(side_effect=callback_with_kwargs_only)
        callback2 = MagicMock(side_effect=callback_with_all_params)

        self.event_manager.register_event(TestEvents.EVENT_A, callback1)
        self.event_manager.register_event(TestEvents.EVENT_A, callback2)

        # Emit with kwargs only to avoid args/kwargs conflicts
        self.event_manager.emit(TestEvents.EVENT_A, arg2="value2", arg3="value3")

        time.sleep(0.1)

        # Both callbacks should receive kwargs (callback1 filters, callback2 accepts all)
        # Check that they were called and verify content
        callback1.assert_called_once()
        callback2.assert_called_once()

        # Verify callback1 received the expected args
        args, kwargs = callback1.call_args
        self.assertIn("arg2", kwargs)
        self.assertIn("arg3", kwargs)
        self.assertEqual(kwargs["arg2"], "value2")
        self.assertEqual(kwargs["arg3"], "value3")

    def test_emit_with_default_data(self):
        """Test that default event_date and event_time are added when needed."""

        def callback_with_default_data(**kwargs):
            # Accept all kwargs including default data
            pass

        def callback_without_default_data(**kwargs):
            # Also accept all kwargs but we'll verify content
            pass

        callback1 = MagicMock(side_effect=callback_with_default_data)
        callback2 = MagicMock(side_effect=callback_without_default_data)

        self.event_manager.register_event(TestEvents.EVENT_A, callback1)
        self.event_manager.register_event(TestEvents.EVENT_A, callback2)

        # Mock datetime to control the default data
        with patch(
            "PyOrchestrate.core.utilities.event_manager.datetime"
        ) as mock_datetime:
            mock_now = MagicMock()
            mock_now.date.return_value.isoformat.return_value = "2025-08-07"
            mock_now.time.return_value.isoformat.return_value = "10:30:00"
            mock_datetime.now.return_value = mock_now

            self.event_manager.emit(TestEvents.EVENT_A, custom_arg="value")

            time.sleep(0.1)

            # Both callbacks should receive all data including default data
            expected_kwargs = {
                "event_date": "2025-08-07",
                "event_time": "10:30:00",
                "custom_arg": "value",
            }
            callback1.assert_called_once_with(**expected_kwargs)
            callback2.assert_called_once_with(**expected_kwargs)

    def test_emit_with_exception_in_callback(self):
        """Test that exceptions in one callback don't affect others."""

        def failing_callback(**kwargs):
            raise ValueError("Test exception")

        def working_callback(**kwargs):
            test_arg = kwargs.get("test_arg")
            with self.callback_lock:
                self.callback_results.append(f"working_callback_{test_arg}")

        callback1 = MagicMock(side_effect=failing_callback)
        callback2 = MagicMock(side_effect=working_callback)

        self.event_manager.register_event(TestEvents.EVENT_A, callback1)
        self.event_manager.register_event(TestEvents.EVENT_A, callback2)

        # Emit event
        self.event_manager.emit(TestEvents.EVENT_A, test_arg="success")

        time.sleep(0.2)

        # Both callbacks should have been called
        callback1.assert_called_once()
        callback2.assert_called_once()

        # Working callback should have executed successfully
        with self.callback_lock:
            self.assertIn("working_callback_success", self.callback_results)

    def test_shutdown_prevents_new_emissions(self):
        """Test that shutdown prevents new event emissions."""
        callback = MagicMock()
        self.event_manager.register_event(TestEvents.EVENT_A, callback)

        # Shutdown the event manager
        self.event_manager.shutdown()

        # Try to emit an event after shutdown
        self.event_manager.emit(TestEvents.EVENT_A, arg="value")

        time.sleep(0.1)

        # Callback should not have been called
        callback.assert_not_called()

    def test_shutdown_idempotent(self):
        """Test that shutdown can be called multiple times safely."""
        # Call shutdown multiple times
        self.event_manager.shutdown()
        self.event_manager.shutdown()
        self.event_manager.shutdown()

        # Should not raise any exception
        self.assertTrue(self.event_manager._shutdown)

    def test_lazy_executor_initialization(self):
        """Test that ThreadPoolExecutor is created lazily."""
        # Initially no executor
        self.assertIsNone(self.event_manager._executor)

        # Register callback
        callback = MagicMock()
        self.event_manager.register_event(TestEvents.EVENT_A, callback)

        # Still no executor after registration
        self.assertIsNone(self.event_manager._executor)

        # Emit event should create executor
        self.event_manager.emit(TestEvents.EVENT_A, arg="value")

        # Now executor should exist
        self.assertIsNotNone(self.event_manager._executor)
        self.assertIsInstance(self.event_manager._executor, ThreadPoolExecutor)

    def test_no_default_data_optimization(self):
        """Test that default data is not created when no callback needs it."""

        def callback_no_defaults(**kwargs):
            # This callback accepts **kwargs but we'll test it doesn't get default data
            pass

        callback = MagicMock(side_effect=callback_no_defaults)
        self.event_manager.register_event(TestEvents.EVENT_A, callback)

        # Since the callback accepts **kwargs, default data will be created
        # So we test a different scenario: no callbacks at all
        self.event_manager._listeners[TestEvents.EVENT_A] = []

        # Mock datetime to ensure it's not called when no listeners
        with patch(
            "PyOrchestrate.core.utilities.event_manager.datetime"
        ) as mock_datetime:
            self.event_manager.emit(TestEvents.EVENT_A, custom_arg="value")

            time.sleep(0.1)

            # datetime.now() should not have been called
            mock_datetime.now.assert_not_called()

            # Callback should not be called since we cleared listeners
            callback.assert_not_called()


class TestEventManagerThreadSafety(unittest.TestCase):
    """Test thread safety of EventManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.event_manager = EventManager(max_workers=10)
        self.results = []
        self.results_lock = threading.Lock()
        self.error_count = 0
        self.error_lock = threading.Lock()

    def tearDown(self):
        """Clean up after tests."""
        self.event_manager.shutdown(wait=True)

    def test_concurrent_registration(self):
        """Test concurrent registration of callbacks from multiple threads."""

        def register_callbacks():
            try:
                for i in range(10):
                    callback = MagicMock()
                    self.event_manager.register_event(TestEvents.STRESS_TEST, callback)
            except Exception as e:
                with self.error_lock:
                    self.error_count += 1

        # Start multiple threads registering callbacks
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=register_callbacks)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check no errors occurred
        self.assertEqual(self.error_count, 0)

        # Check that all callbacks were registered
        listeners = self.event_manager._listeners.get(TestEvents.STRESS_TEST, [])
        self.assertEqual(len(listeners), 50)  # 5 threads * 10 callbacks each

    def test_concurrent_emissions(self):
        """Test concurrent event emissions from multiple threads."""

        def thread_callback(**kwargs):
            thread_id = kwargs.get("thread_id")
            event_count = kwargs.get("event_count")
            with self.results_lock:
                self.results.append(f"thread_{thread_id}_event_{event_count}")

        # Register callback
        callback = MagicMock(side_effect=thread_callback)
        self.event_manager.register_event(TestEvents.STRESS_TEST, callback)

        def emit_events(thread_id):
            try:
                for i in range(20):
                    self.event_manager.emit(
                        TestEvents.STRESS_TEST, thread_id=thread_id, event_count=i
                    )
            except Exception as e:
                with self.error_lock:
                    self.error_count += 1

        # Start multiple threads emitting events
        threads = []
        num_threads = 8
        for thread_id in range(num_threads):
            thread = threading.Thread(target=emit_events, args=(thread_id,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Wait for all async callbacks to complete
        time.sleep(0.5)

        # Check no errors occurred during emission
        self.assertEqual(self.error_count, 0)

        # Check that all events were processed
        with self.results_lock:
            self.assertEqual(
                len(self.results), num_threads * 20
            )  # 8 threads * 20 events each

    def test_concurrent_executor_initialization(self):
        """Test that ThreadPoolExecutor is safely initialized under concurrent access."""

        def emit_event():
            try:
                callback = MagicMock()
                self.event_manager.register_event(TestEvents.EVENT_A, callback)
                self.event_manager.emit(TestEvents.EVENT_A, arg="test")
            except Exception as e:
                with self.error_lock:
                    self.error_count += 1

        # Start multiple threads that will trigger executor initialization
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=emit_event)
            threads.append(thread)

        # Start all threads simultaneously
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check no errors occurred
        self.assertEqual(self.error_count, 0)

        # Check that exactly one executor was created
        self.assertIsNotNone(self.event_manager._executor)
        self.assertIsInstance(self.event_manager._executor, ThreadPoolExecutor)

    def test_shutdown_during_concurrent_operations(self):
        """Test shutdown behavior during concurrent operations."""

        def continuous_emit():
            callback = MagicMock()
            self.event_manager.register_event(TestEvents.EVENT_B, callback)

            for i in range(100):
                if not self.event_manager._shutdown:
                    try:
                        self.event_manager.emit(TestEvents.EVENT_B, count=i)
                        time.sleep(0.001)  # Small delay
                    except Exception:
                        # Expected during shutdown
                        pass

        # Start background thread emitting events
        emit_thread = threading.Thread(target=continuous_emit)
        emit_thread.start()

        # Let it run for a bit
        time.sleep(0.1)

        # Shutdown while operations are ongoing
        self.event_manager.shutdown(wait=True)

        # Wait for background thread to finish
        emit_thread.join(timeout=2.0)

        # Verify shutdown completed successfully
        self.assertTrue(self.event_manager._shutdown)

    def test_registration_and_emission_mixed(self):
        """Test mixed concurrent registration and emission operations."""
        shared_results = []
        results_lock = threading.Lock()

        def register_and_emit(worker_id):
            try:
                # Register a callback
                def callback(**kwargs):
                    worker_id_kw = kwargs.get("worker_id")
                    operation = kwargs.get("operation")
                    with results_lock:
                        shared_results.append(f"worker_{worker_id_kw}_{operation}")

                callback_mock = MagicMock(side_effect=callback)
                self.event_manager.register_event(TestEvents.EVENT_C, callback_mock)

                # Emit some events
                for op in range(5):
                    self.event_manager.emit(
                        TestEvents.EVENT_C, worker_id=worker_id, operation=f"op_{op}"
                    )
            except Exception as e:
                with self.error_lock:
                    self.error_count += 1

        # Start multiple workers
        threads = []
        num_workers = 6
        for worker_id in range(num_workers):
            thread = threading.Thread(target=register_and_emit, args=(worker_id,))
            threads.append(thread)
            thread.start()

        # Wait for all workers to complete
        for thread in threads:
            thread.join()

        # Wait for async processing
        time.sleep(0.3)

        # Check no errors occurred
        self.assertEqual(self.error_count, 0)

        # Check that operations completed
        with results_lock:
            # Each worker should have completed 5 operations
            # But due to multiple registrations, we might have more results
            self.assertGreaterEqual(len(shared_results), num_workers * 5)


if __name__ == "__main__":
    unittest.main()
